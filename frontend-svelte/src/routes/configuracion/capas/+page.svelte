<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import Pagination from '$lib/Pagination.svelte';
  import * as XLSX from 'xlsx';

  // ── ESTADO GENERAL Y PESTAÑAS ──────────────────────────────────────────
  let tabActiva = $state('inec'); // 'inec' | 'ods'

  // ── ESTADO DE CAPAS TERRITORIALES INEC ────────────────────────────────
  let capas = $state([]);
  let cargando = $state(true);
  let subiendo = $state(false);
  let progreso = $state(0);
  let progresoInterval;

  let page = $state(1);
  let pageSize = $state(10);

  let form = $state({
    tipo_indicador: 'NBI',
    anio: 2022,
    unidad: '%',
    fuente: 'INEC - Censo de Población y Vivienda 2022',
    archivo: null,
  });

  let preview = $state(null);
  let errores = $state([]);

  // ── ESTADO DE CAPAS E INDICADORES ODS ─────────────────────────────────
  let listaOds = $state([]);
  let cargandoOds = $state(false);
  let subiendoLoteOds = $state(false);
  let progresoLote = $state(0);
  let loteDetectado = $state({}); // { 1: { ods_num, nombre_indicador, anio_reciente, valor_reciente, ... }, ... }
  let archivosProcesados = $state(0);
  let totalArchivosLote = $state(0);
  let odsModalDetalle = $state(null); // ODS seleccionado para ver serie histórica

  // Catálogo Maestro de los 17 ODS
  const CATALOGO_17_ODS = [
    { num: 1, nombre: "Fin de la Pobreza", color: "#E5243B", icono: "bi-cash-coin", desc: "Poner fin a la pobreza en todas sus formas en todo el mundo." },
    { num: 2, nombre: "Hambre Cero", color: "#DDA63A", icono: "bi-egg-fried", desc: "Poner fin al hambre, lograr la seguridad alimentaria y mejorar la nutrición." },
    { num: 3, nombre: "Salud y Bienestar", color: "#4C9F38", icono: "bi-heart-pulse-fill", desc: "Garantizar una vida sana y promover el bienestar para todos en todas las edades." },
    { num: 4, nombre: "Educación de Calidad", color: "#C5192D", icono: "bi-book-fill", desc: "Garantizar una educación inclusiva, equitativa y de calidad." },
    { num: 5, nombre: "Igualdad de Género", color: "#FF3A21", icono: "bi-gender-ambiguous", desc: "Lograr la igualdad entre los géneros y empoderar a todas las mujeres y las niñas." },
    { num: 6, nombre: "Agua Limpia y Saneamiento", color: "#26BDE2", icono: "bi-droplet-fill", desc: "Garantizar la disponibilidad de agua y su gestión sostenible y el saneamiento." },
    { num: 7, nombre: "Energía Asequible y No Contaminante", color: "#FCC30B", icono: "bi-lightning-charge-fill", desc: "Garantizar el acceso a una energía asequible, segura, sostenible y moderna." },
    { num: 8, nombre: "Trabajo Decente y Crecimiento Económico", color: "#A21942", icono: "bi-briefcase-fill", desc: "Promover el crecimiento económico inclusivo y sostenible, el empleo y el trabajo decente." },
    { num: 9, nombre: "Industria, Innovación e Infraestructura", color: "#FD6925", icono: "bi-building-gear", desc: "Construir infraestructuras resilientes, promover la industrialización sostenible y fomentar la innovación." },
    { num: 10, nombre: "Reducción de las Desigualdades", color: "#DD1367", icono: "bi-distribute-vertical", desc: "Reducir la desigualdad en y entre los países." },
    { num: 11, nombre: "Ciudades y Comunidades Sostenibles", color: "#FD9D24", icono: "bi-houses-fill", desc: "Lograr que las ciudades y los asentamientos humanos sean inclusivos, seguros, resilientes y sostenibles." },
    { num: 12, nombre: "Producción y Consumo Responsables", color: "#BF8B2E", icono: "bi-arrow-repeat", desc: "Garantizar modalidades de consumo y producción sostenibles." },
    { num: 13, nombre: "Acción por el Clima", color: "#3F7E44", icono: "bi-tree-fill", desc: "Adoptar medidas urgentes para combatir el cambio climático y sus efectos." },
    { num: 14, nombre: "Vida Submarina", color: "#0A97D9", icono: "bi-water", desc: "Conservar y utilizar sosteniblemente los océanos, los mares y los recursos marinos." },
    { num: 15, nombre: "Vida de Ecosistemas Terrestres", color: "#56C02B", icono: "bi-flower1", desc: "Gestionar sosteniblemente los bosques, luchar contra la desertificación y detener la pérdida de biodiversidad." },
    { num: 16, nombre: "Paz, Justicia e Instituciones Sólidas", color: "#00689D", icono: "bi-shield-check", desc: "Promover sociedades pacíficas e inclusivas para el desarrollo sostenible." },
    { num: 17, nombre: "Alianzas para Lograr los Objetivos", color: "#19486A", icono: "bi-people-fill", desc: "Revitalizar la Alianza Mundial para el Desarrollo Sostenible." },
  ];

  let odsCargadosCount = $derived(listaOds.filter(o => o.cargado).length);
  let odsDetectadosCount = $derived(Object.keys(loteDetectado).length);

  // ── CARGA INICIAL ─────────────────────────────────────────────────────
  async function cargarTodo() {
    await Promise.all([cargarCapasINEC(), cargarCapasODS()]);
  }

  async function cargarCapasINEC() {
    cargando = true;
    try { 
      capas = await fetchAPI('/api/capas-indicador/'); 
    } catch (e) { 
      toast.error('No se pudieron cargar las capas territoriales'); 
    } finally { 
      cargando = false; 
    }
  }

  async function cargarCapasODS() {
    cargandoOds = true;
    try {
      const data = await fetchAPI('/api/capas-ods/');
      listaOds = data;
    } catch (e) {
      toast.error('No se pudieron cargar los indicadores ODS');
    } finally {
      cargandoOds = false;
    }
  }

  onMount(cargarTodo);

  // ═══════════════════════════════════════════════════════════════════════
  // 1. LÓGICA CAPA TERRITORIAL INEC (NBI ORIGINAL)
  // ═══════════════════════════════════════════════════════════════════════
  function onFileINEC(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    form.archivo = f;
    const reader = new FileReader();
    reader.onload = () => parseCSVINEC(reader.result);
    reader.readAsText(f, 'utf-8');
  }

  function parseCSVINEC(txt) {
    errores = [];
    const lines = txt.split(/\r?\n/).filter(l => l.trim());
    if (!lines.length) { errores = ['El archivo CSV está completamente vacío']; preview = null; return; }
    
    const firstLine = lines[0];
    const sep = firstLine.includes(';') && !firstLine.includes(',') ? ';' : (firstLine.includes('\t') ? '\t' : ',');
    const header = firstLine.split(sep).map(s => s.trim().toLowerCase().replace(/^["']|["']$/g, ''));
    const iDpa = header.indexOf('dpa_canton');
    const iVal = header.indexOf('valor');
    
    if (iDpa < 0 || iVal < 0) {
      errores = [
        'Faltan columnas requeridas: "dpa_canton" y "valor"',
        `Columnas detectadas: [${header.join(', ')}]`
      ];
      preview = null;
      return;
    }
    
    const rows = [];
    const vistos = new Set();
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const c = line.split(sep).map(s => s.trim().replace(/^["']|["']$/g, ''));
      const dpa = c[iDpa]?.padStart(4, '0');
      const valRaw = c[iVal]?.replace(',', '.');
      const val = parseFloat(valRaw);
      
      if (!dpa || !/^\d{4}$/.test(dpa)) { 
        errores.push(`Fila ${i+1}: código DPA inválido "${c[iDpa]}"`); 
        continue; 
      }
      if (isNaN(val)) { 
        errores.push(`Fila ${i+1}: valor numérico inválido "${c[iVal]}"`); 
        continue; 
      }
      vistos.add(dpa);
      rows.push({ dpa_canton: dpa, valor: val });
    }
    preview = rows;
  }

  async function subirINEC() {
    if (!form.tipo_indicador.trim()) { toast.error('Indica el tipo de indicador'); return; }
    if (!form.archivo)      { toast.error('Selecciona un archivo CSV'); return; }
    if (!preview?.length)   { toast.error('El archivo CSV no contiene filas válidas'); return; }
    if (!form.fuente.trim()){ toast.error('Indica la fuente oficial'); return; }
    
    subiendo = true;
    progreso = 20;
    progresoInterval = setInterval(() => {
      if (progreso < 85) progreso += Math.floor(Math.random() * 15) + 5;
    }, 200);

    try {
      const fd = new FormData();
      fd.append('tipo_indicador', form.tipo_indicador.trim().toUpperCase());
      fd.append('anio', form.anio);
      fd.append('unidad', form.unidad);
      fd.append('fuente', form.fuente);
      fd.append('archivo', form.archivo);

      const r = await fetch('/api/capas-indicador/upload/', { 
        method: 'POST', 
        body: fd, 
        credentials: 'include' 
      });

      progreso = 100;
      clearInterval(progresoInterval);

      let data;
      const textResponse = await r.text();
      try {
        data = JSON.parse(textResponse);
      } catch (err) {
        throw new Error('Error en el servidor al procesar la capa');
      }

      if (!r.ok) throw new Error(data.error || 'Error al subir la capa');

      toast.success(`¡Capa guardada con éxito! ${data.insertados} cantones actualizados (${data.tipo_indicador} ${data.anio})`);
      form = { tipo_indicador: 'NBI', anio: 2022, unidad: '%', fuente: 'INEC - Censo de Población y Vivienda 2022', archivo: null };
      preview = null; 
      errores = [];
      const fileInput = document.getElementById('csvinput-inec');
      if (fileInput) fileInput.value = '';
      await cargarCapasINEC();
    } catch (e) {
      clearInterval(progresoInterval);
      toast.error(e.message || 'Error al procesar el archivo');
    } finally { 
      setTimeout(() => { subiendo = false; progreso = 0; }, 500);
    }
  }

  async function eliminarINEC(c) {
    const ok = await confirmDialog({
      title: '¿Eliminar capa territorial?',
      message: `Se eliminará la capa "${c.tipo_indicador} ${c.anio}" y sus ${c.total} registros cantonales asociados.`,
      confirmText: 'Sí, eliminar capa',
      type: 'danger',
      icon: 'bi-map-fill'
    });
    if (!ok) return;

    try {
      const r = await fetch(`/api/capas-indicador/${c.tipo_indicador}/${c.anio}/`, { 
        method: 'DELETE', 
        credentials: 'include' 
      });
      if (!r.ok) throw new Error('No se pudo eliminar la capa');
      toast.success('Capa territorial eliminada correctamente');
      await cargarCapasINEC();
    } catch (e) { 
      toast.error(e.message); 
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 2. LÓGICA DE DETECCIÓN Y CARGA MASIVA AUTOMÁTICA DE ODS (BATCH)
  // ═══════════════════════════════════════════════════════════════════════

  function detectarNumeroODS(nombreArchivo, contenidoTexto) {
    const t = (nombreArchivo + ' ' + contenidoTexto.slice(0, 2000)).toLowerCase();
    
    // Reglas de coincidencia por códigos CEPAL / ONU y palabras clave
    if (t.includes('si_pov_day1') || t.includes('pobreza') || t.includes('ods_1') || t.includes('ods1') || t.includes('objetivo 1') || t.includes('goal 1') || t.includes('poverty')) return 1;
    if (t.includes('sn_itk_defc') || t.includes('subalimentacion') || t.includes('hambre') || t.includes('ag_prd_fies') || t.includes('ods_2') || t.includes('ods2') || t.includes('objetivo 2') || t.includes('hunger')) return 2;
    if (t.includes('sh_') || t.includes('salud') || t.includes('mortalidad') || t.includes('vacunacion') || t.includes('ods_3') || t.includes('ods3') || t.includes('objetivo 3') || t.includes('health')) return 3;
    if (t.includes('se_') || t.includes('educacion') || t.includes('alfabetizacion') || t.includes('escolaridad') || t.includes('ods_4') || t.includes('ods4') || t.includes('objetivo 4') || t.includes('education')) return 4;
    if (t.includes('sg_') || t.includes('genero') || t.includes('mujeres') || t.includes('femicidio') || t.includes('ods_5') || t.includes('ods5') || t.includes('objetivo 5') || t.includes('gender')) return 5;
    if (t.includes('sh_h2o') || t.includes('agua') || t.includes('saneamiento') || t.includes('potable') || t.includes('ods_6') || t.includes('ods6') || t.includes('objetivo 6') || t.includes('water')) return 6;
    if (t.includes('eg_') || t.includes('energia') || t.includes('electricidad') || t.includes('renovable') || t.includes('ods_7') || t.includes('ods7') || t.includes('objetivo 7') || t.includes('energy')) return 7;
    if (t.includes('sl_') || t.includes('empleo') || t.includes('trabajo') || t.includes('desempleo') || t.includes('pib') || t.includes('ods_8') || t.includes('ods8') || t.includes('objetivo 8') || t.includes('decent work')) return 8;
    if (t.includes('nv_') || t.includes('industria') || t.includes('innovacion') || t.includes('investigacion') || t.includes('ods_9') || t.includes('ods9') || t.includes('objetivo 9') || t.includes('industry')) return 9;
    if (t.includes('gini') || t.includes('desigualdad') || t.includes('ingresos') || t.includes('ods_10') || t.includes('ods10') || t.includes('objetivo 10') || t.includes('inequality')) return 10;
    if (t.includes('en_') || t.includes('ciudades') || t.includes('urban') || t.includes('asentamientos') || t.includes('ods_11') || t.includes('ods11') || t.includes('objetivo 11') || t.includes('cities')) return 11;
    if (t.includes('consumo') || t.includes('produccion') || t.includes('residuos') || t.includes('reciclaje') || t.includes('ods_12') || t.includes('ods12') || t.includes('objetivo 12') || t.includes('consumption')) return 12;
    if (t.includes('clim') || t.includes('co2') || t.includes('emisiones') || t.includes('desastres') || t.includes('ods_13') || t.includes('ods13') || t.includes('objetivo 13') || t.includes('climate')) return 13;
    if (t.includes('mar') || t.includes('submarina') || t.includes('pesca') || t.includes('costas') || t.includes('ods_14') || t.includes('ods14') || t.includes('objetivo 14') || t.includes('ocean')) return 14;
    if (t.includes('bosque') || t.includes('deforestacion') || t.includes('terrestre') || t.includes('biodiversidad') || t.includes('ods_15') || t.includes('ods15') || t.includes('objetivo 15') || t.includes('biodiversity')) return 15;
    if (t.includes('paz') || t.includes('justicia') || t.includes('homicidio') || t.includes('instituciones') || t.includes('ods_16') || t.includes('ods16') || t.includes('objetivo 16') || t.includes('peace')) return 16;
    if (t.includes('alianza') || t.includes('cooperacion') || t.includes('asociaciones') || t.includes('ods_17') || t.includes('ods17') || t.includes('objetivo 17') || t.includes('partnership')) return 17;
    
    return null;
  }

  function procesarFilasODS(nombreArchivo, rows) {
    if (!rows || !rows.length) return null;

    const firstRowsStr = JSON.stringify(rows.slice(0, 10));
    const odsNum = detectarNumeroODS(nombreArchivo, firstRowsStr);
    if (!odsNum) return null;

    const odsInfo = CATALOGO_17_ODS.find(o => o.num === odsNum);
    let nombreIndicador = '';
    let codigoIndicador = '';
    let unidad = '%';
    const serieHistorica = [];

    for (const r of rows) {
      // Normalizar nombres de columnas a minúsculas sin acentos ni espacios
      const norm = {};
      for (const [k, v] of Object.entries(r)) {
        if (!k) continue;
        const kn = k.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[\s_]+/g, "");
        norm[kn] = v;
      }

      // 1. Filtrar solo filas correspondientes a Ecuador
      const paisVal = String(norm['paisestandar'] || norm['pais'] || norm['country'] || norm['location'] || norm['area'] || '');
      if (paisVal && !paisVal.toLowerCase().includes('ecuador')) {
        continue;
      }

      // 2. Extraer nombre de indicador
      const indVal = String(norm['indicator'] || norm['indicador'] || norm['meta'] || norm['series'] || '');
      if (indVal && !nombreIndicador) {
        nombreIndicador = indVal;
        const matchCode = indVal.match(/([A-Z0-9_]{4,})/);
        codigoIndicador = matchCode ? matchCode[1] : `ODS_${odsNum}`;
      }

      // 3. Extraer unidad
      const unitVal = String(norm['unit'] || norm['unidad'] || norm['measure'] || '');
      if (unitVal && unidad === '%') {
        unidad = unitVal;
      }

      // 4. Extraer año y valor
      const anioRaw = String(norm['anosestandar'] || norm['aniosestandar'] || norm['ano'] || norm['anio'] || norm['year'] || norm['timeperiod'] || '');
      const anio = parseInt(anioRaw);
      
      const valRaw = String(norm['value'] || norm['valor'] || norm['dato'] || norm['val'] || '').replace(',', '.');
      const val = parseFloat(valRaw);

      if (!isNaN(anio) && !isNaN(val)) {
        serieHistorica.push({ anio, valor: val });
      }
    }

    if (!serieHistorica.length) return null;

    // Deduplicar años y ordenar ascendentemente
    const mapaAnios = new Map();
    for (const item of serieHistorica) {
      mapaAnios.set(item.anio, item.valor);
    }
    const serieLimpia = Array.from(mapaAnios.entries())
      .map(([anio, valor]) => ({ anio, valor }))
      .sort((a, b) => a.anio - b.anio);

    const masReciente = serieLimpia[serieLimpia.length - 1];

    return {
      ods_num: odsNum,
      nombre_ods: odsInfo ? odsInfo.nombre : `ODS ${odsNum}`,
      codigo_indicador: codigoIndicador || `ODS_${odsNum}`,
      nombre_indicador: nombreIndicador || `${odsInfo?.nombre || 'Indicador Oficial'} (Ecuador)`,
      anio_reciente: masReciente.anio,
      valor_reciente: masReciente.valor,
      unidad: unidad || '%',
      fuente: 'CEPAL / ONU - Agenda 2030 Ecuador',
      serie_historica: serieLimpia,
      nombre_archivo: nombreArchivo,
    };
  }

  let auditoriaLote = $state([]); // Logs de auditoría de cada archivo procesado
  let odsFaltantes = $derived(
    [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17].filter(num => !loteDetectado[num] && !listaOds.find(o => o.num === num && o.cargado))
  );

  async function onArchivoIndividualODS(odsNum, e) {
    const f = e.target.files?.[0];
    if (!f) return;

    try {
      const buffer = await f.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: 'array' });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const rows = XLSX.utils.sheet_to_json(worksheet, { defval: '', raw: false });

      let parsed = procesarFilasODS(f.name, rows);
      if (!parsed) {
        // Asignar directamente al ODS del cuadro
        const odsInfo = CATALOGO_17_ODS.find(o => o.num === odsNum);
        parsed = {
          ods_num: odsNum,
          nombre_ods: odsInfo ? odsInfo.nombre : `ODS ${odsNum}`,
          codigo_indicador: `ODS_${odsNum}`,
          nombre_indicador: `${odsInfo?.nombre || 'Indicador Oficial'} (Ecuador)`,
          anio_reciente: 2023,
          valor_reciente: 0,
          unidad: '%',
          fuente: 'CEPAL / ONU - Agenda 2030 Ecuador',
          serie_historica: [],
          nombre_archivo: f.name,
        };
      } else {
        parsed.ods_num = odsNum;
        parsed.nombre_ods = CATALOGO_17_ODS.find(o => o.num === odsNum)?.nombre || `ODS ${odsNum}`;
      }

      loteDetectado = { ...loteDetectado, [odsNum]: parsed };

      auditoriaLote = [
        ...auditoriaLote.filter(l => l.ods_num !== odsNum),
        {
          nombre_archivo: f.name,
          ods_num: odsNum,
          nombre_ods: parsed.nombre_ods,
          total_anios: parsed.serie_historica.length,
          anio_reciente: parsed.anio_reciente,
          valor_reciente: parsed.valor_reciente,
          unidad: parsed.unidad,
          es_duplicado: false,
        }
      ];
      totalArchivosLote = auditoriaLote.length;
      toast.success(`✓ ODS ${odsNum}: ${parsed.nombre_ods} cargado`);
    } catch (err) {
      console.error(err);
      toast.error('Error al procesar el archivo');
    }
  }

  async function onArchivosLoteODS(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    totalArchivosLote = files.length;
    archivosProcesados = 0;
    const nuevoLote = { ...loteDetectado };
    const logs = [];

    for (const f of files) {
      try {
        const buffer = await f.arrayBuffer();
        const workbook = XLSX.read(buffer, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        const rows = XLSX.utils.sheet_to_json(worksheet, { defval: '', raw: false });

        const parsed = procesarFilasODS(f.name, rows);
        if (parsed) {
          const yaExiste = nuevoLote[parsed.ods_num];
          const esDup = Boolean(yaExiste);
          
          if (yaExiste) {
            if (parsed.serie_historica.length >= yaExiste.serie_historica.length) {
              nuevoLote[parsed.ods_num] = parsed;
            }
          } else {
            nuevoLote[parsed.ods_num] = parsed;
          }

          logs.push({
            nombre_archivo: f.name,
            ods_num: parsed.ods_num,
            nombre_ods: parsed.nombre_ods,
            total_anios: parsed.serie_historica.length,
            anio_reciente: parsed.anio_reciente,
            valor_reciente: parsed.valor_reciente,
            unidad: parsed.unidad,
            es_duplicado: esDup,
          });
        }
      } catch (err) {
        console.error('Error leyendo archivo ODS:', f.name, err);
      }
      archivosProcesados++;
    }

    auditoriaLote = logs;
    loteDetectado = nuevoLote;
    const count = Object.keys(loteDetectado).length;
    if (count > 0) {
      toast.success(`¡Se reconocieron ${count} indicadores ODS!`);
    }
  }

  async function guardarTodosLoteODS() {
    const items = Object.values(loteDetectado);
    if (!items.length) {
      toast.error('No hay indicadores ODS detectados para guardar');
      return;
    }

    subiendoLoteOds = true;
    progresoLote = 30;

    try {
      const res = await fetch('/api/capas-ods/batch-upload/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(items),
        credentials: 'include',
      });

      progresoLote = 100;
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al guardar');

      toast.success(`¡Excelente! ${data.procesados} indicadores ODS guardados en la base de datos.`);
      loteDetectado = {};
      await cargarCapasODS();
    } catch (e) {
      toast.error(e.message || 'Error al guardar los indicadores');
    } finally {
      subiendoLoteOds = false;
      progresoLote = 0;
    }
  }

  async function eliminarODS(num, nombre) {
    const ok = await confirmDialog({
      title: '¿Eliminar indicador ODS?',
      message: `Se eliminarán los datos históricos del "ODS ${num}: ${nombre}".`,
      confirmText: 'Sí, eliminar',
      type: 'danger',
      icon: 'bi-trash-fill'
    });
    if (!ok) return;

    try {
      const r = await fetch(`/api/capas-ods/${num}/delete/`, { method: 'DELETE', credentials: 'include' });
      if (!r.ok) throw new Error('No se pudo eliminar el indicador');
      toast.success(`Datos del ODS ${num} eliminados`);
      await cargarCapasODS();
    } catch (e) {
      toast.error(e.message);
    }
  }
</script>

<svelte:head><title>Gestión de Capas e Indicadores — SGV UTEQ</title></svelte:head>

<!-- SUBBAR SUPERIOR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/configuracion">Configuración</a>
    <span class="sep">/</span>
    <span class="current">Gestión de Capas</span>
  </nav>
</div>

<div class="cap-body">

  <!-- SELECTOR DE SUBMÓDULOS EN TABS ELEGANTES -->
  <div class="cap-nav-tabs">
    <button 
      type="button" 
      class="nav-tab-btn" 
      class:active={tabActiva === 'inec'} 
      onclick={() => tabActiva = 'inec'}>
      <i class="bi bi-geo-alt-fill"></i>
      <span>1. Capas Territoriales INEC (NBI y Cantones)</span>
      <span class="badge-tab">{capas.length} Activas</span>
    </button>
    <button 
      type="button" 
      class="nav-tab-btn" 
      class:active={tabActiva === 'ods'} 
      onclick={() => tabActiva = 'ods'}>
      <i class="bi bi-globe-americas"></i>
      <span>2. Gestión de Capas ODS (Agenda 2030 CEPAL/ONU)</span>
      <span class="badge-tab highlight">{odsCargadosCount}/17 ODS</span>
    </button>
  </div>

  <!-- ════════════════════════════════════════════════════════════════════ -->
  <!-- VISTA 1: CAPAS TERRITORIALES INEC (INTACTA)                          -->
  <!-- ════════════════════════════════════════════════════════════════════ -->
  {#if tabActiva === 'inec'}
    <!-- FORM DE CARGA INEC -->
    <section class="cap-card">
      <header class="cap-h">
        <div class="cap-h-icon inec-color">
          <i class="bi bi-cloud-arrow-up-fill"></i>
        </div>
        <div>
          <h3>Cargar Capa Territorial INEC</h3>
          <p>Sube un archivo CSV con los valores oficiales de Necesidades Básicas Insatisfechas (NBI) o indicadores por cantón.</p>
        </div>
      </header>

      <div class="cap-form">
        <div class="fg">
          <label>Tipo de indicador</label>
          <input type="text" bind:value={form.tipo_indicador} maxlength="30" placeholder="NBI, POBREZA..." />
        </div>
        <div class="fg">
          <label>Año de la medición</label>
          <input type="number" bind:value={form.anio} min="1990" max="2100" />
        </div>
        <div class="fg">
          <label>Unidad de medida</label>
          <input type="text" bind:value={form.unidad} maxlength="20" placeholder="%" />
        </div>
        <div class="fg wide">
          <label>Fuente oficial</label>
          <input type="text" bind:value={form.fuente} maxlength="160" placeholder="Ej: INEC - Censo de Población y Vivienda 2022" />
        </div>
        <div class="fg wide">
          <label>Archivo CSV de cantones <span class="hint">(Columnas requeridas: <code>dpa_canton</code>, <code>valor</code>)</span></label>
          <div class="file-uploader-box">
            <input id="csvinput-inec" type="file" accept=".csv,text/csv" onchange={onFileINEC} class="file-hidden-input" />
            <label for="csvinput-inec" class="file-browse-btn">
              <i class="bi bi-folder2-open"></i> Seleccionar archivo CSV
            </label>
            <span class="file-selected-name">
              {#if form.archivo}
                <i class="bi bi-file-earmark-check-fill text-success"></i> {form.archivo.name}
              {:else}
                <span class="text-muted">Ningún archivo seleccionado</span>
              {/if}
            </span>
          </div>
        </div>
      </div>

      {#if errores.length}
        <div class="alert warn">
          <b>{errores.length} advertencias:</b>
          <ul>{#each errores.slice(0,5) as e}<li>{e}</li>{/each}</ul>
        </div>
      {/if}

      {#if preview}
        <div class="alert ok">
          ✓ <b>{preview.length}</b> cantones válidos listos para indexar.
        </div>
      {/if}

      {#if subiendo}
        <div class="progress-wrap">
          <div class="progress-header">
            <span class="progress-label"><i class="bi bi-arrow-repeat spin"></i> Procesando datos cantonales...</span>
            <span class="progress-pct">{progreso}%</span>
          </div>
          <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: {progreso}%;"></div></div>
        </div>
      {/if}

      <div class="cap-actions">
        <button class="btn-primario" onclick={subirINEC} disabled={subiendo || !preview?.length}>
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Guardando...{:else}<i class="bi bi-check-lg"></i> Guardar Capa Territorial{/if}
        </button>
      </div>
    </section>

    <!-- LISTA DE CAPAS INEC -->
    <section class="cap-card table-card">
      <header class="cap-h">
        <div class="cap-h-icon inec-color">
          <i class="bi bi-database-fill-check"></i>
        </div>
        <div>
          <h3>Capas Territoriales Activas</h3>
          <p>Capas de polígonos disponibles para visualización en el mapa interactivo.</p>
        </div>
      </header>

      {#if cargando}
        <div class="empty"><i class="bi bi-arrow-repeat spin"></i> Cargando capas...</div>
      {:else if !capas.length}
        <div class="empty">No hay capas cargadas todavía. Sube una con el formulario superior.</div>
      {:else}
        <div class="table-responsive">
          <table class="cap-table">
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Año</th>
                <th>Cantones</th>
                <th>Rango ({capas[0]?.unidad || '%'})</th>
                <th>Unidad</th>
                <th>Fuente</th>
                <th>Estado</th>
                <th class="text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {#each capas.slice((page-1)*pageSize, page*pageSize) as c}
                <tr>
                  <td><span class="badge-indicador">{c.tipo_indicador}</span></td>
                  <td><strong>{c.anio}</strong></td>
                  <td>{c.total} cantones</td>
                  <td>
                    {#if c.min !== null && c.max !== null}
                      <span class="rango-badge">{c.min}% — {c.max}%</span>
                    {:else}
                      —
                    {/if}
                  </td>
                  <td>{c.unidad}</td>
                  <td class="td-fuente" title={c.fuente}>{c.fuente}</td>
                  <td><span class="badge-activa"><i class="bi bi-check-circle-fill"></i> Activa</span></td>
                  <td class="text-right">
                    <button class="btn-action-view" onclick={() => window.location.href='/mapa'} title="Ver en el Mapa">
                      <i class="bi bi-map"></i>
                    </button>
                    <button class="btn-action-delete" onclick={() => eliminarINEC(c)} title="Eliminar capa">
                      <i class="bi bi-trash"></i>
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        <Pagination totalItems={capas.length} bind:currentPage={page} bind:pageSize={pageSize} />
      {/if}
    </section>
  {/if}

  <!-- ════════════════════════════════════════════════════════════════════ -->
  <!-- VISTA 2: GESTIÓN DE CAPAS ODS (17 CUADROS CON CARGA DIRECTA)         -->
  <!-- ════════════════════════════════════════════════════════════════════ -->
  {#if tabActiva === 'ods'}
    <section class="cap-card">
      <header class="cap-h">
        <div class="cap-h-icon ods-color">
          <i class="bi bi-grid-3x3-gap-fill"></i>
        </div>
        <div class="cap-h-between">
          <div>
            <h3>Matriz de los 17 Objetivos de Desarrollo Sostenible (Agenda 2030)</h3>
            <p>Carga el archivo Excel (.xlsx) o CSV en el cuadro de cada ODS. Al finalizar, pulsa el botón inferior para guardar en el sistema.</p>
          </div>
          <div class="ods-counter-badge">
            <strong>{odsCargadosCount}</strong> / 17 Activos
          </div>
        </div>
      </header>

      {#if cargandoOds}
        <div class="empty"><i class="bi bi-arrow-repeat spin"></i> Cargando matriz ODS...</div>
      {:else}
        <!-- MATRIZ DIRECTA DE LOS 17 ODS -->
        <div class="ods-grid-17">
          {#each listaOds as ods}
            {@const enLote = loteDetectado[ods.ods_num]}
            {@const dato = enLote || (ods.cargado ? ods : null)}
            <div 
              class="ods-card" 
              class:has-data={dato !== null}
              class:is-pending-save={enLote !== undefined}
              style="--ods-color: {ods.color};">
              
              <!-- INPUT OCULTO DE CARGA INDIVIDUAL PARA ESTE ODS -->
              <input 
                id="file-ods-{ods.num}" 
                type="file" 
                accept=".xlsx,.xls,.csv,.tsv,.txt,.ods" 
                onchange={(e) => onArchivoIndividualODS(ods.num, e)} 
                class="file-hidden-input" />

              <div class="ods-card-top" style="background-color: {ods.color};">
                <span class="ods-num">ODS {ods.num}</span>
                <i class="bi {ods.icono} ods-top-icon"></i>
              </div>

              <div class="ods-card-body">
                <h4 class="ods-title">{ods.nombre}</h4>

                {#if dato}
                  <div class="ods-data-box">
                    <div class="odb-header">
                      <span class="odb-tag" class:odb-lote={enLote}>
                        {enLote ? '⚡ Listo para guardar' : '✓ En Base de Datos'}
                      </span>
                      <span class="odb-year">{dato.anio_reciente}</span>
                    </div>
                    <div class="odb-value-wrap">
                      <span class="odb-value">{dato.valor_reciente}</span>
                      <span class="odb-unit">{dato.unidad}</span>
                    </div>
                    <p class="odb-ind-name" title={dato.nombre_indicador}>{dato.nombre_indicador}</p>
                    <div class="odb-meta-row">
                      <small><i class="bi bi-clock-history"></i> {dato.serie_historica?.length || 0} años registrados</small>
                    </div>
                    {#if dato.nombre_archivo}
                      <div class="odb-file-pill" title={dato.nombre_archivo}>
                        <i class="bi bi-file-earmark-spreadsheet"></i> {dato.nombre_archivo}
                      </div>
                    {/if}
                  </div>
                {:else}
                  <label for="file-ods-{ods.num}" class="ods-empty-upload-box">
                    <i class="bi bi-cloud-arrow-up-fill"></i>
                    <strong>Cargar archivo Excel</strong>
                    <span>Haz clic aquí para seleccionar (.xlsx o .csv)</span>
                  </label>
                {/if}
              </div>

              <div class="ods-card-footer">
                {#if dato}
                  <button 
                    type="button" 
                    class="btn-ods-mini view" 
                    onclick={() => odsModalDetalle = dato}
                    title="Ver evolución histórica">
                    <i class="bi bi-graph-up"></i> Histórico
                  </button>
                  <label for="file-ods-{ods.num}" class="btn-ods-mini edit" title="Cambiar archivo">
                    <i class="bi bi-arrow-repeat"></i> Cambiar
                  </label>
                  {#if ods.cargado}
                    <button 
                      type="button" 
                      class="btn-ods-mini del" 
                      onclick={() => eliminarODS(ods.ods_num, ods.nombre)}
                      title="Eliminar indicador">
                      <i class="bi bi-trash"></i>
                    </button>
                  {/if}
                {:else}
                  <label for="file-ods-{ods.num}" class="btn-ods-mini upload-hint">
                    <i class="bi bi-plus-circle"></i> Seleccionar
                  </label>
                {/if}
              </div>
            </div>
          {/each}
        </div>

        <!-- CERTIFICACIÓN Y TRAZABILIDAD DE ARCHIVOS PROCESADOS -->
        {#if auditoriaLote.length > 0}
          <div class="ods-audit-card">
            <div class="oac-hdr">
              <h4><i class="bi bi-shield-check"></i> Certificación y Trazabilidad de Archivos ({totalArchivosLote} cargados)</h4>
              <span class="oac-stat">{odsDetectadosCount} ODS Listos</span>
            </div>
            <div class="oac-list">
              {#each auditoriaLote as aud}
                <div class="oac-item" class:is-duplicate={aud.es_duplicado}>
                  <div class="oac-icon">
                    <i class="bi {aud.es_duplicado ? 'bi-exclamation-triangle-fill text-amber' : 'bi-check-circle-fill text-green'}"></i>
                  </div>
                  <div class="oac-detail">
                    <div class="oac-title-row">
                      <strong class="oac-filename">{aud.nombre_archivo}</strong>
                      {#if aud.es_duplicado}
                        <span class="badge-dup">⚠️ Repetido / Reemplazo</span>
                      {/if}
                    </div>
                    <span class="oac-sub">➔ Asignado a <b>ODS {aud.ods_num}: {aud.nombre_ods}</b> ({aud.total_anios} años históricos, valor {aud.valor_reciente} {aud.unidad} en {aud.anio_reciente})</span>
                  </div>
                </div>
              {/each}
            </div>

            {#if odsFaltantes.length > 0}
              <div class="oac-missing-alert">
                <i class="bi bi-info-circle-fill"></i>
                <span><b>Pendientes de archivo ({odsFaltantes.length} ODS):</b> {odsFaltantes.map(n => `ODS ${n}`).join(', ')}.</span>
              </div>
            {/if}
          </div>
        {/if}

        <!-- BOTÓN FINAL DE GUARDAR TODOS LOS 17 ODS -->
        <div class="ods-bottom-save-bar">
          <div class="obs-left">
            <strong>{odsDetectadosCount > 0 ? `${odsDetectadosCount} ODS listos para guardar en base de datos` : 'Selecciona los archivos en los cuadros de arriba'}</strong>
            <p>Al guardar, los datos oficiales de Ecuador se sincronizarán permanentemente con todos los proyectos universitarios.</p>
          </div>
          <button 
            type="button" 
            class="btn-guardar-ods-final" 
            onclick={guardarTodosLoteODS} 
            disabled={subiendoLoteOds || odsDetectadosCount === 0}>
            {#if subiendoLoteOds}
              <i class="bi bi-arrow-repeat spin"></i> Guardando ODS en el Sistema...
            {:else}
              <i class="bi bi-cloud-check-fill"></i> Guardar los ODS en el Sistema ({odsDetectadosCount})
            {/if}
          </button>
        </div>
      {/if}
    </section>
  {/if}

</div>

<!-- MODAL PARA VER SERIE HISTÓRICA DE UN ODS -->
{#if odsModalDetalle}
  <div class="modal-overlay" onclick={() => odsModalDetalle = null}>
    <div class="modal-box" onclick={e => e.stopPropagation()}>
      <div class="modal-hdr" style="background-color: {odsModalDetalle.color || '#1b7a2b'};">
        <div>
          <h3>ODS {odsModalDetalle.ods_num}: {odsModalDetalle.nombre_ods}</h3>
          <p>{odsModalDetalle.nombre_indicador}</p>
        </div>
        <button class="modal-close-btn" onclick={() => odsModalDetalle = null}>&times;</button>
      </div>
      <div class="modal-content-scroll">
        <div class="m-highlight-banner">
          <div>
            <span class="mhb-label">Valor más reciente en Ecuador</span>
            <div class="mhb-val">{odsModalDetalle.valor_reciente} <small>{odsModalDetalle.unidad}</small></div>
          </div>
          <div class="text-right">
            <span class="mhb-label">Año de medición</span>
            <div class="mhb-year">{odsModalDetalle.anio_reciente}</div>
          </div>
        </div>

        <h4 class="m-sec-title"><i class="bi bi-clock-history"></i> Serie Histórica Registrada</h4>
        {#if odsModalDetalle.serie_historica && odsModalDetalle.serie_historica.length}
          <div class="table-responsive">
            <table class="cap-table">
              <thead>
                <tr>
                  <th>Año</th>
                  <th>Valor</th>
                  <th>Unidad</th>
                  <th>Tendencia</th>
                </tr>
              </thead>
              <tbody>
                {#each odsModalDetalle.serie_historica as pt, idx}
                  {@const anterior = idx > 0 ? odsModalDetalle.serie_historica[idx - 1].valor : null}
                  <tr>
                    <td><strong>{pt.anio}</strong></td>
                    <td><b>{pt.valor}</b></td>
                    <td>{odsModalDetalle.unidad}</td>
                    <td>
                      {#if anterior !== null}
                        {#if pt.valor < anterior}
                          <span class="trend down"><i class="bi bi-arrow-down-right"></i> Reducción</span>
                        {:else if pt.valor > anterior}
                          <span class="trend up"><i class="bi bi-arrow-up-right"></i> Incremento</span>
                        {:else}
                          <span class="trend equal">= Estable</span>
                        {/if}
                      {:else}
                        <span class="trend base">Línea base</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <p class="empty">No hay serie histórica disponible para este indicador.</p>
        {/if}
      </div>
      <div class="modal-ftr">
        <button class="btn-sga-blue" onclick={() => odsModalDetalle = null}>Cerrar</button>
      </div>
    </div>
  </div>
{/if}

<style>
/* ── SUBBAR ── */
.subbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  background: #ffffff;
  border-bottom: 1px solid #eef2f6;
}
.breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 0.84rem; }
.breadcrumb a { color: #1b7a2b; text-decoration: none; font-weight: 700; }
.breadcrumb a:hover { text-decoration: underline; }
.breadcrumb .sep { color: #94a3b8; }
.breadcrumb .current { color: #1e293b; font-weight: 800; }

/* ── BODY ── */
.cap-body { padding: 24px 28px; display: flex; flex-direction: column; gap: 24px; }

/* ── PESTAÑAS SUBMÓDULO PERFECTAMENTE CENTRADAS ── */
.cap-nav-tabs {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
  margin-bottom: 4px;
}
.nav-tab-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.88rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}
.nav-tab-btn:hover {
  background: #f8fafc;
  color: #1e293b;
  border-color: #cbd5e1;
}
.nav-tab-btn.active {
  background: #1b7a2b;
  color: #ffffff;
  border-color: #1b7a2b;
  box-shadow: 0 4px 12px rgba(27, 122, 43, 0.25);
}
.badge-tab {
  background: rgba(0,0,0,0.06);
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 800;
}
.nav-tab-btn.active .badge-tab {
  background: rgba(255,255,255,0.25);
  color: #ffffff;
}

/* ── CARDS ── */
.cap-card {
  background: #ffffff;
  border: 1px solid #eef2f6;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.03);
}
.cap-h {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}
.cap-h-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.cap-h-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}
.cap-h-icon.inec-color { background: #eaf5ea; color: #1b7a2b; }
.cap-h-icon.ods-color { background: #e0f2fe; color: #0284c7; }
.cap-h h3 { font-size: 1.05rem; font-weight: 800; color: #1e293b; margin: 0 0 4px; }
.cap-h p { font-size: 0.8rem; color: #64748b; margin: 0; }

.ods-counter-badge {
  background: #f0fdf4;
  border: 1.5px solid #86efac;
  color: #166534;
  padding: 6px 14px;
  border-radius: 30px;
  font-size: 0.85rem;
  font-weight: 700;
}
.ods-counter-badge strong { font-size: 1.1rem; color: #15803d; }

/* ── FORMULARIO ── */
.cap-form {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.fg { display: flex; flex-direction: column; gap: 6px; }
.fg.wide { grid-column: span 3; }
.fg label { font-size: 0.72rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }
.fg .hint { text-transform: none; font-weight: 600; color: #94a3b8; }
.fg .hint code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; color: #1e293b; }
.fg input {
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 9px 14px;
  font-size: 0.86rem;
  font-family: inherit;
  font-weight: 600;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
  transition: all 0.2s ease;
}
.fg input:focus { border-color: #1b7a2b; background: #ffffff; box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.1); }

/* Uploader Box */
.file-uploader-box {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1.5px dashed #cbd5e1;
  border-radius: 10px;
}
.file-hidden-input { display: none; }
.file-browse-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #1e293b;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}
.file-browse-btn:hover { background: #f1f5f9; border-color: #94a3b8; }
.file-selected-name { font-size: 0.82rem; font-weight: 600; color: #1e293b; }

/* ── BOTONES ── */
.cap-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
.btn-primario {
  background: #1b7a2b;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 10px 22px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}
.btn-primario:hover:not(:disabled) { background: #15803d; box-shadow: 0 4px 12px rgba(27, 122, 43, 0.3); }
.btn-primario:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── PROGRESS BAR ── */
.progress-wrap { margin: 16px 0; }
.progress-header { display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
.progress-bar-bg { width: 100%; height: 8px; background: #e2e8f0; border-radius: 10px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: #1b7a2b; transition: width 0.2s ease; }

/* ── ALERTAS ── */
.alert { padding: 12px 16px; border-radius: 10px; font-size: 0.82rem; margin-bottom: 14px; }
.alert.warn { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
.alert.warn ul { margin: 6px 0 0 16px; padding: 0; }
.alert.ok { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; font-weight: 600; }

/* ── TABLA ── */
.table-responsive { overflow-x: auto; width: 100%; }
.cap-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; text-align: left; }
.cap-table th { padding: 12px 14px; font-size: 0.72rem; font-weight: 800; color: #64748b; text-transform: uppercase; background: #f8fafc; border-bottom: 1.5px solid #e2e8f0; }
.cap-table td { padding: 12px 14px; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
.cap-table tr:hover td { background: #f8fafc; }
.badge-indicador { background: #dcfce7; color: #166534; font-weight: 800; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; }
.rango-badge { background: #f1f5f9; font-weight: 700; padding: 3px 8px; border-radius: 6px; color: #334155; }
.badge-activa { color: #16a34a; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; }
.td-fuente { max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #64748b; font-size: 0.78rem; }
.btn-action-view { background: #eff6ff; color: #2563eb; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; margin-right: 4px; }
.btn-action-delete { background: #fef2f2; color: #dc2626; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; }
.text-right { text-align: right; }
.empty { text-align: center; padding: 36px 20px; color: #94a3b8; font-size: 0.88rem; font-weight: 600; }

/* ── ZONA DROPZONE ODS ── */
.ods-dropzone-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  background: #f8fafc;
  border: 2px dashed #0284c7;
  border-radius: 16px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}
.ods-dropzone-box:hover {
  background: #f0f9ff;
  border-color: #0369a1;
  transform: translateY(-2px);
}
.odz-icon { font-size: 2.8rem; color: #0284c7; margin-bottom: 8px; }
.odz-text strong { font-size: 1rem; color: #1e293b; display: block; margin-bottom: 4px; }
.odz-text p { font-size: 0.8rem; color: #64748b; margin: 0 0 16px; }
.odz-btn {
  background: #0284c7;
  color: #ffffff;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* ── AUDITORÍA Y TRAZABILIDAD DE LOTE ODS ── */
.ods-audit-card {
  margin-top: 18px;
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px 20px;
}
.oac-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f1f5f9;
}
.oac-hdr h4 { margin: 0; font-size: 0.92rem; font-weight: 800; color: #1e293b; display: flex; align-items: center; gap: 6px; }
.oac-stat { font-size: 0.76rem; font-weight: 800; color: #15803d; background: #dcfce7; padding: 3px 10px; border-radius: 20px; }

.oac-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}
.oac-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #eef2f6;
  border-radius: 8px;
  font-size: 0.8rem;
}
.oac-item.is-duplicate {
  background: #fffbeb;
  border-color: #fde68a;
}
.oac-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }
.text-green { color: #16a34a; }
.text-amber { color: #d97706; }
.oac-detail { display: flex; flex-direction: column; gap: 2px; }
.oac-title-row { display: flex; align-items: center; gap: 8px; }
.oac-filename { color: #1e293b; font-family: monospace; font-size: 0.82rem; }
.badge-dup { background: #fef3c7; color: #92400e; font-size: 0.68rem; font-weight: 800; padding: 1px 6px; border-radius: 4px; }
.oac-sub { color: #475569; font-size: 0.76rem; }

.oac-missing-alert {
  margin-top: 12px;
  padding: 10px 14px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  font-size: 0.78rem;
  color: #1e40af;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Pastilla de archivo original en tarjeta */
.odb-file-pill {
  margin-top: 8px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 0.68rem;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* BARRA FLOTANTE DE LOTE */
.ods-batch-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding: 14px 20px;
  background: #f0fdf4;
  border: 1.5px solid #86efac;
  border-radius: 12px;
}
.ob-badge { font-weight: 800; color: #166534; font-size: 0.92rem; display: flex; align-items: center; gap: 6px; }
.ob-sub { font-size: 0.78rem; color: #475569; display: block; }
.btn-guardar-lote {
  background: #16a34a;
  color: #ffffff;
  border: none;
  padding: 10px 22px;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
  transition: all 0.2s;
}
.btn-guardar-lote:hover:not(:disabled) { background: #15803d; transform: scale(1.02); }

/* ── GRID DE LOS 17 ODS ── */
.ods-grid-17 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.ods-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.ods-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.06);
  border-color: var(--ods-color);
}
.ods-card.has-data {
  border-color: #cbd5e1;
}
.ods-card.is-pending-save {
  border-color: #16a34a;
  box-shadow: 0 0 0 2px #86efac;
}
.ods-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  color: #ffffff;
}
.ods-num { font-size: 0.84rem; font-weight: 900; letter-spacing: 0.05em; text-transform: uppercase; }
.ods-top-icon { font-size: 1.15rem; }

.ods-card-body { padding: 14px; flex: 1; display: flex; flex-direction: column; }
.ods-title { font-size: 0.9rem; font-weight: 800; color: #1e293b; margin: 0 0 10px; line-height: 1.25; }

.ods-data-box {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
  border: 1px solid #eef2f6;
  flex: 1;
  display: flex;
  flex-direction: column;
}
.odb-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.odb-tag { font-size: 0.68rem; font-weight: 800; color: #16a34a; }
.odb-tag.odb-lote { color: #d97706; }
.odb-year { font-size: 0.72rem; font-weight: 700; color: #64748b; background: #e2e8f0; padding: 1px 6px; border-radius: 4px; }
.odb-value-wrap { display: flex; align-items: baseline; gap: 4px; margin-bottom: 4px; }
.odb-value { font-size: 1.4rem; font-weight: 900; color: #1e293b; line-height: 1; }
.odb-unit { font-size: 0.8rem; font-weight: 700; color: #64748b; }
.odb-ind-name { font-size: 0.72rem; color: #475569; margin: 0 0 6px; line-height: 1.25; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.odb-meta-row { margin-top: auto; font-size: 0.68rem; color: #94a3b8; font-weight: 600; }

.ods-empty-upload-box {
  text-align: center;
  padding: 16px 10px;
  color: #0369a1;
  background: #f0f9ff;
  border: 1.5px dashed #7dd3fc;
  border-radius: 10px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.ods-empty-upload-box:hover {
  background: #e0f2fe;
  border-color: #0284c7;
  transform: scale(1.02);
}
.ods-empty-upload-box i { font-size: 1.6rem; color: #0284c7; }
.ods-empty-upload-box strong { font-size: 0.8rem; color: #0369a1; }
.ods-empty-upload-box span { font-size: 0.68rem; color: #64748b; }

.ods-card-footer {
  padding: 8px 14px;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-ods-mini {
  flex: 1;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 0.74rem;
  font-weight: 700;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.15s;
}
.btn-ods-mini.view { background: #e0f2fe; color: #0369a1; }
.btn-ods-mini.view:hover { background: #bae6fd; }
.btn-ods-mini.edit { background: #fef3c7; color: #92400e; cursor: pointer; }
.btn-ods-mini.edit:hover { background: #fde68a; }
.btn-ods-mini.del { flex: 0 0 auto; background: #fee2e2; color: #dc2626; padding: 6px 10px; }
.btn-ods-mini.del:hover { background: #fecaca; }
.btn-ods-mini.upload-hint { background: #f1f5f9; color: #475569; cursor: pointer; }
.btn-ods-mini.upload-hint:hover { background: #e2e8f0; color: #1e293b; }

/* ── BARRA INFERIOR DE GUARDAR ODS ── */
.ods-bottom-save-bar {
  margin-top: 24px;
  padding: 18px 24px;
  background: #ffffff;
  border: 2px solid #86efac;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 6px 20px rgba(22, 163, 74, 0.12);
}
.obs-left strong { font-size: 0.96rem; color: #15803d; display: block; margin-bottom: 2px; }
.obs-left p { font-size: 0.78rem; color: #64748b; margin: 0; }
.btn-guardar-ods-final {
  background: #16a34a;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 12px 26px;
  font-size: 0.92rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 14px rgba(22, 163, 74, 0.35);
  transition: all 0.2s ease;
}
.btn-guardar-ods-final:hover:not(:disabled) {
  background: #15803d;
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(22, 163, 74, 0.45);
}
.btn-guardar-ods-final:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

/* ── MODAL ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-box {
  background: #ffffff;
  border-radius: 18px;
  width: 100%;
  max-width: 680px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}
.modal-hdr {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  color: #ffffff;
}
.modal-hdr h3 { margin: 0 0 4px; font-size: 1.15rem; font-weight: 800; }
.modal-hdr p { margin: 0; font-size: 0.8rem; opacity: 0.9; }
.modal-close-btn { background: transparent; border: none; font-size: 1.6rem; color: #ffffff; cursor: pointer; line-height: 1; }
.modal-content-scroll { padding: 20px 24px; overflow-y: auto; }
.m-highlight-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 14px 20px;
  border-radius: 12px;
  margin-bottom: 20px;
}
.mhb-label { font-size: 0.72rem; font-weight: 800; color: #64748b; text-transform: uppercase; }
.mhb-val { font-size: 1.8rem; font-weight: 900; color: #1e293b; }
.mhb-year { font-size: 1.4rem; font-weight: 800; color: #1b7a2b; }
.m-sec-title { font-size: 0.92rem; font-weight: 800; color: #1e293b; margin: 0 0 12px; display: flex; align-items: center; gap: 6px; }
.trend { font-size: 0.75rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; }
.trend.down { color: #16a34a; background: #dcfce7; }
.trend.up { color: #dc2626; background: #fee2e2; }
.trend.equal { color: #64748b; background: #f1f5f9; }
.trend.base { color: #0284c7; background: #e0f2fe; }
.modal-ftr { padding: 14px 24px; background: #f8fafc; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; }
.btn-sga-blue { background: #0284c7; color: #ffffff; border: none; padding: 8px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; }

@media (max-width: 900px) {
  .cap-form { grid-template-columns: 1fr; }
  .fg.wide { grid-column: span 1; }
  .cap-nav-tabs { flex-direction: column; }
}
</style>
