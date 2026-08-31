<script>
  import { onMount } from 'svelte';
  import { toast } from '$lib/toast';

  // ubicaciones: array bindable de puntos del proyecto.
  // Cada punto: { nombre_lugar, provincia, canton, parroquia, sector, latitud, longitud, es_principal }
  let { ubicaciones = $bindable([]) } = $props();

  let mapEl;
  let map, markersLayer, L;

  // Tabs de modo de entrada
  let modoEntrada = $state('busqueda'); // 'busqueda' | 'manual' | 'archivo'

  // 1. Buscador Inteligente
  let query = $state('');
  let resultados = $state([]);
  let buscando = $state(false);
  let sinResultados = $state(false);
  let debounceId;

  // 2. Ingreso Manual / Enlace
  let inputEnlaceOCoords = $state('');
  let inputNombreManual = $state('');
  let inputLatManual = $state('');
  let inputLngManual = $state('');

  // 3. Archivo
  let archivoCargando = $state(false);

  const CENTRO_EC = [-1.026, -79.474]; // Quevedo / Los Ríos por defecto

  onMount(async () => {
    L = (await import('leaflet')).default;
    map = L.map(mapEl, { zoomControl: true }).setView(CENTRO_EC, 10);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);

    // Clic en el mapa → coloca un punto nuevo
    map.on('click', async (e) => {
      await agregarPunto(e.latlng.lat, e.latlng.lng);
    });

    redibujar();
  });

  // ── Extraer Coordenadas de Enlaces o Texto ────────────────────────
  function parsearCoordenadasOEnlace(texto) {
    if (!texto) return null;
    const str = texto.trim();

    // 1. Coordenadas directas estilo "-1.0264, -79.4740" o "-1.0264 -79.4740"
    const coordMatch = str.match(/(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lng = parseFloat(coordMatch[2]);
      if (lat >= -5 && lat <= 2 && lng >= -92 && lng <= -75) { // Rango válido Ecuador
        return { lat, lng };
      }
      return { lat, lng };
    }

    // 2. Enlaces Google Maps / WhatsApp tipo ?q=lat,lng o @lat,lng,zoom
    const gmapsMatch = str.match(/(?:q=|@|loc:)(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)/i);
    if (gmapsMatch) {
      return { lat: parseFloat(gmapsMatch[1]), lng: parseFloat(gmapsMatch[2]) };
    }

    return null;
  }

  // ── Búsqueda Híbrida (Photon Komoot + Nominatim Ecuador) ─────────
  function onInput() {
    sinResultados = false;
    clearTimeout(debounceId);
    
    // Si el usuario pegó un enlace o coordenadas directamente en el buscador
    const coordsDetectadas = parsearCoordenadasOEnlace(query);
    if (coordsDetectadas) {
      agregarPunto(coordsDetectadas.lat, coordsDetectadas.lng, { nombre_lugar: 'Ubicación importada' });
      query = '';
      resultados = [];
      toast.success('Coordenadas detectadas y ubicadas en el mapa.');
      return;
    }

    if (query.trim().length < 2) { resultados = []; return; }
    debounceId = setTimeout(buscarHibrido, 400);
  }

  async function buscarHibrido() {
    buscando = true; resultados = []; sinResultados = false;
    const q = query.trim();

    try {
      // Búsqueda en paralelo en Photon (tolerante a errores, ideal para sectores/barrios) y Nominatim
      const [resPhoton, resNominatim] = await Promise.all([
        fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&lat=-1.026&lon=-79.474&limit=6`)
          .then(r => r.json()).catch(() => ({ features: [] })),
        fetch(`https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=6&countrycodes=ec&q=${encodeURIComponent(q)}`, {
          headers: { 'Accept-Language': 'es' }
        }).then(r => r.json()).catch(() => [])
      ]);

      const lista = [];

      // Procesar resultados de Photon
      (resPhoton.features || []).forEach(f => {
        const p = f.properties || {};
        const [lng, lat] = f.geometry.coordinates;
        // Priorizar Ecuador
        if (!p.country || p.country.toLowerCase().includes('ecuador') || p.countrycode === 'EC') {
          const partes = [p.name, p.district || p.locality, p.city || p.county, p.state].filter(Boolean);
          lista.push({
            lat,
            lon: lng,
            display_name: partes.join(', '),
            nombre: p.name || 'Ubicación',
            provincia: p.state || '',
            canton: p.city || p.county || '',
            parroquia: p.district || p.locality || '',
            sector: p.street || p.name || '',
          });
        }
      });

      // Procesar resultados de Nominatim
      (resNominatim || []).forEach(r => {
        const a = r.address || {};
        lista.push({
          lat: parseFloat(r.lat),
          lon: parseFloat(r.lon),
          display_name: r.display_name,
          nombre: r.display_name?.split(',').slice(0, 2).join(',').trim() || 'Ubicación',
          provincia: a.state || a.region || '',
          canton: a.county || a.city || a.town || a.municipality || '',
          parroquia: a.suburb || a.village || a.city_district || '',
          sector: a.neighbourhood || a.hamlet || '',
        });
      });

      // Deduplicar por cercanía
      const unicos = [];
      lista.forEach(item => {
        const yaExiste = unicos.some(u => Math.abs(u.lat - item.lat) < 0.001 && Math.abs(u.lon - item.lon) < 0.001);
        if (!yaExiste) unicos.push(item);
      });

      resultados = unicos.slice(0, 7);
      sinResultados = resultados.length === 0;
    } catch {
      sinResultados = true;
    } finally {
      buscando = false;
    }
  }

  function elegirResultado(r) {
    agregarPunto(r.lat, r.lon, {
      nombre_lugar: r.nombre,
      provincia: r.provincia,
      canton: r.canton,
      parroquia: r.parroquia,
      sector: r.sector,
    });
    query = ''; resultados = [];
  }

  // ── Agregar Punto Manual / Enlace ───────────────────────────────
  async function aplicarIngresoManual() {
    let lat = parseFloat(inputLatManual);
    let lng = parseFloat(inputLngManual);

    // Si pegó un enlace en el campo de enlace
    if (inputEnlaceOCoords.trim()) {
      const parsed = parsearCoordenadasOEnlace(inputEnlaceOCoords);
      if (parsed) {
        lat = parsed.lat;
        lng = parsed.lng;
      } else {
        toast.error('No se pudieron extraer coordenadas válidas del enlace o texto.');
        return;
      }
    }

    if (isNaN(lat) || isNaN(lng)) {
      toast.error('Por favor ingresa coordenadas válidas (Latitud y Longitud).');
      return;
    }

    const nombre = inputNombreManual.trim() || 'Ubicación de Proyecto';
    await agregarPunto(lat, lng, { nombre_lugar: nombre });
    inputEnlaceOCoords = '';
    inputNombreManual = '';
    inputLatManual = '';
    inputLngManual = '';
    toast.success('Ubicación agregada al mapa con éxito.');
  }

  // ── Importar Archivo (KML / GPX / GeoJSON / CSV) ────────────────
  async function manejarArchivo(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    archivoCargando = true;

    try {
      const ext = file.name.split('.').pop().toLowerCase();
      const text = await file.text();
      const puntosExtraidos = [];

      if (ext === 'kml') {
        // Parsear XML KML de Google Earth
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, 'text/xml');
        const placemarks = xml.querySelectorAll('Placemark');
        
        placemarks.forEach((pm, idx) => {
          const name = pm.querySelector('name')?.textContent?.trim() || `Punto KML #${idx + 1}`;
          const coordsText = pm.querySelector('coordinates')?.textContent?.trim();
          if (coordsText) {
            const [lng, lat] = coordsText.split(',').map(Number);
            if (!isNaN(lat) && !isNaN(lng)) {
              puntosExtraidos.push({ lat, lng, nombre_lugar: name });
            }
          }
        });
      } else if (ext === 'gpx') {
        // Parsear GPX de GPS / Celular
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, 'text/xml');
        const wpts = xml.querySelectorAll('wpt');
        wpts.forEach((w, idx) => {
          const lat = parseFloat(w.getAttribute('lat'));
          const lng = parseFloat(w.getAttribute('lon'));
          const name = w.querySelector('name')?.textContent?.trim() || `Punto GPX #${idx + 1}`;
          if (!isNaN(lat) && !isNaN(lng)) {
            puntosExtraidos.push({ lat, lng, nombre_lugar: name });
          }
        });
      } else if (ext === 'geojson' || ext === 'json') {
        // Parsear GeoJSON
        const geojson = JSON.parse(text);
        const features = geojson.features || (geojson.type === 'Feature' ? [geojson] : []);
        features.forEach((f, idx) => {
          if (f.geometry?.type === 'Point') {
            const [lng, lat] = f.geometry.coordinates;
            const name = f.properties?.name || f.properties?.nombre || `Punto GeoJSON #${idx + 1}`;
            if (!isNaN(lat) && !isNaN(lng)) {
              puntosExtraidos.push({ lat, lng, nombre_lugar: name });
            }
          }
        });
      } else if (ext === 'csv' || ext === 'txt') {
        // Parsear CSV / TXT con líneas tipo lat,lon,nombre
        const lines = text.split(/\r?\n/).filter(l => l.trim());
        lines.forEach((line, idx) => {
          if (idx === 0 && (line.toLowerCase().includes('lat') || line.toLowerCase().includes('lon'))) return; // header
          const cols = line.split(/[,;\t]/).map(c => c.trim().replace(/^["']|["']$/g, ''));
          if (cols.length >= 2) {
            const lat = parseFloat(cols[0]);
            const lng = parseFloat(cols[1]);
            const name = cols[2] || `Punto CSV #${idx + 1}`;
            if (!isNaN(lat) && !isNaN(lng)) {
              puntosExtraidos.push({ lat, lng, nombre_lugar: name });
            }
          }
        });
      } else {
        toast.error('Formato no compatible. Sube un archivo .kml, .gpx, .geojson o .csv');
        return;
      }

      if (puntosExtraidos.length === 0) {
        toast.error('No se encontraron coordenadas válidas dentro del archivo.');
        return;
      }

      // Agregar puntos encontrados
      for (const p of puntosExtraidos) {
        await agregarPunto(p.lat, p.lng, { nombre_lugar: p.nombre_lugar });
      }

      toast.success(`Se importaron ${puntosExtraidos.length} ubicación(es) correctamente.`);
      e.target.value = '';
    } catch (err) {
      console.error(err);
      toast.error('Error al procesar el archivo geográfico.');
    } finally {
      archivoCargando = false;
    }
  }

  // ── Agregar / gestionar puntos ──────────────────────────────────
  async function agregarPunto(lat, lng, meta = null) {
    let info = meta;
    if (!info || !info.provincia) {
      const rev = await reverseGeocode(lat, lng);
      if (rev) {
        info = { ...rev, ...(meta?.nombre_lugar ? { nombre_lugar: meta.nombre_lugar } : {}) };
      }
    }

    const esPrimero = ubicaciones.length === 0;
    ubicaciones = [...ubicaciones, {
      nombre_lugar: info?.nombre_lugar || (esPrimero ? 'Ubicación Principal' : `Ubicación Alterna #${ubicaciones.length + 1}`),
      provincia: info?.provincia || '',
      canton: info?.canton || '',
      parroquia: info?.parroquia || '',
      sector: info?.sector || '',
      latitud: Number(lat).toFixed(7),
      longitud: Number(lng).toFixed(7),
      es_principal: esPrimero,
    }];
    redibujar();
    map.setView([lat, lng], Math.max(map.getZoom(), 13));
  }

  async function reverseGeocode(lat, lng) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&addressdetails=1&lat=${lat}&lon=${lng}`;
      const res = await fetch(url, { headers: { 'Accept-Language': 'es' } });
      const r = await res.json();
      const a = r.address || {};
      return {
        nombre_lugar: r.display_name?.split(',').slice(0, 2).join(',').trim() || '',
        provincia: a.state || a.region || '',
        canton: a.county || a.city || a.town || a.municipality || '',
        parroquia: a.suburb || a.village || a.city_district || '',
        sector: a.neighbourhood || a.hamlet || a.road || '',
      };
    } catch { return null; }
  }

  function quitar(i) {
    const eraPrincipal = ubicaciones[i].es_principal;
    ubicaciones = ubicaciones.filter((_, idx) => idx !== i);
    if (eraPrincipal && ubicaciones.length) ubicaciones[0].es_principal = true;
    ubicaciones = ubicaciones;
    redibujar();
  }

  function marcarPrincipal(i) {
    ubicaciones = ubicaciones.map((u, idx) => ({ ...u, es_principal: idx === i }));
    redibujar();
  }

  function centrarEn(i) {
    const u = ubicaciones[i];
    map.setView([parseFloat(u.latitud), parseFloat(u.longitud)], 15);
  }

  // ── Dibujar marcadores ──────────────────────────────────────────
  function redibujar() {
    if (!markersLayer || !L) return;
    markersLayer.clearLayers();
    ubicaciones.forEach((u, i) => {
      const lat = parseFloat(u.latitud), lng = parseFloat(u.longitud);
      if (isNaN(lat) || isNaN(lng)) return;
      const color = u.es_principal ? '#1b7505' : '#0284c7';
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:24px;height:24px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:${color};border:2.5px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;">
                 <span style="transform:rotate(45deg);color:#fff;font-size:11px;font-weight:900;">${i + 1}</span>
               </div>`,
        iconSize: [24, 24], iconAnchor: [12, 24],
      });
      const marker = L.marker([lat, lng], { icon, draggable: true });
      marker.on('dragend', async (e) => {
        const p = e.target.getLatLng();
        ubicaciones[i].latitud = p.lat.toFixed(7);
        ubicaciones[i].longitud = p.lng.toFixed(7);
        const rev = await reverseGeocode(p.lat, p.lng);
        if (rev) {
          if (!ubicaciones[i].canton) ubicaciones[i].canton = rev.canton;
          if (!ubicaciones[i].provincia) ubicaciones[i].provincia = rev.provincia;
        }
        ubicaciones = ubicaciones;
      });
      marker.bindTooltip(
        `<b>${u.nombre_lugar || `Punto ${i + 1}`}</b><br><small style="color:${color};font-weight:700;">${u.es_principal ? '⭐ Ubicación Principal' : '📍 Ubicación Alterna'}</small>`,
        { direction: 'top', offset: [0, -20] }
      );
      markersLayer.addLayer(marker);
    });
  }

  $effect(() => { ubicaciones; redibujar(); });
</script>

<div class="ms-wrap">
  
  <!-- BARRA DE MODOS DE ENTRADA -->
  <div class="ms-toolbar">
    <div class="ms-tabs-mode">
      <button
        type="button"
        class="tab-btn"
        class:active={modoEntrada === 'busqueda'}
        onclick={() => modoEntrada = 'busqueda'}
      >
        <i class="bi bi-search"></i> Búsqueda de Lugar
      </button>
      <button
        type="button"
        class="tab-btn"
        class:active={modoEntrada === 'manual'}
        onclick={() => modoEntrada = 'manual'}
      >
        <i class="bi bi-geo-alt"></i> Enlace WhatsApp / Coordenadas
      </button>
      <button
        type="button"
        class="tab-btn"
        class:active={modoEntrada === 'archivo'}
        onclick={() => modoEntrada = 'archivo'}
      >
        <i class="bi bi-file-earmark-arrow-up"></i> Importar Archivo (KML / GPX / CSV)
      </button>
    </div>
  </div>

  <!-- 1. MODO BÚSQUEDA INTELIGENTE -->
  {#if modoEntrada === 'busqueda'}
    <div class="ms-search">
      <div class="ms-search-box">
        <i class="bi bi-search"></i>
        <input
          bind:value={query}
          oninput={onInput}
          placeholder="Escribe sector, barrio o cantón: 'Quevedo 20 de Febrero', 'La Chiquita', 'Mocache'..."
        />
        {#if buscando}<i class="bi bi-arrow-repeat spin"></i>{/if}
      </div>
      {#if resultados.length}
        <ul class="ms-results">
          {#each resultados as r}
            <li onclick={() => elegirResultado(r)}>
              <i class="bi bi-geo-alt-fill"></i>
              <div class="ms-r-txt">
                <span class="ms-r-name">{r.nombre}</span>
                <span class="ms-r-sub">{r.display_name}</span>
              </div>
            </li>
          {/each}
        </ul>
      {:else if sinResultados}
        <div class="ms-noresult">
          <i class="bi bi-info-circle"></i> Sin coincidencias directas. Prueba con el cantón o haz clic directo en el mapa satelital.
        </div>
      {/if}
    </div>

  <!-- 2. MODO MANUAL / ENLACE WHATSAPP / GOOGLE MAPS -->
  {:else if modoEntrada === 'manual'}
    <div class="ms-manual-box">
      <div class="mm-row">
        <div class="mm-input-wrap full">
          <label for="link-coords">Pegar enlace de WhatsApp, Google Maps o Coordenadas:</label>
          <input
            id="link-coords"
            bind:value={inputEnlaceOCoords}
            placeholder="Ej: https://maps.app.goo.gl/... o https://maps.google.com/?q=-1.0264,-79.474 o -1.0264, -79.474"
          />
        </div>
      </div>
      <div class="mm-row">
        <div class="mm-input-wrap">
          <label for="lat-manual">Latitud (opcional):</label>
          <input id="lat-manual" bind:value={inputLatManual} placeholder="-1.026450" />
        </div>
        <div class="mm-input-wrap">
          <label for="lng-manual">Longitud (opcional):</label>
          <input id="lng-manual" bind:value={inputLngManual} placeholder="-79.474120" />
        </div>
        <div class="mm-input-wrap">
          <label for="nom-manual">Nombre del lugar:</label>
          <input id="nom-manual" bind:value={inputNombreManual} placeholder="Ej: Sector 20 de Febrero" />
        </div>
        <button type="button" class="btn-aplicar-manual" onclick={aplicarIngresoManual}>
          <i class="bi bi-plus-lg"></i> Agregar Punto
        </button>
      </div>
    </div>

  <!-- 3. MODO IMPORTAR ARCHIVO -->
  {:else if modoEntrada === 'archivo'}
    <div class="ms-file-box">
      <label class="file-drop-zone">
        <input type="file" accept=".kml,.gpx,.geojson,.json,.csv,.txt" onchange={manejarArchivo} />
        <i class="bi bi-cloud-arrow-up-fill file-ic"></i>
        <span class="file-title">Haz clic para subir archivo geográfico</span>
        <span class="file-sub">Formatos soportados: Google Earth (.kml), GPS Garmin (.gpx), GeoJSON (.geojson), CSV / TXT</span>
      </label>
      {#if archivoCargando}
        <div class="loading-file"><i class="bi bi-arrow-repeat spin"></i> Procesando coordenadas del archivo...</div>
      {/if}
    </div>
  {/if}

  <!-- MAPA INTERACTIVO -->
  <div class="ms-map" bind:this={mapEl}></div>
  <p class="ms-hint"><i class="bi bi-cursor-fill"></i> También puedes hacer clic directo sobre el mapa para agregar nuevos puntos o arrastrar los pines para ajustar la posición.</p>

  <!-- LISTA DE UBICACIONES -->
  {#if ubicaciones.length}
    <div class="ms-list">
      <div class="ms-list-hdr">
        <span><i class="bi bi-geo-alt-fill text-green"></i> {ubicaciones.length} {ubicaciones.length === 1 ? 'ubicación registrada' : 'ubicaciones registradas'}</span>
        <span class="ms-list-hint">⭐ La estrella marca la Ubicación Principal del proyecto</span>
      </div>
      {#each ubicaciones as u, i}
        <div class="ms-item" class:principal={u.es_principal}>
          <span class="ms-num" style="background:{u.es_principal ? '#1b7505' : '#0284c7'}">{i + 1}</span>
          <div class="ms-item-body">
            <div class="ms-nom-row">
              <input class="ms-item-nom" bind:value={u.nombre_lugar} placeholder="Nombre o sector del lugar" />
              <span class="ms-type-badge" class:principal={u.es_principal}>
                {u.es_principal ? 'Ubicación Principal' : `Ubicación Alterna #${i + 1}`}
              </span>
            </div>
            <div class="ms-item-meta">
              {#if u.canton}<span><i class="bi bi-geo"></i> {u.canton}</span>{/if}
              {#if u.provincia}<span>· {u.provincia}</span>{/if}
              <span class="ms-coords">({u.latitud}, {u.longitud})</span>
            </div>
          </div>
          <button type="button" class="ms-act" title="Centrar en el mapa" onclick={() => centrarEn(i)}>
            <i class="bi bi-crosshair"></i>
          </button>
          <button type="button" class="ms-act" class:on={u.es_principal} title={u.es_principal ? 'Es la ubicación principal' : 'Marcar como ubicación principal'} onclick={() => marcarPrincipal(i)}>
            <i class="bi bi-star{u.es_principal ? '-fill' : ''}"></i>
          </button>
          <button type="button" class="ms-act danger" title="Eliminar ubicación" onclick={() => quitar(i)}>
            <i class="bi bi-trash"></i>
          </button>
        </div>
      {/each}
    </div>
  {:else}
    <div class="ms-empty">
      <i class="bi bi-geo-alt"></i>
      Aún no has agregado ubicaciones. Busca un sector, pega un enlace o haz clic en el mapa.
    </div>
  {/if}
</div>

<style>
  .ms-wrap { display: flex; flex-direction: column; gap: 10px; position: relative; width: 100%; }

  /* TOOLBAR DE MODOS */
  .ms-toolbar { display: flex; align-items: center; justify-content: space-between; }
  .ms-tabs-mode { display: flex; gap: 6px; flex-wrap: wrap; }
  .tab-btn {
    background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px;
    padding: 6px 12px; font-size: 0.78rem; font-weight: 700; color: #475569;
    cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
    transition: all 0.15s ease;
  }
  .tab-btn:hover { background: #e2e8f0; color: #1e293b; }
  .tab-btn.active { background: #1b7505; color: #ffffff; border-color: #1b7505; }

  /* 1. BUSCADOR */
  .ms-search { position: relative; z-index: 1000; }
  .ms-search-box {
    display: flex; align-items: center; gap: 9px;
    border: 1.5px solid #cbd5e1; border-radius: 10px;
    padding: 9px 14px; background: #ffffff; transition: border-color .2s;
  }
  .ms-search-box:focus-within { border-color: #1b7505; box-shadow: 0 0 0 3px rgba(27, 117, 5, 0.1); }
  .ms-search-box > .bi-search { color: #94a3b8; font-size: .95rem; }
  .ms-search-box input {
    flex: 1; border: none; background: transparent; outline: none;
    font-size: .86rem; font-family: inherit; font-weight: 600; color: #1e293b;
  }
  .ms-results {
    list-style: none; position: absolute; top: calc(100% + 4px); left: 0; right: 0;
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    box-shadow: 0 10px 30px rgba(0,0,0,.12); z-index: 1200; overflow: hidden; max-height: 260px; overflow-y: auto;
    margin: 0; padding: 0;
  }
  .ms-results li {
    display: flex; align-items: flex-start; gap: 10px; padding: 10px 14px;
    font-size: .82rem; color: #334155; cursor: pointer; border-bottom: 1px solid #f1f5f9;
  }
  .ms-results li:last-child { border-bottom: none; }
  .ms-results li:hover { background: #f0fdf4; color: #15803d; }
  .ms-results li i { color: #d97706; margin-top: 2px; flex-shrink: 0; }
  .ms-r-txt { display: flex; flex-direction: column; }
  .ms-r-name { font-weight: 700; color: #1e293b; }
  .ms-r-sub { font-size: 0.74rem; color: #64748b; }
  .ms-noresult { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: #fff8e6;
    border: 1px solid #fde68a; border-radius: 8px; padding: 8px 14px; font-size: .78rem; color: #92400e; z-index: 1200; }

  /* 2. INGRESO MANUAL */
  .ms-manual-box {
    background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 10px;
    padding: 12px 14px; display: flex; flex-direction: column; gap: 10px;
  }
  .mm-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; }
  .mm-input-wrap { display: flex; flex-direction: column; gap: 3px; flex: 1; min-width: 130px; }
  .mm-input-wrap.full { flex: 100%; }
  .mm-input-wrap label { font-size: 0.72rem; font-weight: 700; color: #475569; }
  .mm-input-wrap input {
    border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px;
    font-size: 0.82rem; font-family: inherit; outline: none; background: #fff;
  }
  .mm-input-wrap input:focus { border-color: #1b7505; }
  .btn-aplicar-manual {
    background: #1b7505; color: #ffffff; border: none; border-radius: 6px;
    padding: 7px 16px; font-size: 0.8rem; font-weight: 700; cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px; height: 33px;
  }
  .btn-aplicar-manual:hover { background: #145c04; }

  /* 3. ARCHIVO */
  .ms-file-box { background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 10px; padding: 14px; text-align: center; }
  .file-drop-zone { display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; gap: 4px; }
  .file-drop-zone input { display: none; }
  .file-ic { font-size: 2rem; color: #1b7505; margin-bottom: 2px; }
  .file-title { font-size: 0.85rem; font-weight: 700; color: #1e293b; }
  .file-sub { font-size: 0.72rem; color: #64748b; }
  .loading-file { font-size: 0.78rem; font-weight: 600; color: #15803d; margin-top: 8px; }

  /* MAPA */
  .ms-map { width: 100%; height: 350px; border-radius: 12px; overflow: hidden; border: 1px solid #cbd5e1; position: relative; z-index: 0; }
  .ms-hint { font-size: .74rem; color: #64748b; font-weight: 600; display: flex; align-items: center; gap: 6px; margin: 0; }

  /* LISTA DE UBICACIONES */
  .ms-list { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
  .ms-list-hdr { display: flex; align-items: center; justify-content: space-between; font-size: .8rem; font-weight: 800; color: #1e293b; padding: 2px 2px; }
  .ms-list-hint { font-size: .72rem; font-weight: 600; color: #64748b; }
  .text-green { color: #15803d; }

  .ms-item {
    display: flex; align-items: center; gap: 10px;
    border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 9px 12px; background: #fff;
    transition: all 0.15s ease;
  }
  .ms-item.principal { border-color: #86efac; background: #f0fdf4; }
  .ms-num { width: 26px; height: 26px; border-radius: 50%; color: #fff; font-size: .76rem; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .ms-item-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  
  .ms-nom-row { display: flex; align-items: center; gap: 8px; }
  .ms-item-nom { flex: 1; border: none; background: transparent; outline: none; font-size: .86rem; font-weight: 700; color: #1e293b; font-family: inherit; padding: 1px 0; }
  .ms-item-nom:focus { border-bottom: 1.5px solid #1b7505; }
  
  .ms-type-badge { font-size: 0.65rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: #e0f2fe; color: #0369a1; }
  .ms-type-badge.principal { background: #dcfce7; color: #15803d; }

  .ms-item-meta { font-size: .72rem; color: #64748b; font-weight: 600; display: flex; flex-wrap: wrap; gap: 6px; }
  .ms-coords { color: #94a3b8; font-family: monospace; font-size: .68rem; }

  .ms-act { background: #f8fafc; border: 1px solid #e2e8f0; color: #64748b; font-size: .9rem; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; cursor: pointer; transition: all 0.15s ease; }
  .ms-act:hover { background: #e0f2fe; color: #0284c7; border-color: #bae6fd; }
  .ms-act.on { color: #d97706; background: #fef3c7; border-color: #fde68a; }
  .ms-act.danger:hover { background: #fee2e2; color: #dc2626; border-color: #fecaca; }

  .ms-empty { display: flex; align-items: center; gap: 9px; justify-content: center; padding: 18px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; font-size: .82rem; color: #64748b; font-weight: 600; }
  .ms-empty i { font-size: 1.2rem; color: #94a3b8; }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin .7s linear infinite; color: #1b7505; }
</style>
