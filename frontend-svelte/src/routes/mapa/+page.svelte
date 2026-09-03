<script>
  import { onMount } from 'svelte';
  import { fetchAPI, capaNBIActiva, capaODSActiva, odsSeleccionadoMapa, periodoSeleccionadoGlobal } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { get } from 'svelte/store';
  import InstitutionalLoader from '$lib/InstitutionalLoader.svelte';

  function copiarCoordenadas(lat, lng) {
    if (!lat || !lng) return;
    const coords = `${Number(lat).toFixed(6)}, ${Number(lng).toFixed(6)}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(coords).then(() => {
        toast.success(`Coordenadas GPS copiadas: ${coords}`);
      }).catch(() => {
        toast.info(`Coordenadas: ${coords}`);
      });
    } else {
      toast.info(`Coordenadas: ${coords}`);
    }
  }

  const CATALOGO_17_ODS = [
    { num: 1, nombre: "Fin de la Pobreza", color: "#E5243B", icono: "bi-cash-coin" },
    { num: 2, nombre: "Hambre Cero", color: "#DDA63A", icono: "bi-egg-fried" },
    { num: 3, nombre: "Salud y Bienestar", color: "#4C9F38", icono: "bi-heart-pulse-fill" },
    { num: 4, nombre: "Educación de Calidad", color: "#C5192D", icono: "bi-book-fill" },
    { num: 5, nombre: "Igualdad de Género", color: "#FF3A21", icono: "bi-gender-ambiguous" },
    { num: 6, nombre: "Agua Limpia y Saneamiento", color: "#26BDE2", icono: "bi-droplet-fill" },
    { num: 7, nombre: "Energía Asequible y No Contaminante", color: "#FCC30B", icono: "bi-lightning-charge-fill" },
    { num: 8, nombre: "Trabajo Decente y Crecimiento Económico", color: "#A21942", icono: "bi-briefcase-fill" },
    { num: 9, nombre: "Industria, Innovación e Infraestructura", color: "#FD6925", icono: "bi-building-gear" },
    { num: 10, nombre: "Reducción de las Desigualdades", color: "#DD1367", icono: "bi-distribute-vertical" },
    { num: 11, nombre: "Ciudades y Comunidades Sostenibles", color: "#FD9D24", icono: "bi-houses-fill" },
    { num: 12, nombre: "Producción y Consumo Responsables", color: "#BF8B2E", icono: "bi-arrow-repeat" },
    { num: 13, nombre: "Acción por el Clima", color: "#3F7E44", icono: "bi-tree-fill" },
    { num: 14, nombre: "Vida Submarina", color: "#0A97D9", icono: "bi-water" },
    { num: 15, nombre: "Vida de Ecosistemas Terrestres", color: "#56C02B", icono: "bi-flower1" },
    { num: 16, nombre: "Paz, Justicia e Instituciones Sólidas", color: "#00689D", icono: "bi-shield-check" },
    { num: 17, nombre: "Alianzas para Lograr los Objetivos", color: "#19486A", icono: "bi-people-fill" },
  ];

  let facultades   = $state([]);
  let carreras     = $state([]);
  let periodos     = $state([]);
  let anios        = $state([]);
  let cargandoProyectos = $state(false);

  let filtros = $state({ facultad:'', carrera:'', periodo:'', estado:'', anio:'', buscar:'' });
  let total   = $state(0);
  let proySeleccionado = $state(null);
  let ubiSeleccionadaId = $state(null);
  let proyectoRedExtendidaId = $state(null);
  let modalTab = $state('general');
  let fotoActiva = $state(0);
  let lightboxAbierto = $state(false);
  let modalDocs = $state([]);       // documentos cacheados por proyecto id
  let modalDocsLoad = $state(false);
  let docAbierto = $state(null);    // {url, nombre, extension}

  // Estado y datos de Capas ODS en el Mapa
  let listaCapasOdsDB = $state([]);
  let odsHudMinimizado = $state(false);
  let modalHistoricoOds = $state(null);

  async function cargarCapasOdsDB() {
    try {
      const data = await fetchAPI('/api/capas-ods/');
      listaCapasOdsDB = data || [];
    } catch {
      listaCapasOdsDB = [];
    }
  }

  let infoOdsActivo = $derived.by(() => {
    if (!$capaODSActiva || !$odsSeleccionadoMapa) return null;
    const dbItem = listaCapasOdsDB.find(o => o.num === $odsSeleccionadoMapa);
    const catItem = CATALOGO_17_ODS.find(o => o.num === $odsSeleccionadoMapa);
    if (!catItem) return null;
    return {
      ...catItem,
      ...(dbItem || {}),
      color: catItem.color,
      icono: catItem.icono,
      nombre: catItem.nombre,
      cargado: dbItem?.cargado || false,
    };
  });

  function extractUrl(item) {
    if (!item) return '';
    let url = typeof item === 'string' ? item : (item.url || item.ruta_foto || item.foto_url || item.src || '');
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) return url;
    if (!url.startsWith('/')) url = '/' + url;
    if (!url.startsWith('/media/')) url = '/media' + url;
    return url;
  }

  async function cargarDocumentos(id) {
    modalDocs = []; modalDocsLoad = true;
    try {
      const r = await fetch(`/api/proyectos/${id}/documentos/`, { credentials:'include' });
      modalDocs = r.ok ? await r.json() : [];
    } catch { modalDocs = []; }
    finally { modalDocsLoad = false; }
  }

  $effect(() => {
    if (proySeleccionado && modalTab === 'documentos') {
      cargarDocumentos(proySeleccionado.id);
    }
  });

  // Capa NBI (estado en store compartido con layout)
  let nbiAviso     = $state('');
  let nbiCargaTodo = $state(false);   // switch: OFF = solo viewport, ON = todos los cantones
  let nbiByCanton  = null;
  let nbiLayer     = null;
  let nbiLeyenda   = null;

  // Quevedo (centro por defecto)
  const QUEVEDO = { lat: -1.026, lng: -79.474, zoom: 12 };

  const ESTADOS = [
    { val:'EN_EJECUCION', label:'En ejecución', color:'#1b7505' },
    { val:'PROPUESTO',    label:'Propuesto',    color:'#dba112' },
    { val:'APROBADO',     label:'Aprobado',     color:'#0d6efd' },
    { val:'EN_CIERRE',    label:'En cierre',    color:'#fd7e14' },
    { val:'DETENIDO',     label:'Detenido',     color:'#dc3545' },
    { val:'FINALIZADO',   label:'Finalizado',   color:'#a8a8a7' },
    { val:'RECHAZADO',    label:'Rechazado',    color:'#6c757d' },
  ];

  let map, markersLayer, redesLayer;
  let capaBaseActual = $state('osm'); // 'osm' | 'satelite' | 'hibrido'
  let tileLayerOSM, tileLayerSat, tileLayerLabels;

  function setCapaBase(tipo) {
    if (!map) return;
    capaBaseActual = tipo;

    if (tileLayerOSM && map.hasLayer(tileLayerOSM)) map.removeLayer(tileLayerOSM);
    if (tileLayerSat && map.hasLayer(tileLayerSat)) map.removeLayer(tileLayerSat);
    if (tileLayerLabels && map.hasLayer(tileLayerLabels)) map.removeLayer(tileLayerLabels);

    if (tipo === 'osm') {
      if (tileLayerOSM) tileLayerOSM.addTo(map);
    } else if (tipo === 'satelite') {
      if (tileLayerSat) tileLayerSat.addTo(map);
    } else if (tipo === 'hibrido') {
      if (tileLayerSat) tileLayerSat.addTo(map);
      if (tileLayerLabels) tileLayerLabels.addTo(map);
    }

    if (markersLayer) markersLayer.bringToFront();
    if (redesLayer) redesLayer.bringToFront();
  }

  function desplegarRedNodos(p, L) {
    if (!redesLayer || !map) return;
    redesLayer.clearLayers();

    if (!p.ubicaciones || p.ubicaciones.length <= 1) return;

    const principal = p.ubicaciones.find(u => u.es_principal) || p.ubicaciones[0];
    const secundarias = p.ubicaciones.filter(u => u !== principal);

    const latLngs = [[principal.latitud, principal.longitud]];

    secundarias.forEach((u, idx) => {
      latLngs.push([u.latitud, u.longitud]);

      // 1. Halo base blanco/luminoso para garantizar contraste sobre capas NBI o mapa satelital
      const polyHalo = L.polyline([[principal.latitud, principal.longitud], [u.latitud, u.longitud]], {
        color: '#ffffff',
        weight: 5,
        opacity: 0.85,
        lineCap: 'round',
        pane: 'markerPane'
      });
      redesLayer.addLayer(polyHalo);

      // 2. Línea conectora estilizada en azul zafiro/dorado institucional con trazo nítido
      const poly = L.polyline([[principal.latitud, principal.longitud], [u.latitud, u.longitud]], {
        color: '#0284c7',
        weight: 2.5,
        dashArray: '5, 7',
        opacity: 1,
        lineCap: 'round',
        className: 'red-line-vector',
        pane: 'markerPane'
      });
      redesLayer.addLayer(poly);

      // 3. Marcador estilo chincheta / pin satélite (Google Earth style)
      const pinIcon = L.divIcon({
        className: 'custom-pin-wrap',
        html: `
          <div class="satellite-pin-node" style="--pin-color: ${p.color};">
            <div class="pin-head">
              <i class="bi bi-pin-angle-fill"></i>
              <span class="pin-num">${idx + 2}</span>
            </div>
            <div class="pin-tag">${u.nombre_lugar || u.sector || u.canton || `Punto ${idx + 2}`}</div>
          </div>
        `,
        iconSize: [32, 42],
        iconAnchor: [16, 38],
      });

      const pinMarker = L.marker([u.latitud, u.longitud], { icon: pinIcon, zIndexOffset: 950 });
      pinMarker.bindTooltip(
        `<b>${p.nombre_corto}</b><br><span style="color:#0284c7;font-weight:700;">📍 Ubicación alterna:</span> ${u.nombre_lugar || u.canton}`,
        { direction: 'top', offset: [0, -34] }
      );
      pinMarker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        ubiSeleccionadaId = u.id_ubicacion ?? idx;
        proySeleccionado = p;
        modalTab = 'ubicacion';
        fotoActiva = 0;
        lightboxAbierto = false;
        docAbierto = null;
        modalDocs = [];
      });
      redesLayer.addLayer(pinMarker);
    });

    // Ajustar zoom suavemente para abarcar toda la red de nodos
    if (latLngs.length > 1) {
      const bounds = L.latLngBounds(latLngs);
      map.flyToBounds(bounds, { padding: [60, 60], maxZoom: 14, duration: 1.2 });
    }
  }

  // ── Proyectos ────────────────────────────────────────────────
  async function cargarProyectos() {
    cargandoProyectos = true;
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([k,v]) => { if(v) params.set(k,v); });
      
      const odsActivo = get(capaODSActiva);
      const odsNum = get(odsSeleccionadoMapa);
      if (odsActivo && odsNum) {
        params.set('ods', odsNum);
      }

      const data = await fetchAPI('/api/mapa/proyectos/?' + params.toString());
      proyectosGeoJSON = data;
      total = data.features?.length ?? 0;

      markersLayer.clearLayers();
      if (redesLayer) redesLayer.clearLayers();
      proyectoRedExtendidaId = null;

      if (get(capaODSActiva)) {
        cargarCantonesODS();
      } else if (odsPolygonsLayer && map) {
        map.removeLayer(odsPolygonsLayer);
        odsPolygonsLayer = null;
      }

      (data.features || []).forEach(f => {
      const [lng, lat] = f.geometry.coordinates;
      // Validación defensiva: ignorar coordenadas nulas, NaN o en el océano (0, 0)
      if (lat == null || lng == null || isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) {
        return;
      }
      const p = f.properties;
      const L = window._L;
      const numUbis = p.ubicaciones?.length || 1;
      const tieneMulti = numUbis > 1;

      const icon = L.divIcon({
        className: 'sgv-pin-container',
        html: `
          <div class="sgv-pin-hub" style="--c:${p.color};">
            <svg class="sgv-pin-svg" viewBox="0 0 28 36" width="28" height="36">
              <ellipse cx="14" cy="35" rx="5" ry="1.5" fill="rgba(0,0,0,0.3)" />
              <path d="M14 1 C6.82 1 1 6.82 1 14 C1 23.8 14 35 14 35 C14 35 27 23.8 27 14 C27 6.82 21.18 1 14 1 Z" 
                    fill="${p.color}" 
                    stroke="#ffffff" 
                    stroke-width="1.8" 
                    stroke-linejoin="round" />
              <circle cx="14" cy="13.5" r="7.5" fill="#ffffff" />
              <path d="M14 9.5 L19.5 12 L14 14.5 L8.5 12 Z" fill="${p.color}" />
              <path d="M10.5 13.5 V15.8 C10.5 17 14 17.5 14 17.5 C14 17.5 17.5 17 17.5 15.8 V13.5" fill="${p.color}" />
              <path d="M19 12.5 V16.2" stroke="${p.color}" stroke-width="0.8" stroke-linecap="round" />
            </svg>
            ${tieneMulti ? `<span class="sgv-pin-badge" title="${numUbis} sedes de ejecución">${numUbis}</span>` : ''}
          </div>
        `,
        iconSize: [28, 36],
        iconAnchor: [14, 35],
      });

      const marker = L.marker([lat, lng], { icon, zIndexOffset: tieneMulti ? 500 : 100 });
      marker.on('click', () => {
        if (tieneMulti) {
          // Si aún no se ha extendido la red en el mapa, extenderla primero sin abrir modal
          if (proyectoRedExtendidaId !== p.id) {
            proyectoRedExtendidaId = p.id;
            desplegarRedNodos(p, L);
            return;
          }
        } else {
          // Si es un proyecto de 1 sola ubicación, limpiar cualquier red previa abierta
          if (redesLayer) redesLayer.clearLayers();
          proyectoRedExtendidaId = null;
        }

        // Si ya está extendida o es un proyecto de 1 sola ubicación, abrir el modal
        ubiSeleccionadaId = p.ubicaciones?.[0]?.id_ubicacion ?? null;
        proySeleccionado = p;
        modalTab = 'general';
        fotoActiva = 0;
        lightboxAbierto = false;
        docAbierto = null;
        modalDocs = [];
      });

      let odsBadgeHtml = '';
      if (p.ods) {
        const odsItems = String(p.ods).split(',').map(s => s.trim()).filter(Boolean);
        if (odsItems.length) {
          odsBadgeHtml = `<div style="margin-top:4px;display:flex;gap:3px;flex-wrap:wrap;">` + 
            odsItems.slice(0, 3).map(o => {
              const num = parseInt(o.replace(/\D/g, ''));
              const cat = CATALOGO_17_ODS.find(c => c.num === num);
              return `<span style="background:${cat?.color || '#1b7505'};color:#ffffff;font-size:9px;font-weight:700;padding:1px 5px;border-radius:3px;">ODS ${num || o}</span>`;
            }).join('') + (odsItems.length > 3 ? `<span style="font-size:9px;color:#64748b;">+${odsItems.length-3}</span>` : '') + `</div>`;
        }
      }

      marker.bindTooltip(
        `<b>${p.nombre_corto}</b>${tieneMulti ? `<br><span style="color:#15803d;font-weight:700;">🌐 Red de ${numUbis} ubicaciones</span>` : ''}${odsBadgeHtml}`,
        { direction: 'top', offset: [0, -35] }
      );
      markersLayer.addLayer(marker);
    });
    } catch (e) {
      console.error('Error al cargar proyectos en el mapa:', e);
    } finally {
      cargandoProyectos = false;
    }
  }

  // ── Capas Territoriales ODS ──────────────────────────────────
  let proyectosGeoJSON = $state(null);
  let odsPolygonsLayer = null;

  function normalizarNombreCanton(s) {
    if (!s) return '';
    return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '');
  }

  async function cargarCantonesODS() {
    const L = window._L;
    if (!map) return;
    try {
      if (!cantonesGeo) {
        const res = await fetch('/geo/cantones_ec.geojson');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        cantonesGeo = await res.json();
      }
      renderODSPolygonsLayer();
    } catch (e) {
      console.error('[ODS Layer]', e);
    }
  }

  function renderODSPolygonsLayer() {
    const L = window._L;
    if (!map || !cantonesGeo) return;
    if (odsPolygonsLayer) { map.removeLayer(odsPolygonsLayer); odsPolygonsLayer = null; }
    if (!$capaODSActiva) return;

    const odsActivo = infoOdsActivo;
    const colorODS = odsActivo?.color || '#1b7505';

    // Contar proyectos por cantón
    const cantonesCount = {};
    (proyectosGeoJSON?.features || []).forEach(f => {
      const p = f.properties || {};
      const ubiList = p.ubicaciones || [{ canton: p.canton, provincia: p.provincia }];
      ubiList.forEach(u => {
        const cNorm = normalizarNombreCanton(u.canton || p.canton);
        if (cNorm) {
          cantonesCount[cNorm] = (cantonesCount[cNorm] || 0) + 1;
        }
      });
    });

    const feats = filtrarFeaturesPorVista(L);
    odsPolygonsLayer = L.geoJSON({ type: 'FeatureCollection', features: feats }, {
      style: (feature) => {
        const p = feature.properties || {};
        const cNorm = normalizarNombreCanton(p.canton || p.name);
        const count = cantonesCount[cNorm] || 0;
        const tieneProy = count > 0;
        return {
          weight: tieneProy ? 1.5 : 0.5,
          opacity: tieneProy ? 0.9 : 0.35,
          color: tieneProy ? colorODS : '#94a3b8',
          fillOpacity: tieneProy ? Math.min(0.28 + (count * 0.12), 0.75) : 0.04,
          fillColor: tieneProy ? colorODS : '#cbd5e1',
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        const nombre = p.canton || p.name || 'Cantón';
        const prov = p.province || p.provincia || '';
        const cNorm = normalizarNombreCanton(nombre);
        const count = cantonesCount[cNorm] || 0;

        let metaInfo = '';
        if (odsActivo) {
          metaInfo = `<div style="margin-top:4px;border-top:1px solid rgba(0,0,0,0.1);padding-top:4px;">
            <b style="color:${colorODS}">ODS ${odsActivo.num}: ${odsActivo.nombre}</b><br>
            <span style="font-size:0.75rem;color:#475569"><b>Indicador nacional:</b> ${odsActivo.valor_reciente ?? '—'} ${odsActivo.unidad || ''} (${odsActivo.anio_reciente || 'Reciente'})</span>
          </div>`;
        }

        layer.bindTooltip(
          `<b>Cantón:</b> ${nombre}${prov ? ` (${prov})` : ''}<br>` +
          `<span style="color:#0f172a;font-weight:700;">📍 Proyectos UTEQ:</span> ${count > 0 ? `<strong>${count}</strong> proyectos activos` : '<i>Sin proyectos en esta meta</i>'}` +
          metaInfo,
          { sticky: true, direction: 'top' }
        );

        layer.on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          map.flyToBounds(layer.getBounds(), { padding: [40, 40], maxZoom: 13, duration: 1.0 });
        });
      }
    }).addTo(map);

    if (markersLayer) markersLayer.bringToFront();
    if (redesLayer) redesLayer.bringToFront();
  }

  // ── Capa NBI/INEC ───────────────────────────────────────────
  // Paleta pastel (tonos tierra/durazno) — más suave que YlOrRd
  function getNBIColor(pct) {
    if (pct >= 80) return '#c96f6f';
    if (pct >= 65) return '#e08a7d';
    if (pct >= 50) return '#eaa98a';
    if (pct >= 40) return '#f2c19a';
    if (pct >= 30) return '#f5d4a8';
    if (pct >= 20) return '#f7e3b8';
    return '#f0ead2';
  }

  // Cache del geojson de cantones (viene con dpa_canton ya inyectado)
  let cantonesGeo = null;

  // Bounds cacheados por feature (evitar recomputar en cada moveend)
  const featureBoundsCache = new WeakMap();
  function getFeatureBounds(L, feature) {
    let b = featureBoundsCache.get(feature);
    if (b) return b;
    b = L.geoJSON(feature).getBounds();
    featureBoundsCache.set(feature, b);
    return b;
  }

  function filtrarFeaturesPorVista(L) {
    if (!cantonesGeo || !map) return cantonesGeo?.features ?? [];
    if (nbiCargaTodo) return cantonesGeo.features;
    const view = map.getBounds();
    return cantonesGeo.features.filter(f => view.intersects(getFeatureBounds(L, f)));
  }

  async function cargarCantonesNBI() {
    const L = window._L;
    if (!map || !nbiByCanton) return;
    nbiAviso = 'Cargando capa NBI…';
    try {
      if (!cantonesGeo) {
        const res = await fetch('/geo/cantones_ec.geojson');
        if (!res.ok) throw new Error(`HTTP ${res.status} al leer /geo/cantones_ec.geojson`);
        cantonesGeo = await res.json();
      }
      renderNBILayer();
    } catch (e) {
      console.error('[NBI]', e);
      nbiAviso = `Error al cargar capa NBI: ${e.message || e}`;
    }
  }

  function renderNBILayer() {
    const L = window._L;
    if (!map || !cantonesGeo || !nbiByCanton) return;
    if (nbiLayer) { map.removeLayer(nbiLayer); nbiLayer = null; }
    const feats = filtrarFeaturesPorVista(L);
    let matched = 0;
    nbiLayer = L.geoJSON({ type:'FeatureCollection', features: feats }, {
      style: (feature) => {
        const p = feature.properties || {};
        const entry = p.dpa_canton ? nbiByCanton[p.dpa_canton] : null;
        const pct = entry?.nbi_pct ?? null;
        if (pct !== null) matched++;
        return {
          weight: 0.6, opacity: 0.8, color: '#333',
          fillOpacity: pct !== null ? 0.65 : 0.15,
          fillColor: pct !== null ? getNBIColor(pct) : '#d0d0d0',
        };
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        const entry = p.dpa_canton ? nbiByCanton[p.dpa_canton] : null;
        const nombre = entry?.canton || p.canton || '';
        const prov = entry?.provincia || p.province || '';
        const pct = entry?.nbi_pct;
        const notaHist = p.canton_original
          ? `<br><i style="color:#888;font-size:.72rem">Zona ${p.canton_original} · asignada a ${nombre}</i>`
          : '';
        layer.bindTooltip(
          `<b>Cantón:</b> ${nombre}<br><b>Provincia:</b> ${prov}<br>` +
          (pct != null ? `<b>NBI 2022:</b> ${pct}%` : '<i>Sin dato NBI</i>') +
          notaHist,
          { sticky: true, direction: 'top' }
        );
      },
    }).addTo(map);
    const modo = nbiCargaTodo ? 'toda la capa' : 'solo vista actual';
    nbiAviso = `${matched} cantones (${modo})`;
  }

  function toggleNbiCargaTodo() {
    nbiCargaTodo = !nbiCargaTodo;
    if (nbiLayer) renderNBILayer();
  }

  function centrarEnQuevedo() {
    if (!map) return;
    map.setView([QUEVEDO.lat, QUEVEDO.lng], QUEVEDO.zoom);
  }

  function agregarLeyendaNBI() {
    const L = window._L;
    if (nbiLeyenda) return;
    nbiLeyenda = L.control({ position: 'bottomright' });
    nbiLeyenda.onAdd = () => {
      const div = L.DomUtil.create('div', 'nbi-leyenda');
      div.innerHTML = `
        <b>NBI 2022 (%)</b>
        <div><span style="background:#c96f6f"></span>≥ 80%</div>
        <div><span style="background:#e08a7d"></span>65 – 79%</div>
        <div><span style="background:#eaa98a"></span>50 – 64%</div>
        <div><span style="background:#f2c19a"></span>40 – 49%</div>
        <div><span style="background:#f5d4a8"></span>30 – 39%</div>
        <div><span style="background:#f7e3b8"></span>20 – 29%</div>
        <div><span style="background:#f0ead2"></span>&lt; 20%</div>
      `;
      return div;
    };
    nbiLeyenda.addTo(map);
  }

  async function toggleNBI(activo) {
    if (activo) {
      if (!nbiByCanton) {
        nbiByCanton = await fetchAPI('/api/capa-pobreza/');
      }
      await cargarCantonesNBI();
      agregarLeyendaNBI();
    } else {
      if (nbiLayer)   { map.removeLayer(nbiLayer); nbiLayer = null; }
      if (nbiLeyenda) { map.removeControl(nbiLeyenda); nbiLeyenda = null; }
      nbiAviso = '';
    }
  }

  // ── Mount ────────────────────────────────────────────────────
  onMount(async () => {
    // Inicia mapa inmediatamente mientras cargan los filtros en paralelo
    const Lprom = import('leaflet').then(m => m.default);

    const [L, facs, carrs, pers] = await Promise.all([
      Lprom,
      fetchAPI('/api/facultades/'),
      fetchAPI('/api/carreras/'),
      fetchAPI('/api/periodos/'),
    ]);
    facultades = facs;
    carreras   = carrs;
    periodos   = pers;

    try { const a = await fetchAPI('/api/mapa/anios/'); anios = a.anios || a; } catch {}

    window._L = L;
    map = L.map('map', { zoomControl: false }).setView([-1.5, -78.5], 7);

    // Configuración de Capas Base Oficiales (Callejero OpenStreetMap, Satelital Esri y Etiquetas Híbridas)
    tileLayerOSM = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    });

    tileLayerSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; High-Resolution Satellite',
      maxZoom: 19
    });

    tileLayerLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Esri Labels',
      maxZoom: 19,
      pane: 'overlayPane'
    });

    tileLayerOSM.addTo(map);
    L.control.zoom({ position: 'topleft' }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);
    redesLayer = L.layerGroup().addTo(map);

    // Al hacer clic en el fondo del mapa, ocultar la red de nodos
    map.on('click', () => {
      if (redesLayer) redesLayer.clearLayers();
      proyectoRedExtendidaId = null;
    });

    // Re-renderizar capas en modo "solo vista" al mover/zoom
    let mvTimer;
    map.on('moveend zoomend', () => {
      clearTimeout(mvTimer);
      mvTimer = setTimeout(() => {
        if (nbiLayer && !nbiCargaTodo) renderNBILayer();
        if (odsPolygonsLayer) renderODSPolygonsLayer();
      }, 120);
    });

    await cargarCapasOdsDB();
    await cargarProyectos();

    // Suscribir a los stores DESPUÉS de que el mapa esté listo
    const unsubNBI = capaNBIActiva.subscribe(activo => toggleNBI(activo));
    const unsubODS = capaODSActiva.subscribe(() => { if (map) cargarProyectos(); });
    const unsubODSNum = odsSeleccionadoMapa.subscribe(() => { if (map) cargarProyectos(); });
    const unsubPeriodo = periodoSeleccionadoGlobal.subscribe(p => {
      if (p && p.id && map) {
        filtros.periodo = String(p.id);
        filtrar();
      }
    });

    return () => {
      unsubNBI();
      unsubODS();
      unsubODSNum();
      unsubPeriodo();
    };
  });

  async function filtrar() { await cargarProyectos(); }
  function limpiar() {
    filtros = { facultad:'', carrera:'', periodo:'', estado:'', anio:'', buscar:'' };
    cargarProyectos();
  }

  let carrerasFiltradas = $derived(
    filtros.facultad
      ? carreras.filter(c => String(c.id_facultad) === String(filtros.facultad))
      : carreras
  );
</script>

<svelte:head><title>Mapa — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Mapa interactivo</span>
  </nav>
</div>

<div class="mapa-layout">
  <div class="mapa-right">

    <!-- FILTROS REESTRUCTURADOS -->
    <div class="filtros-bar">
      <div class="filtros-grid-top">
        <select class="fsel" bind:value={filtros.facultad} onchange={() => { filtros.carrera=''; filtrar(); }}>
          <option value="">Facultad (Todas)</option>
          {#each facultades as f}
            <option value={f.id_facultad}>{f.nombre_corto || f.nombre}</option>
          {/each}
        </select>

        <select class="fsel" bind:value={filtros.carrera} onchange={filtrar}>
          <option value="">Carrera (Todas)</option>
          {#each carrerasFiltradas as c}
            <option value={c.id_carrera}>{c.nombre}</option>
          {/each}
        </select>

        <select class="fsel" bind:value={filtros.periodo} onchange={filtrar}>
          <option value="">Período (Todos)</option>
          {#each periodos as p}
            <option value={p.id_periodo}>{p.nombre}</option>
          {/each}
        </select>

        <select class="fsel fsel-sm" bind:value={filtros.estado} onchange={filtrar}>
          <option value="">Estado (Todos)</option>
          {#each ESTADOS as e}
            <option value={e.val}>{e.label}</option>
          {/each}
        </select>

        <select class="fsel fsel-xs" bind:value={filtros.anio} onchange={filtrar}>
          <option value="">Año</option>
          {#each anios as a}
            <option value={a}>{a}</option>
          {/each}
        </select>
      </div>

      <div class="filtros-grid-bot">
        <div class="buscar-wrap">
          <i class="bi bi-search buscar-ico"></i>
          <input
            class="fbuscar"
            bind:value={filtros.buscar}
            onkeydown={(e) => { if (e.key === 'Enter') filtrar(); }}
            placeholder="Buscar proyecto, cantón, responsable..."
          />
        </div>

        <button class="btn-quevedo" onclick={centrarEnQuevedo} title="Centrar mapa en Quevedo">
          <i class="bi bi-geo-alt-fill"></i> Quevedo
        </button>

        {#if nbiAviso}
          <span class="nbi-aviso">{nbiAviso}</span>
        {/if}

        <div class="factions">
          <span class="total-badge"><i class="bi bi-pin-map-fill"></i> {total} proyectos</span>
          <button class="btn-limpiar" onclick={limpiar} title="Restablecer filtros">Limpiar</button>
          <button class="btn-filtrar" onclick={filtrar}><i class="bi bi-funnel-fill"></i> Filtrar</button>
        </div>
      </div>

      {#if filtros.facultad && facultades.find(f => String(f.id_facultad) === String(filtros.facultad) && (f.codigo === 'FCC' || f.nombre?.includes('Computación')))}
        <div class="fcc-mapa-banner">
          <i class="bi bi-info-circle-fill"></i>
          <span><strong>FCC:</strong> Facultad de reciente creación institucional. Sin proyectos asignados en este ciclo académico. Sus carreras históricas constan amparadas bajo FCI.</span>
        </div>
      {/if}
    </div>

    <!-- MAPA CON WIDGET HUD FLOTANTE -->
    <div class="map-container-wrap">
      {#if cargandoProyectos}
        <InstitutionalLoader fullscreen={false} texto="ACTUALIZANDO MAPA" subtexto="Georreferenciando proyectos..." />
      {/if}
      <div id="map" style="width:100%;height:100%;"></div>

      <!-- SELECTOR DE CAPA BASE PROFESIONAL (CALLEJERO / SATELITAL / HÍBRIDO) -->
      <div class="map-layer-selector">
        <button 
          type="button"
          class="layer-btn" 
          class:active={capaBaseActual === 'osm'} 
          onclick={() => setCapaBase('osm')}
          title="Vista de mapa callejero vectorial (OpenStreetMap)"
        >
          <i class="bi bi-map"></i> Callejero
        </button>
        <button 
          type="button"
          class="layer-btn" 
          class:active={capaBaseActual === 'satelite'} 
          onclick={() => setCapaBase('satelite')}
          title="Vista satelital aérea de alta resolución (Esri Imagery)"
        >
          <i class="bi bi-globe-americas"></i> Satelital
        </button>
        <button 
          type="button"
          class="layer-btn" 
          class:active={capaBaseActual === 'hibrido'} 
          onclick={() => setCapaBase('hibrido')}
          title="Vista satelital con nombres de cantones, vías y referencias"
        >
          <i class="bi bi-layers-fill"></i> Híbrido
        </button>
      </div>

      <!-- CARD HUD FLOTANTE DE ODS (AGENDA 2030) -->
      {#if $capaODSActiva && infoOdsActivo}
        <div class="map-ods-floating-card" style="--ods-accent: {infoOdsActivo.color || '#E5243B'};">
          <div class="mofc-header" style="background: {infoOdsActivo.color || '#E5243B'};">
            <div class="mofc-title-wrap">
              <span class="mofc-badge">ODS {infoOdsActivo.num}</span>
              <span class="mofc-name">{infoOdsActivo.nombre}</span>
            </div>
            <div class="mofc-actions">
              <button 
                type="button" 
                class="mofc-btn-icon" 
                onclick={() => odsHudMinimizado = !odsHudMinimizado} 
                title={odsHudMinimizado ? 'Expandir diagnóstico' : 'Minimizar'}
              >
                <i class="bi {odsHudMinimizado ? 'bi-chevron-down' : 'bi-chevron-up'}"></i>
              </button>
              <button 
                type="button" 
                class="mofc-btn-icon" 
                onclick={() => { odsSeleccionadoMapa.set(null); }} 
                title="Quitar filtro ODS"
              >
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          {#if !odsHudMinimizado}
            <div class="mofc-body">
              <div class="mofc-stat-row">
                <div class="mofc-stat-box">
                  <span class="mofc-stat-lbl">INDICADOR OFICIAL ECUADOR</span>
                  <div class="mofc-stat-val">
                    <strong>{infoOdsActivo.valor_reciente ?? '—'}</strong>
                    <small>{infoOdsActivo.unidad || '%'}</small>
                    <span class="mofc-stat-yr">({infoOdsActivo.anio_reciente || 'Reciente'})</span>
                  </div>
                  <p class="mofc-stat-sub" title={infoOdsActivo.nombre_indicador || infoOdsActivo.nombre}>
                    {infoOdsActivo.nombre_indicador || 'Meta de Desarrollo Sostenible (CEPAL / ONU)'}
                  </p>
                </div>
              </div>

              <div class="mofc-impact-row">
                <div class="mofc-impact-pill">
                  <i class="bi bi-geo-alt-fill" style="color: {infoOdsActivo.color};"></i>
                  <span><strong>{total}</strong> proyectos UTEQ alineados</span>
                </div>
                {#if infoOdsActivo.serie_historica && infoOdsActivo.serie_historica.length > 0}
                  <button 
                    type="button" 
                    class="mofc-btn-hist" 
                    onclick={() => modalHistoricoOds = infoOdsActivo}
                  >
                    <i class="bi bi-clock-history"></i> Evolución ({infoOdsActivo.serie_historica.length} años)
                  </button>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      {/if}

      <div class="map-hud-bar">
        <div class="hud-item"><i class="bi bi-geo-alt-fill text-verde"></i> <strong>{total}</strong> Proyectos ubicados</div>
        <div class="hud-sep"></div>
        <div class="hud-item"><i class="bi bi-building"></i> <strong>{facultades.length}</strong> Facultades UTEQ</div>
        <div class="hud-sep"></div>
        <div class="hud-item"><i class="bi bi-crosshair"></i> <strong>Quevedo</strong> (Sede Central)</div>
      </div>
    </div>
  </div>
</div>

<!-- MODAL DE EVOLUCIÓN HISTÓRICA ODS -->
{#if modalHistoricoOds}
  <div class="ods-modal-overlay" onclick={() => modalHistoricoOds = null}>
    <div class="ods-modal-box" onclick={(e) => e.stopPropagation()}>
      <div class="omb-hdr" style="background: {modalHistoricoOds.color || '#1b7505'};">
        <div class="omb-hdr-info">
          <h3><i class="bi {modalHistoricoOds.icono || 'bi-globe-americas'}"></i> ODS {modalHistoricoOds.num}: {modalHistoricoOds.nombre}</h3>
          <p>{modalHistoricoOds.nombre_indicador || 'Indicador Oficial CEPAL / ONU (Ecuador)'}</p>
        </div>
        <button class="omb-close" onclick={() => modalHistoricoOds = null}><i class="bi bi-x-lg"></i></button>
      </div>

      <div class="omb-body">
        <div class="omb-kpi-row">
          <div class="omb-kpi-card">
            <span class="okc-lbl">VALOR MÁS RECIENTE EN ECUADOR</span>
            <div class="okc-val">
              {modalHistoricoOds.valor_reciente} <small>{modalHistoricoOds.unidad}</small>
            </div>
          </div>
          <div class="omb-kpi-card">
            <span class="okc-lbl">AÑO DE MEDICIÓN</span>
            <div class="okc-val">{modalHistoricoOds.anio_reciente}</div>
          </div>
          <div class="omb-kpi-card">
            <span class="okc-lbl">PROYECTOS UTEQ ALINEADOS</span>
            <div class="okc-val text-verde">{total}</div>
          </div>
        </div>

        <h4 class="omb-subhdr"><i class="bi bi-clock-history"></i> Serie Histórica Registrada en Ecuador</h4>
        {#if modalHistoricoOds.serie_historica && modalHistoricoOds.serie_historica.length}
          <div class="omb-table-wrap">
            <table class="omb-table">
              <thead>
                <tr>
                  <th>Año</th>
                  <th>Valor Oficial</th>
                  <th>Unidad</th>
                  <th>Evolución</th>
                </tr>
              </thead>
              <tbody>
                {#each modalHistoricoOds.serie_historica as fila, idx}
                  {@const prev = idx > 0 ? modalHistoricoOds.serie_historica[idx - 1].valor : null}
                  {@const dif = prev !== null ? fila.valor - prev : null}
                  <tr>
                    <td><strong>{fila.anio}</strong></td>
                    <td class="td-val">{fila.valor}</td>
                    <td><span class="badge-unit">{modalHistoricoOds.unidad}</span></td>
                    <td>
                      {#if dif === null}
                        <span class="trend-base">Línea base</span>
                      {:else if dif > 0}
                        <span class="trend-up">▲ +{dif.toFixed(2)}</span>
                      {:else if dif < 0}
                        <span class="trend-down">▼ {dif.toFixed(2)}</span>
                      {:else}
                        <span class="trend-eq">═ 0.00</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <p class="empty-hist">No hay serie histórica registrada para este indicador.</p>
        {/if}
      </div>

      <div class="omb-ftr">
        <button class="btn-sec" onclick={() => modalHistoricoOds = null}>Cerrar</button>
      </div>
    </div>
  </div>
{/if}

<!-- MODAL -->
{#if proySeleccionado}
  {@const p = proySeleccionado}
  {@const fotosRaw = (p.fotos && p.fotos.length ? p.fotos : (p.foto_url ? [p.foto_url] : []))}
  {@const fotos = fotosRaw.map(extractUrl).filter(Boolean)}
  {@const TABS = [
    { id:'general',    label:'General',    icon:'bi-info-circle' },
    { id:'ubicacion',  label:'Ubicación',  icon:'bi-geo-alt' },
    { id:'cronograma', label:'Cronograma', icon:'bi-calendar-range' },
    { id:'documentos', label:'Documentos', icon:'bi-file-earmark-pdf' },
    { id:'notas',      label:'Notas',      icon:'bi-journal-text', hidden: !p.observaciones && !p.motivo_detencion && !p.ods },
  ].filter(t => !t.hidden)}
  <div class="modal-overlay" onclick={() => proySeleccionado = null}>
    <div class="modal-box wide" onclick={(e) => e.stopPropagation()}>
      <button class="modal-close" onclick={() => proySeleccionado = null}>
        <i class="bi bi-x-lg"></i>
      </button>

      <div class="modal-split">
        <!-- COLUMNA IZQUIERDA: foto + header -->
        <aside class="msp-left">
          <div class="msp-foto">
            {#if fotos.length}
              {#key fotoActiva}
                <img
                  src={fotos[fotoActiva]}
                  alt="Foto {fotoActiva+1}"
                  onerror={(e) => { e.currentTarget.style.display='none'; if (e.currentTarget.parentElement.querySelector('.msp-fallback')) e.currentTarget.parentElement.querySelector('.msp-fallback').style.display='flex'; }}
                />
              {/key}
              <div class="msp-fallback" style="display:none">
                <i class="bi bi-image-alt"></i>
                <small>Imagen no encontrada</small>
              </div>
              <button class="msp-expand" onclick={() => lightboxAbierto = true} title="Ver en grande">
                <i class="bi bi-arrows-fullscreen"></i>
              </button>
              {#if fotos.length > 1}
                <button class="msp-nav prev" onclick={() => fotoActiva = (fotoActiva - 1 + fotos.length) % fotos.length}>
                  <i class="bi bi-chevron-left"></i>
                </button>
                <button class="msp-nav next" onclick={() => fotoActiva = (fotoActiva + 1) % fotos.length}>
                  <i class="bi bi-chevron-right"></i>
                </button>
                <span class="msp-counter">{fotoActiva+1} / {fotos.length}</span>
              {/if}
            {:else}
              <div class="msp-fallback">
                <i class="bi bi-image"></i>
                <small>Sin fotos</small>
              </div>
            {/if}
          </div>

          <div class="msp-head">
            <div class="modal-estado" style="background:{p.color}20;color:{p.color}">
              {p.estado?.replace('_',' ')}
            </div>
            <h2 class="msp-title">{p.nombre}</h2>
            <span class="msp-code">{p.codigo}</span>
          </div>

          {#if fotos.length > 1}
            <div class="msp-thumbs">
              {#each fotos as f, i}
                <button
                  class="msp-thumb"
                  class:active={i === fotoActiva}
                  onclick={() => fotoActiva = i}
                  title="Ver foto {i+1}"
                >
                  <img src={f} alt="thumb {i+1}" onerror={(e) => { e.currentTarget.style.opacity=.3; }} />
                </button>
              {/each}
            </div>
          {/if}

          <!-- TABS -->
          <nav class="msp-tabs">
            {#each TABS as t}
              <button class="msp-tab" class:active={modalTab === t.id} onclick={() => modalTab = t.id}>
                <i class="bi {t.icon}"></i> {t.label}
              </button>
            {/each}
          </nav>
        </aside>

        <!-- COLUMNA DERECHA: contenido del tab -->
        <div class="msp-right">
          {#if modalTab === 'general'}
            {#if p.descripcion}
              <p class="msp-desc">{p.descripcion}</p>
            {/if}

            <h5 class="msp-h5">Académico</h5>
            <div class="msp-grid">
              <div class="mi"><i class="bi bi-mortarboard-fill"></i><div><span class="mi-l">Facultad</span><span class="mi-v">{p.facultad}</span></div></div>
              <div class="mi"><i class="bi bi-book-fill"></i><div><span class="mi-l">Carrera</span><span class="mi-v">{p.carrera}</span></div></div>
              {#if p.programa}<div class="mi full"><i class="bi bi-diagram-3"></i><div><span class="mi-l">Programa</span><span class="mi-v">{p.programa}</span></div></div>{/if}
              {#if p.linea_vinculacion}<div class="mi full"><i class="bi bi-link-45deg"></i><div><span class="mi-l">Línea de vinculación</span><span class="mi-v">{p.linea_vinculacion}</span></div></div>{/if}
              {#if p.area_conocimiento}<div class="mi"><i class="bi bi-lightbulb"></i><div><span class="mi-l">Área</span><span class="mi-v">{p.area_conocimiento}</span></div></div>{/if}
              {#if p.sub_area_conocimiento}<div class="mi"><i class="bi bi-lightbulb-off"></i><div><span class="mi-l">Sub-área</span><span class="mi-v">{p.sub_area_conocimiento}</span></div></div>{/if}
              {#if p.alcance}<div class="mi"><i class="bi bi-arrows-fullscreen"></i><div><span class="mi-l">Alcance</span><span class="mi-v">{p.alcance}</span></div></div>{/if}
            </div>

            {#if p.objetivo_general || p.objetivos_especificos}
              <h5 class="msp-h5">Objetivos</h5>
              {#if p.objetivo_general}
                <div class="mi-block"><span class="mi-l">General</span><p class="mi-p">{p.objetivo_general}</p></div>
              {/if}
              {#if p.objetivos_especificos}
                <div class="mi-block"><span class="mi-l">Específicos</span><p class="mi-p">{p.objetivos_especificos}</p></div>
              {/if}
            {/if}

            {#if p.director_nombre || p.director_correo || p.resolucion_aprobacion || p.fecha_aprobacion || p.presupuesto_planificado != null}
              <h5 class="msp-h5">Dirección y aprobación</h5>
              <div class="msp-grid">
                {#if p.director_nombre}<div class="mi"><i class="bi bi-person"></i><div><span class="mi-l">Director/a</span><span class="mi-v">{p.director_nombre}</span></div></div>{/if}
                {#if p.director_correo}<div class="mi"><i class="bi bi-envelope"></i><div><span class="mi-l">Correo</span><span class="mi-v">{p.director_correo}</span></div></div>{/if}
                {#if p.resolucion_aprobacion}<div class="mi full"><i class="bi bi-file-earmark-check"></i><div><span class="mi-l">Resolución</span><span class="mi-v">{p.resolucion_aprobacion}</span></div></div>{/if}
                {#if p.fecha_aprobacion}<div class="mi"><i class="bi bi-calendar2-check"></i><div><span class="mi-l">Fecha aprobación</span><span class="mi-v">{p.fecha_aprobacion}</span></div></div>{/if}
                {#if p.presupuesto_planificado != null}<div class="mi"><i class="bi bi-currency-dollar"></i><div><span class="mi-l">Presupuesto</span><span class="mi-v">$ {p.presupuesto_planificado.toLocaleString('es-EC',{minimumFractionDigits:2})}</span></div></div>{/if}
              </div>
            {/if}

          {:else if modalTab === 'ubicacion'}
            {#if p.ubicaciones && p.ubicaciones.length > 0}
              <div class="ubicaciones-list-tab">
                <h5 class="msp-h5">Puntos y Ubicaciones de Ejecución ({p.ubicaciones.length})</h5>
                <div class="ubis-cards-grid">
                  {#each p.ubicaciones as u, idx}
                    {@const esSeleccionada = (ubiSeleccionadaId !== null && (u.id_ubicacion === ubiSeleccionadaId || (u.id_ubicacion == null && idx === ubiSeleccionadaId)))}
                    <div class="ubi-card" class:es-principal={u.es_principal} class:nodo-activo={esSeleccionada}>
                      <div class="uc-head">
                        <span class="uc-badge" class:principal={u.es_principal} class:seleccionada={esSeleccionada}>
                          <i class="bi bi-{esSeleccionada ? 'check-circle-fill' : (u.es_principal ? 'star-fill' : 'pin-fill')}"></i>
                          {#if esSeleccionada}
                            Ubicación Seleccionada {u.es_principal ? '(Principal)' : `(#${idx + 1})`}
                          {:else}
                            {u.es_principal ? 'Ubicación Principal' : `Ubicación Alterna #${idx + 1}`}
                          {/if}
                        </span>
                        <div class="uc-actions-bar">
                          <button class="btn-flyto" onclick={() => {
                            if (map) { map.flyTo([u.latitud, u.longitud], 15); proySeleccionado = null; }
                          }} title="Centrar en el mapa">
                            <i class="bi bi-crosshair"></i> Ver en mapa
                          </button>
                          <button class="btn-copy-gps" onclick={() => copiarCoordenadas(u.latitud, u.longitud)} title="Copiar coordenadas GPS al portapapeles">
                            <i class="bi bi-clipboard"></i> Copiar GPS
                          </button>
                          <a href="https://www.google.com/maps?q={u.latitud},{u.longitud}" target="_blank" rel="noopener noreferrer" class="btn-gmaps" title="Abrir en Google Maps">
                            <i class="bi bi-box-arrow-up-right"></i> Maps
                          </a>
                        </div>
                      </div>
                      <div class="uc-title">{u.nombre_lugar || 'Ubicación de ejecución'}</div>
                      <div class="uc-meta">
                        <span><i class="bi bi-geo-alt"></i> {u.canton || p.canton || '—'}, {u.provincia || p.provincia || '—'}</span>
                        {#if u.sector}<span><i class="bi bi-house"></i> {u.sector}</span>{/if}
                        <span class="uc-coords">{u.latitud?.toFixed(5)}, {u.longitud?.toFixed(5)}</span>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {:else}
              <div class="msp-grid">
                <div class="mi"><i class="bi bi-pin-map"></i><div><span class="mi-l">Provincia</span><span class="mi-v">{p.provincia || '—'}</span></div></div>
                <div class="mi"><i class="bi bi-pin-map-fill"></i><div><span class="mi-l">Cantón</span><span class="mi-v">{p.canton || '—'}</span></div></div>
                {#if p.parroquia}<div class="mi"><i class="bi bi-signpost"></i><div><span class="mi-l">Parroquia</span><span class="mi-v">{p.parroquia}</span></div></div>{/if}
                {#if p.sector}<div class="mi"><i class="bi bi-house"></i><div><span class="mi-l">Sector</span><span class="mi-v">{p.sector}</span></div></div>{/if}
                {#if p.latitud && p.longitud}
                  <div class="mi" style="grid-column: 1 / -1; display:flex; align-items:center; justify-content:space-between; background:#f8fafc; padding:10px 14px; border-radius:10px; border:1px solid #e2e8f0;">
                    <div>
                      <span class="mi-l">Coordenadas GPS</span>
                      <span class="mi-v" style="font-family:monospace; font-weight:700;">{Number(p.latitud).toFixed(6)}, {Number(p.longitud).toFixed(6)}</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                      <button class="btn-copy-gps" onclick={() => copiarCoordenadas(p.latitud, p.longitud)}><i class="bi bi-clipboard"></i> Copiar GPS</button>
                      <a href="https://www.google.com/maps?q={p.latitud},{p.longitud}" target="_blank" rel="noopener noreferrer" class="btn-gmaps"><i class="bi bi-box-arrow-up-right"></i> Maps</a>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}

          {:else if modalTab === 'cronograma'}
            <div class="msp-grid">
              <div class="mi"><i class="bi bi-calendar3"></i><div><span class="mi-l">Período inicio</span><span class="mi-v">{p.periodo}</span></div></div>
              {#if p.periodo_fin}<div class="mi"><i class="bi bi-calendar3"></i><div><span class="mi-l">Período fin</span><span class="mi-v">{p.periodo_fin}</span></div></div>{/if}
              {#if p.fecha_inicio}<div class="mi"><i class="bi bi-play-circle"></i><div><span class="mi-l">Inicio</span><span class="mi-v">{p.fecha_inicio}</span></div></div>{/if}
              {#if p.fecha_fin_planificada}<div class="mi"><i class="bi bi-flag"></i><div><span class="mi-l">Fin planificado</span><span class="mi-v">{p.fecha_fin_planificada}</span></div></div>{/if}
              {#if p.fecha_fin_real}<div class="mi"><i class="bi bi-flag-fill"></i><div><span class="mi-l">Fin real</span><span class="mi-v">{p.fecha_fin_real}</span></div></div>{/if}
            </div>

          {:else if modalTab === 'documentos'}
            {#if modalDocsLoad}
              <div class="msp-empty"><i class="bi bi-arrow-repeat spin"></i> Cargando documentos...</div>
            {:else if !modalDocs.length}
              <div class="msp-empty">
                <i class="bi bi-folder2-open" style="font-size:2rem;color:#ccc;display:block;margin-bottom:8px"></i>
                Este proyecto no tiene documentos cargados.
              </div>
            {:else}
              <ul class="msp-docs">
                {#each modalDocs as d}
                  {@const ext = (d.nombre?.split('.').pop() || '').toLowerCase()}
                  {@const isPdf = ext === 'pdf'}
                  {@const kb = d.tamanio_kb ? (d.tamanio_kb > 1024 ? (d.tamanio_kb/1024).toFixed(1)+' MB' : d.tamanio_kb+' KB') : ''}
                  <li class="msp-doc">
                    <i class="bi bi-file-earmark-{isPdf ? 'pdf' : (['jpg','jpeg','png','gif','webp'].includes(ext) ? 'image' : (['doc','docx'].includes(ext) ? 'word' : (['xls','xlsx'].includes(ext) ? 'excel' : 'text')))}"></i>
                    <div class="msp-doc-info">
                      <span class="msp-doc-name" title={d.nombre}>{d.nombre}</span>
                      <span class="msp-doc-meta">{d.tipo}{kb ? ' · '+kb : ''}</span>
                    </div>
                    <div class="msp-doc-acts">
                      <button class="msp-doc-btn" onclick={() => docAbierto = { url:d.url, nombre:d.nombre, extension:ext }} title="Ver aquí">
                        <i class="bi bi-eye"></i>
                      </button>
                      <a class="msp-doc-btn" href={d.url} target="_blank" rel="noopener" title="Abrir en nueva pestaña">
                        <i class="bi bi-box-arrow-up-right"></i>
                      </a>
                    </div>
                  </li>
                {/each}
              </ul>
            {/if}

            {#if p.ods}
              {@const odsItems = String(p.ods).split(',').map(s => s.trim()).filter(Boolean)}
              <div class="mi-block">
                <span class="mi-l"><i class="bi bi-globe-americas"></i> Alineación ODS (Agenda 2030)</span>
                <div class="proy-ods-badges-wrap">
                  {#each odsItems as o}
                    {@const num = parseInt(o.replace(/\D/g, ''))}
                    {@const cat = CATALOGO_17_ODS.find(c => c.num === num)}
                    <span class="proy-ods-badge-item" style="--ods-col: {cat?.color || '#1b7505'};">
                      <i class="bi {cat?.icono || 'bi-bullseye'}"></i>
                      <strong>ODS {num || o}:</strong> {cat?.nombre || o}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}
            {#if p.motivo_detencion}
              <div class="mi-block warn"><span class="mi-l">Motivo detención</span><p class="mi-p">{p.motivo_detencion}</p></div>
            {/if}
            {#if p.observaciones}
              <div class="mi-block"><span class="mi-l">Observaciones</span><p class="mi-p">{p.observaciones}</p></div>
            {/if}
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- LIGHTBOX FOTOS -->
  {#if lightboxAbierto && fotos.length}
    <div class="lightbox" onclick={() => lightboxAbierto = false}>
      <button class="lb-close"><i class="bi bi-x-lg"></i></button>
      <img src={fotos[fotoActiva]} alt="Foto {fotoActiva+1}" onclick={(e) => e.stopPropagation()} />
      {#if fotos.length > 1}
        <button class="lb-nav prev" onclick={(e) => { e.stopPropagation(); fotoActiva = (fotoActiva - 1 + fotos.length) % fotos.length; }}>
          <i class="bi bi-chevron-left"></i>
        </button>
        <button class="lb-nav next" onclick={(e) => { e.stopPropagation(); fotoActiva = (fotoActiva + 1) % fotos.length; }}>
          <i class="bi bi-chevron-right"></i>
        </button>
        <span class="lb-counter">{fotoActiva+1} / {fotos.length}</span>
      {/if}
    </div>
  {/if}

  <!-- VISOR DE DOCUMENTOS -->
  {#if docAbierto}
    <div class="doc-viewer" onclick={() => docAbierto = null}>
      <div class="dv-box" onclick={(e) => e.stopPropagation()}>
        <header class="dv-head">
          <span title={docAbierto.nombre}><i class="bi bi-file-earmark"></i> {docAbierto.nombre}</span>
          <div class="dv-acts">
            <a href={docAbierto.url} target="_blank" rel="noopener" class="dv-btn" title="Abrir aparte"><i class="bi bi-box-arrow-up-right"></i></a>
            <a href={docAbierto.url} download class="dv-btn" title="Descargar"><i class="bi bi-download"></i></a>
            <button class="dv-btn" onclick={() => docAbierto = null} title="Cerrar"><i class="bi bi-x-lg"></i></button>
          </div>
        </header>
        <div class="dv-body">
          {#if ['jpg','jpeg','png','gif','webp'].includes(docAbierto.extension)}
            <img src={docAbierto.url} alt={docAbierto.nombre} />
          {:else if docAbierto.extension === 'pdf'}
            <iframe
              src={docAbierto.url + (docAbierto.url.includes('?') ? '&' : '?') + '_=' + Date.now() + '#toolbar=1&navpanes=0'}
              title={docAbierto.nombre}
            ></iframe>
          {:else}
            <div class="dv-empty">
              <i class="bi bi-file-earmark-arrow-down"></i>
              <p>Este tipo de archivo (.{docAbierto.extension}) no se puede previsualizar aquí.</p>
              <a href={docAbierto.url} download class="dv-download"><i class="bi bi-download"></i> Descargar</a>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
{/if}

<style>
/* ── LAYOUT ── */
.mapa-layout {
  display: flex;
  height: calc(100vh - 56px - 36px - 37px);
  overflow: hidden;
  padding: 12px 12px 12px 4px;
}

/* ── PANEL PRINCIPAL ── */
.mapa-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,.10);
  background: #fff;
  overflow: hidden;
}
/* ── FILTROS rediseñados y balanceados ── */
.filtros-bar {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px 14px;
  border-radius: 16px 16px 0 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filtros-grid-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filtros-grid-top .fsel {
  flex: 1 1 180px;
  min-width: 140px;
}

.filtros-grid-top .fsel-sm {
  flex: 0 1 150px;
  min-width: 120px;
}

.filtros-grid-top .fsel-xs {
  flex: 0 0 90px;
  min-width: 80px;
}

.filtros-grid-bot {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.fsel {
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 0.78rem;
  font-family: inherit;
  font-weight: 600;
  color: #334155;
  background: #f8fafc;
  outline: none;
  cursor: pointer;
  transition: border-color .15s, background .15s;
  appearance: auto;
}

.fsel:focus, .fsel:hover { 
  border-color: var(--verde, #16a34a); 
  background: #ffffff; 
}

.buscar-wrap {
  display: flex; 
  align-items: center; 
  gap: 7px;
  border: 1.5px solid #cbd5e1; 
  border-radius: 10px;
  padding: 5px 12px; 
  background: #f8fafc;
  flex: 1 1 240px;
  min-width: 180px;
  transition: border-color .15s;
}

.buscar-wrap:focus-within { 
  border-color: var(--verde, #16a34a); 
  background: #ffffff; 
}

.buscar-ico { color: #94a3b8; font-size: .85rem; flex-shrink: 0; }
.fbuscar {
  border: none; 
  background: transparent; 
  outline: none;
  font-size: .78rem; 
  font-family: inherit; 
  font-weight: 600;
  color: #1e293b; 
  width: 100%;
}

.btn-quevedo {
  background: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  padding: 5px 12px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #15803d;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-quevedo:hover {
  background: #f0fdf4;
  border-color: #86efac;
}

.factions { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  margin-left: auto; 
}

.total-badge {
  background: #f0fdf4; 
  color: #16a34a;
  font-size: .75rem; 
  font-weight: 800;
  padding: 5px 12px; 
  border-radius: 8px; 
  border: 1px solid #bbf7d0;
  white-space: nowrap;
}

.btn-limpiar {
  background: #ffffff; 
  border: 1.5px solid #cbd5e1; 
  border-radius: 10px;
  padding: 5px 14px; 
  font-size: .78rem; 
  font-weight: 700; 
  color: #64748b;
  cursor: pointer; 
  transition: all .15s; 
  font-family: inherit;
}

.btn-limpiar:hover { 
  background: #f1f5f9;
  border-color: #94a3b8;
  color: #0f172a; 
}

.btn-filtrar {
  background: var(--verde, #16a34a); 
  border: none; 
  border-radius: 10px;
  padding: 6px 18px; 
  font-size: .78rem; 
  font-weight: 800;
  color: #ffffff; 
  cursor: pointer; 
  transition: background .15s; 
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  box-shadow: 0 2px 6px rgba(22, 163, 74, 0.25);
}

.btn-filtrar:hover { 
  background: #15803d; 
}

.fcc-mapa-banner {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-left: 4px solid #0284c7;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: .8rem;
  color: #0369a1;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}
.fcc-mapa-banner i { font-size: 1.15rem; flex-shrink: 0; color: #0284c7; }
.fcc-mapa-banner strong { color: #0c4a6e; }

/* ── MAPA ── */
.map-container-wrap {
  position: relative;
  flex: 1;
  width: 100%;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

/* Selector Flotante de Capa Base (Callejero / Satelital / Híbrido) */
.map-layer-selector {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 1000;
  display: flex;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 12px;
  padding: 4px;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.12);
  gap: 4px;
}

.layer-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.layer-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.layer-btn.active {
  background: var(--verde, #1b5e20);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(27, 94, 32, 0.3);
}

.layer-btn i {
  font-size: 0.85rem;
}
.map-hud-bar {
  position: absolute;
  bottom: 18px;
  left: 18px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(27, 94, 32, 0.18);
  border-radius: 12px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  font-size: 0.78rem;
  color: #333;
}
.hud-item { display: flex; align-items: center; gap: 6px; font-weight: 700; }
.hud-item strong { color: var(--verde, #1b5e20); font-weight: 800; }
.hud-sep { width: 1px; height: 14px; background: #cbd5e1; }

:global(#map) { flex: 1; width: 100%; min-height: 300px; }
:global(.leaflet-container) { font-family: 'Nunito', sans-serif; }
:global(.leaflet-tooltip) { font-family: 'Nunito', sans-serif; font-weight: 700; font-size: .78rem; }

/* ── Leyenda NBI ── */
:global(.nbi-leyenda) {
  background: rgba(255,255,255,.95) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  font-size: .73rem;
  font-family: 'Nunito', sans-serif;
  box-shadow: 0 4px 16px rgba(0,0,0,.18) !important;
  line-height: 1.9;
  z-index: 1000 !important;
  border: 1px solid #e0e0e0;
}
:global(.nbi-leyenda b) { display:block; font-size:.72rem; color:#333; margin-bottom:4px; font-weight:800; }
:global(.nbi-leyenda div) { display:flex; align-items:center; gap:7px; }
:global(.nbi-leyenda span) { display:inline-block; width:13px; height:13px; border-radius:3px; flex-shrink:0; }

/* Botón Quevedo */
.btn-quevedo {
  display:inline-flex;align-items:center;gap:6px;
  background:#fff;border:1.5px solid var(--verde);color:var(--verde);
  border-radius:20px;padding:6px 14px;font-size:.78rem;font-weight:800;
  cursor:pointer;font-family:inherit;transition:background .18s,color .18s;
}
.btn-quevedo:hover { background:var(--verde);color:#fff; }
.btn-quevedo i { font-size:.85rem; }

/* Switch "Toda la capa" */
.nbi-switch {
  display:inline-flex;align-items:center;gap:8px;cursor:pointer;
  padding:5px 10px;border-radius:20px;background:#fafafa;border:1.5px solid var(--borde);
}
.nbi-switch input { display:none; }
.ns-slider {
  width:32px;height:18px;background:#ccc;border-radius:20px;position:relative;transition:background .18s;
}
.ns-slider::after {
  content:'';position:absolute;top:2px;left:2px;width:14px;height:14px;
  background:#fff;border-radius:50%;transition:transform .18s;box-shadow:0 1px 3px rgba(0,0,0,.3);
}
.nbi-switch input:checked ~ .ns-slider { background:var(--verde); }
.nbi-switch input:checked ~ .ns-slider::after { transform:translateX(14px); }
.ns-label { font-size:.75rem;font-weight:700;color:#555; }

/* Aviso NBI en sidebar */
.nbi-aviso {
  margin-top: 6px;
  font-size: .68rem;
  color: #888;
  background: #f5f5f5;
  border-radius: 6px;
  padding: 5px 8px;
  line-height: 1.4;
}

/* ── MODAL ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-box {
  background: #fff;
  border-radius: 18px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
  position: relative;
  animation: pop .2s ease;
}
.modal-box.wide { max-width: 880px; }
@keyframes pop { from { transform: scale(.92); opacity:0; } to { transform: scale(1); opacity:1; } }

.modal-close {
  position: absolute;
  top: 12px; right: 12px;
  background: rgba(0,0,0,.4);
  border: none;
  border-radius: 50%;
  width: 32px; height: 32px;
  color: #fff;
  font-size: .9rem;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  z-index: 1;
  transition: background .2s;
}
.modal-close:hover { background: rgba(0,0,0,.6); }

/* ── Split 2 columnas ── */
.modal-split { display:grid;grid-template-columns:280px 1fr;height:min(90vh,620px); }
@media (max-width:720px) { .modal-split { grid-template-columns:1fr;height:90vh; } }

.msp-left {
  display:flex;flex-direction:column;
  background:#f9fafb;border-right:1px solid #ececec;
  padding:0;overflow:hidden;
}
.msp-foto { position:relative;width:100%;height:180px;background:#eee;flex-shrink:0;overflow:hidden; }
.msp-foto img { width:100%;height:100%;object-fit:cover;display:block; }
.msp-fallback {
  position:absolute;inset:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;
  background:#f6f7f4;color:#b8b8b8;
}
.msp-fallback i { font-size:2.2rem; }
.msp-fallback small { font-size:.7rem;font-weight:700; }

.msp-expand, .msp-nav {
  position:absolute;background:rgba(0,0,0,.45);color:#fff;border:none;border-radius:50%;
  width:28px;height:28px;display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:.75rem;transition:background .18s;
}
.msp-expand:hover, .msp-nav:hover { background:rgba(0,0,0,.7); }
.msp-expand { top:8px;right:8px; }
.msp-nav.prev { top:50%;left:6px;transform:translateY(-50%); }
.msp-nav.next { top:50%;right:6px;transform:translateY(-50%); }
.msp-counter {
  position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.55);color:#fff;font-size:.68rem;font-weight:700;
  padding:2px 8px;border-radius:10px;
}

.msp-head { padding:14px 16px 10px;border-bottom:1px solid #f0f0f0; }
.msp-title { font-size:.9rem;font-weight:900;color:#1a1a1a;line-height:1.3;margin:6px 0 3px; }
.msp-code  { font-size:.68rem;font-weight:700;color:var(--gris);display:block; }

.msp-thumbs {
  display:flex;gap:5px;padding:8px 12px;border-bottom:1px solid #f0f0f0;
  overflow-x:auto;
}
.msp-thumbs::-webkit-scrollbar { height:4px; }
.msp-thumb {
  padding:0;border:2px solid transparent;border-radius:6px;background:none;cursor:pointer;
  flex-shrink:0;transition:border-color .18s;
}
.msp-thumb:hover { border-color:#c3e6b0; }
.msp-thumb.active { border-color:var(--verde); }
.msp-thumb img { width:40px;height:40px;object-fit:cover;border-radius:4px;display:block; }

.msp-tabs { display:flex;flex-direction:column;padding:8px 0;flex:1;overflow-y:auto; }
.msp-tab {
  display:flex;align-items:center;gap:10px;
  padding:9px 16px;font-size:.78rem;font-weight:700;color:#555;
  background:none;border:none;border-left:3px solid transparent;
  cursor:pointer;font-family:inherit;text-align:left;
  transition:background .14s,color .14s,border-color .14s;
}
.msp-tab i { font-size:.9rem;color:#9999bb; }
.msp-tab:hover { background:#fff;color:var(--verde); }
.msp-tab:hover i { color:var(--verde); }
.msp-tab.active { background:#fff;color:var(--verde);border-left-color:var(--verde);font-weight:800; }
.msp-tab.active i { color:var(--verde); }

.msp-right {
  padding:20px 22px;overflow-y:auto;
}
.msp-right::-webkit-scrollbar { width:6px; }
.msp-right::-webkit-scrollbar-thumb { background:#ccc;border-radius:6px; }

.msp-desc {
  font-size:.82rem;color:#555;line-height:1.55;
  margin:0 0 14px;padding:10px 12px;background:#fafafa;
  border-left:3px solid var(--verde);border-radius:0 8px 8px 0;
}
.msp-grid { display:grid;grid-template-columns:1fr 1fr;gap:12px 16px; }
.msp-grid .mi.full { grid-column:1/-1; }
@media (max-width:520px) { .msp-grid { grid-template-columns:1fr; } }
.msp-empty { grid-column:1/-1;color:#999;font-size:.82rem;text-align:center;padding:30px 20px; }
.msp-h5 { font-size:.65rem;font-weight:800;color:var(--verde);text-transform:uppercase;
  letter-spacing:.08em;margin:16px 0 8px;padding-bottom:5px;border-bottom:1px solid #f0f0f0; }
.msp-h5:first-child { margin-top:0; }

/* ── Documentos ── */
.msp-docs { list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px; }
.msp-doc {
  display:flex;align-items:center;gap:10px;
  padding:10px 12px;background:#fafafa;border:1px solid #f0f0f0;border-radius:10px;
  transition:border-color .18s,background .18s;
}
.msp-doc:hover { border-color:var(--verde);background:#f7fbf3; }
.msp-doc > i { font-size:1.4rem;color:var(--verde);flex-shrink:0; }
.msp-doc-info { flex:1;min-width:0;display:flex;flex-direction:column;gap:2px; }
.msp-doc-name { font-size:.82rem;font-weight:700;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.msp-doc-meta { font-size:.68rem;color:#888;font-weight:600; }
.msp-doc-acts { display:flex;gap:4px;flex-shrink:0; }
.msp-doc-btn {
  background:#fff;border:1px solid var(--borde);border-radius:8px;
  width:30px;height:30px;display:flex;align-items:center;justify-content:center;
  color:#666;font-size:.8rem;cursor:pointer;text-decoration:none;transition:all .18s;
}
.msp-doc-btn:hover { background:var(--verde);color:#fff;border-color:var(--verde); }

/* ── Lightbox ── */
.lightbox {
  position:fixed;inset:0;background:rgba(0,0,0,.9);z-index:10000;
  display:flex;align-items:center;justify-content:center;padding:40px;
  animation:fadein .2s ease;
}
@keyframes fadein { from{opacity:0} to{opacity:1} }
.lightbox img { max-width:100%;max-height:100%;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,.5); }
.lb-close {
  position:absolute;top:20px;right:20px;background:rgba(255,255,255,.15);color:#fff;
  border:none;border-radius:50%;width:44px;height:44px;font-size:1.1rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:background .18s;
}
.lb-close:hover { background:rgba(255,255,255,.28); }
.lb-nav {
  position:absolute;top:50%;transform:translateY(-50%);
  background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:50%;
  width:52px;height:52px;font-size:1.3rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:background .18s;
}
.lb-nav:hover { background:rgba(255,255,255,.28); }
.lb-nav.prev { left:24px; } .lb-nav.next { right:24px; }
.lb-counter { position:absolute;bottom:24px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.5);color:#fff;font-size:.85rem;font-weight:700;padding:5px 14px;border-radius:20px; }

/* ── Visor de documentos ── */
.doc-viewer {
  position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:10001;
  display:flex;align-items:center;justify-content:center;padding:24px;
}
.dv-box {
  background:#fff;border-radius:14px;width:100%;max-width:1000px;height:90vh;
  display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.4);
}
.dv-head {
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:12px 18px;background:var(--verde);color:#fff;
}
.dv-head > span {
  display:flex;align-items:center;gap:8px;font-weight:700;font-size:.88rem;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
.dv-acts { display:flex;gap:6px;flex-shrink:0; }
.dv-btn {
  background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:8px;
  width:34px;height:34px;display:flex;align-items:center;justify-content:center;
  font-size:.9rem;cursor:pointer;text-decoration:none;transition:background .18s;
}
.dv-btn:hover { background:rgba(255,255,255,.28); }
.dv-body { flex:1;overflow:hidden;background:#f4f4f4;display:flex;align-items:center;justify-content:center; }
.dv-body iframe { width:100%;height:100%;border:none;background:#fff; }
.dv-body img { max-width:100%;max-height:100%;object-fit:contain; }
.dv-empty { text-align:center;padding:40px;color:#666; }
.dv-empty i { font-size:3rem;color:#c8c8c8;display:block;margin-bottom:12px; }
.dv-empty p { font-size:.88rem;margin-bottom:14px; }
.dv-download {
  display:inline-flex;align-items:center;gap:8px;
  background:var(--verde);color:#fff;text-decoration:none;
  padding:9px 20px;border-radius:20px;font-size:.85rem;font-weight:800;
}
.dv-download:hover { background:#155e04; }

.modal-estado {
  display:inline-block;font-size:.62rem;font-weight:800;
  padding:3px 10px;border-radius:20px;
  text-transform:uppercase;letter-spacing:.05em;
}
.mi { display:flex;align-items:flex-start;gap:8px; }
.mi i { color:var(--verde);font-size:.95rem;margin-top:2px;flex-shrink:0; }
.mi > div { display:flex;flex-direction:column;min-width:0; }
.mi-l { font-size:.62rem;color:var(--gris);font-weight:800;text-transform:uppercase;letter-spacing:.05em; }
.mi-v { font-size:.82rem;color:var(--negro);font-weight:600;word-break:break-word; }
.mi-block { margin-bottom:12px; }
.mi-block:last-child { margin-bottom:0; }
.mi-block.warn { background:#fff8e6;border-left:3px solid #f5b400;padding:8px 12px;border-radius:0 6px 6px 0; }
.mi-p { font-size:.82rem;color:#444;line-height:1.55;margin:4px 0 0;white-space:pre-line; }
.modal-title {
  font-size: 1rem;
  font-weight: 900;
  color: var(--negro);
  line-height: 1.3;
  margin-bottom: 4px;
}
.modal-code {
  font-size: .72rem;
  font-weight: 700;
  color: var(--gris);
}

/* ── PIN PRINCIPAL DE GEORREFERENCIACIÓN UTEQ ── */
:global(.sgv-pin-container) {
  background: transparent !important;
  border: none !important;
}

:global(.sgv-pin-hub) {
  position: relative;
  width: 28px;
  height: 36px;
  cursor: pointer;
  filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.4));
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.22s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(.sgv-pin-hub:hover) {
  transform: scale(1.25) translateY(-5px);
  filter: drop-shadow(0 7px 12px rgba(0, 0, 0, 0.5));
  z-index: 9999 !important;
}

:global(.sgv-pin-svg) {
  display: block;
  overflow: visible;
}

:global(.sgv-pin-badge) {
  position: absolute;
  top: -4px;
  right: -5px;
  background: #0f172a;
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 900;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #ffffff;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.35);
}

/* ── CHINCHETAS SATÉLITE (GOOGLE EARTH PIN STYLE) ── */
:global(.custom-pin-wrap) {
  background: transparent;
  border: none;
}

:global(.satellite-pin-node) {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  animation: bounceIn .3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

:global(.pin-head) {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #facc15;
  color: #854d0e;
  border: 2px solid #ffffff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  position: relative;
}

:global(.pin-num) {
  position: absolute;
  top: -5px;
  right: -5px;
  background: var(--pin-color, #1b7505);
  color: #ffffff;
  font-size: 0.55rem;
  font-weight: 800;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ffffff;
}

:global(.pin-tag) {
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(4px);
  color: #ffffff;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 8px;
  margin-top: 2px;
  white-space: nowrap;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  pointer-events: none;
}

:global(.red-line-vector) {
  animation: dashAnimation 1.2s linear infinite;
  filter: drop-shadow(0 2px 5px rgba(2, 132, 199, 0.4));
}

@keyframes dashAnimation {
  from { stroke-dashoffset: 28; }
  to { stroke-dashoffset: 0; }
}

@keyframes bounceIn {
  from { opacity: 0; transform: translateY(-15px) scale(0.5); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── TAB DE UBICACIONES MÚLTIPLES EN EL MODAL ── */
.ubicaciones-list-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ubis-cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.ubi-card {
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.15s ease;
}

.ubi-card.es-principal {
  background: #f0fdf4;
  border-color: #86efac;
}

.ubi-card.nodo-activo {
  background: #dcfce7 !important;
  border: 2px solid #16a34a !important;
  box-shadow: 0 4px 14px rgba(22, 163, 74, 0.22);
}

.uc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.uc-badge {
  font-size: 0.72rem;
  font-weight: 800;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.uc-badge.principal {
  color: #15803d;
}

.uc-badge.seleccionada {
  color: #15803d !important;
  font-weight: 900;
  background: #ffffff;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #86efac;
}

.btn-flyto {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0284c7;
  font-size: 0.74rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}
.btn-flyto:hover {
  background: #e0f2fe;
  border-color: #bae6fd;
}

.uc-actions-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-copy-gps, .btn-gmaps {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  font-size: 0.74rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  text-decoration: none;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-copy-gps {
  color: #16a34a;
}
.btn-copy-gps:hover {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.btn-gmaps {
  color: #ea580c;
}
.btn-gmaps:hover {
  background: #fff7ed;
  border-color: #fed7aa;
}

.uc-title {
  font-size: 0.88rem;
  font-weight: 800;
  color: #1e293b;
}

.uc-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  font-size: 0.76rem;
  color: #64748b;
}

.uc-coords {
  font-family: monospace;
  font-size: 0.72rem;
  color: #94a3b8;
}

.modal-grid { display:grid;grid-template-columns:1fr 1fr;gap:10px 14px; }
@media (max-width:520px) { .modal-grid { grid-template-columns:1fr; } }

/* ── HUD CARD FLOTANTE DE ODS EN EL MAPA (POSICIONADO BAJO EL SELECTOR DE CAPA) ── */
.map-ods-floating-card {
  position: absolute;
  top: 68px;
  right: 18px;
  z-index: 999;
  width: 320px;
  max-width: calc(100vw - 36px);
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(8px);
  animation: slideInDown 0.25s ease-out;
}

@keyframes slideInDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

.mofc-header {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #ffffff;
}

.mofc-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.mofc-badge {
  background: rgba(0, 0, 0, 0.25);
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.mofc-name {
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mofc-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mofc-btn-icon {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #ffffff;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background 0.15s ease;
}

.mofc-btn-icon:hover {
  background: rgba(255, 255, 255, 0.35);
}

.mofc-body {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mofc-stat-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
}

.mofc-stat-lbl {
  display: block;
  font-size: 0.65rem;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.5px;
}

.mofc-stat-val {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 2px 0;
}

.mofc-stat-val strong {
  font-size: 1.25rem;
  font-weight: 900;
  color: #0f172a;
}

.mofc-stat-val small {
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
}

.mofc-stat-yr {
  font-size: 0.72rem;
  color: #94a3b8;
  font-weight: 600;
}

.mofc-stat-sub {
  font-size: 0.72rem;
  color: #475569;
  line-height: 1.3;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mofc-impact-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.mofc-impact-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  color: #334155;
}

.mofc-impact-pill strong {
  color: #0f172a;
}

.mofc-btn-hist {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #334155;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}

.mofc-btn-hist:hover {
  background: #e2e8f0;
  color: #0f172a;
}

/* ── MODAL EVOLUCIÓN HISTÓRICA ODS ── */
.ods-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.ods-modal-box {
  background: #ffffff;
  border-radius: 16px;
  max-width: 620px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: modalPop 0.2s ease-out;
}

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.omb-hdr {
  padding: 14px 18px;
  color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.omb-hdr-info h3 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 8px;
}

.omb-hdr-info p {
  margin: 0;
  font-size: 0.78rem;
  opacity: 0.9;
  line-height: 1.35;
}

.omb-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #ffffff;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.85rem;
}

.omb-close:hover {
  background: rgba(255, 255, 255, 0.35);
}

.omb-body {
  padding: 18px;
  overflow-y: auto;
  flex: 1;
}

.omb-kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.omb-kpi-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 12px;
}

.okc-lbl {
  display: block;
  font-size: 0.65rem;
  font-weight: 800;
  color: #64748b;
  margin-bottom: 4px;
}

.okc-val {
  font-size: 1.15rem;
  font-weight: 900;
  color: #0f172a;
}

.okc-val small {
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748b;
}

.omb-subhdr {
  font-size: 0.88rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.omb-table-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.omb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.omb-table th {
  background: #f8fafc;
  padding: 8px 12px;
  text-align: left;
  font-weight: 700;
  color: #475569;
  border-bottom: 1px solid #e2e8f0;
}

.omb-table td {
  padding: 7px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}

.omb-table tr:last-child td {
  border-bottom: none;
}

.td-val {
  font-weight: 800;
  color: #0f172a;
}

.badge-unit {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
}

.trend-base { color: #94a3b8; font-size: 0.72rem; font-weight: 600; }
.trend-up { color: #dc2626; font-size: 0.72rem; font-weight: 700; }
.trend-down { color: #16a34a; font-size: 0.72rem; font-weight: 700; }
.trend-eq { color: #64748b; font-size: 0.72rem; font-weight: 600; }

.empty-hist {
  color: #94a3b8;
  font-size: 0.8rem;
  text-align: center;
  padding: 20px;
}

.omb-ftr {
  padding: 12px 18px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.btn-sec {
  background: #e2e8f0;
  border: none;
  color: #334155;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-sec:hover {
  background: #cbd5e1;
}

/* ── BADGES ODS EN MODAL DE PROYECTO ── */
.proy-ods-badges-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.proy-ods-badge-item {
  background: #ffffff;
  border: 1px solid var(--ods-col);
  color: var(--ods-col);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

.proy-ods-badge-item strong {
  font-weight: 800;
}
</style>
