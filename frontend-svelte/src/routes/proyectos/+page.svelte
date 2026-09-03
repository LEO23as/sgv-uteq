<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI, fetchAPICached } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';
  import Pagination from '$lib/Pagination.svelte';
  import ProyectoDetalleModal from '$lib/ProyectoDetalleModal.svelte';
  import InstitutionalLoader from '$lib/InstitutionalLoader.svelte';

  let items       = $state([]);
  let facultades  = $state([]);
  let carreras    = $state([]);
  let periodos    = $state([]);
  let loading     = $state(true);

  // Estados de navegación jerárquica
  let vistaModo           = $state('facultades'); // 'facultades' | 'carreras' | 'tabla' | 'todos'
  let facSeleccionada     = $state(null);
  let carreraSeleccionada = $state(null);

  // Filtros de tabla
  let q         = $state('');
  let filtEst   = $state('');
  let filtPer   = $state('');

  // Modal de Detalle
  let modalProyectoId   = $state(null);
  let modalProyectoOpen = $state(false);

  // Paginación
  let page = $state(1);
  let pageSize = $state(10);

  const ESTADOS = {
    EN_EJECUCION: { label:'En ejecución', cls:'ejecucion' },
    PROPUESTO:    { label:'Propuesto',    cls:'propuesto'  },
    APROBADO:     { label:'Aprobado',     cls:'aprobado'   },
    EN_CIERRE:    { label:'En cierre',    cls:'cierre'     },
    DETENIDO:     { label:'Detenido',     cls:'detenido'   },
    FINALIZADO:   { label:'Finalizado',   cls:'finalizado' },
    RECHAZADO:    { label:'Rechazado',    cls:'rechazado'  },
  };

  const FACULTADES_CONFIG = {
    'AGRARIAS': {
      siglas: 'FCAF',
      color: '#16a34a',
      bg: '#f0fdf4',
      border: '#86efac',
      logo: '/img/facultades/fcaf.png',
      logoSvg: '/img/facultades/fcaf.svg',
      glow: 'rgba(22, 163, 74, 0.18)'
    },
    'EMPRESARIALES': {
      siglas: 'FCE',
      color: '#2563eb',
      bg: '#eff6ff',
      border: '#93c5fd',
      logo: '/img/facultades/fce.png',
      logoSvg: '/img/facultades/fce.svg',
      glow: 'rgba(37, 99, 235, 0.18)'
    },
    'PECUARIAS': {
      siglas: 'FCP',
      color: '#d97706',
      bg: '#fffbeb',
      border: '#fde68a',
      logo: '/img/facultades/fcp.png',
      logoSvg: '/img/facultades/fcp.svg',
      glow: 'rgba(217, 119, 6, 0.18)'
    },
    'SOCIALES': {
      siglas: 'FCSEF',
      color: '#7c3aed',
      bg: '#f5f3ff',
      border: '#ddd6fe',
      logo: '/img/facultades/fcseh.png',
      logoSvg: '/img/facultades/fcseh.svg',
      glow: 'rgba(124, 58, 237, 0.18)'
    },
    'FILOSOFIA': {
      siglas: 'FCSEF',
      color: '#7c3aed',
      bg: '#f5f3ff',
      border: '#ddd6fe',
      logo: '/img/facultades/fcseh.png',
      logoSvg: '/img/facultades/fcseh.svg',
      glow: 'rgba(124, 58, 237, 0.18)'
    },
    'COMPUTACION': {
      siglas: 'FCCD',
      color: '#0284c7',
      bg: '#f0f9ff',
      border: '#7dd3fc',
      logo: '/img/facultades/fccd.png',
      logoSvg: '/img/facultades/fccd.svg',
      glow: 'rgba(2, 132, 199, 0.18)'
    },
    'INGENIERIA': {
      siglas: 'FCI',
      color: '#0284c7',
      bg: '#f0f9ff',
      border: '#7dd3fc',
      logo: '/img/facultades/fci.png',
      logoSvg: '/img/facultades/fccd.svg',
      glow: 'rgba(2, 132, 199, 0.18)'
    },
    'INDUSTRIA': {
      siglas: 'FCIP',
      color: '#d97706',
      bg: '#fffbeb',
      border: '#fde68a',
      logo: '/img/facultades/fcip.png',
      logoSvg: '/img/facultades/fccd.svg',
      glow: 'rgba(217, 119, 6, 0.18)'
    },
    'PRODUCCION': {
      siglas: 'FCIP',
      color: '#d97706',
      bg: '#fffbeb',
      border: '#fde68a',
      logo: '/img/facultades/fcip.png',
      logoSvg: '/img/facultades/fccd.svg',
      glow: 'rgba(217, 119, 6, 0.18)'
    },
    'EDUCACION': {
      siglas: 'FCED',
      color: '#059669',
      bg: '#ecfdf5',
      border: '#a7f3d0',
      logo: '/img/facultades/fced.png',
      logoSvg: '/img/facultades/fced.svg',
      glow: 'rgba(5, 150, 105, 0.18)'
    },
    'SALUD': {
      siglas: 'FCS',
      color: '#e11d48',
      bg: '#fff1f2',
      border: '#fecdd3',
      logo: '/img/facultades/fcs.png',
      logoSvg: '/img/facultades/fcaf.svg',
      glow: 'rgba(225, 29, 72, 0.18)'
    },
  };

  function getFacConfig(nombre) {
    const n = (nombre || '')
      .toUpperCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
    for (const [k, cfg] of Object.entries(FACULTADES_CONFIG)) {
      if (n.includes(k)) return cfg;
    }
    return {
      siglas: 'UTEQ',
      color: '#16a34a',
      bg: '#f0fdf4',
      border: '#86efac',
      logo: '/img/facultades/fcaf.png',
      logoSvg: '/img/facultades/fcaf.svg',
      glow: 'rgba(22, 163, 74, 0.15)'
    };
  }

  function parsearFecha(f) {
    if (!f) return null;
    if (typeof f !== 'string') return new Date(f);
    if (/^\d{4}-\d{2}-\d{2}/.test(f)) {
      const [y, m, d] = f.split('T')[0].split('-').map(Number);
      return new Date(y, m - 1, d);
    }
    if (/^\d{1,2}\/\d{1,2}\/\d{4}/.test(f)) {
      const [d, m, y] = f.split('/').map(Number);
      return new Date(y, m - 1, d);
    }
    const dt = new Date(f);
    return isNaN(dt.getTime()) ? null : dt;
  }

  function formatFechaLocal(f) {
    const dt = parsearFecha(f);
    if (!dt) return '—';
    return dt.toLocaleDateString('es-EC', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function calcularAvance(fechaInicio, fechaFin, estado) {
    if (estado === 'FINALIZADO') return { pct: 100, label: '100% Finalizado', sub: 'Culminado', variant: 'success' };
    
    const ini = parsearFecha(fechaInicio);
    const fin = parsearFecha(fechaFin);
    
    if (!ini || !fin) return { pct: 0, label: '0%', sub: 'Sin fechas', variant: 'info' };
    
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const iniN = new Date(ini); iniN.setHours(0, 0, 0, 0);
    const finN = new Date(fin); finN.setHours(0, 0, 0, 0);
    
    const totalMs = finN.getTime() - iniN.getTime();
    if (totalMs <= 0) return { pct: 100, label: '100%', sub: 'Plazo culminado', variant: 'warning' };
    
    const restDias = Math.ceil((finN.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    const transcurrido = hoy.getTime() - iniN.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurrido / totalMs) * 100)));
    
    if (restDias < 0) return { pct: 100, label: '100%', sub: `Venció ${formatFechaLocal(fin)}`, variant: 'danger' };
    if (transcurrido < 0) return { pct: 0, label: '0%', sub: `Inicia ${formatFechaLocal(ini)}`, variant: 'info' };
    return { pct, label: `${pct}% avance`, sub: `${restDias}d restantes`, variant: 'auto' };
  }

  onMount(async () => {
    try {
      // PROYECTOS: Siempre datos vivos y frescos del servidor
      // CATÁLOGOS: Con caché inteligente en sesión para acelerar la vista a 0 ms
      const [proysRes, facsRes, carrsRes, persRes] = await Promise.all([
        fetchAPI('/api/proyectos/'),
        fetchAPICached('/api/facultades/'),
        fetchAPICached('/api/carreras/'),
        fetchAPICached('/api/periodos/'),
      ]);
      items = proysRes || [];
      facultades = facsRes || [];
      carreras = carrsRes || [];
      periodos = persRes || [];
    } finally { loading = false; }
  });

  // Estadísticas y Conteo por Facultades
  let statsFacultades = $derived.by(() => {
    return facultades.map(fac => {
      const proysFac = items.filter(p => {
        return (p.id_facultad && String(p.id_facultad) === String(fac.id_facultad)) ||
               (p.facultad_nombre && p.facultad_nombre.toLowerCase() === fac.nombre.toLowerCase());
      });
      const enEjec = proysFac.filter(p => p.estado === 'EN_EJECUCION').length;
      const finalizados = proysFac.filter(p => p.estado === 'FINALIZADO').length;
      const carrsFac = carreras.filter(c => String(c.id_facultad) === String(fac.id_facultad));

      return {
        ...fac,
        totalProyectos: proysFac.length,
        enEjecucion: enEjec,
        finalizados,
        totalCarreras: carrsFac.length || 1,
      };
    });
  });

  // Carreras de la Facultad Seleccionada con sus conteos
  let carrerasDeFacultad = $derived.by(() => {
    if (!facSeleccionada) return [];
    const carrs = carreras.filter(c => String(c.id_facultad) === String(facSeleccionada.id_facultad));
    
    return carrs.map(c => {
      const proysCar = items.filter(p => {
        const matchFac = (p.id_facultad && String(p.id_facultad) === String(facSeleccionada.id_facultad)) ||
                         (p.facultad_nombre && p.facultad_nombre.toLowerCase() === facSeleccionada.nombre.toLowerCase());
        const matchCar = (p.id_carrera && String(p.id_carrera) === String(c.id_carrera)) ||
                         (p.carrera_nombre && p.carrera_nombre.toLowerCase() === c.nombre.toLowerCase());
        return matchFac && matchCar;
      });

      return {
        ...c,
        totalProyectos: proysCar.length,
        enEjecucion: proysCar.filter(p => p.estado === 'EN_EJECUCION').length,
      };
    });
  });

  // Filtrado de Proyectos en Tabla
  let filtered = $derived(items.filter(p => {
    // Si estamos en modo de navegación jerárquica
    if (vistaModo === 'tabla') {
      if (facSeleccionada) {
        const matchFac = (p.id_facultad && String(p.id_facultad) === String(facSeleccionada.id_facultad)) ||
                         (p.facultad_nombre && p.facultad_nombre.toLowerCase() === facSeleccionada.nombre.toLowerCase());
        if (!matchFac) return false;
      }
      if (carreraSeleccionada) {
        const matchCar = (p.id_carrera && String(p.id_carrera) === String(carreraSeleccionada.id_carrera)) ||
                         (p.carrera_nombre && p.carrera_nombre.toLowerCase() === carreraSeleccionada.nombre.toLowerCase());
        if (!matchCar) return false;
      }
    }

    const matchQ = !q ||
      p.nombre.toLowerCase().includes(q.toLowerCase()) ||
      (p.nombre_corto && p.nombre_corto.toLowerCase().includes(q.toLowerCase())) ||
      p.codigo.toLowerCase().includes(q.toLowerCase());
    
    const matchE = !filtEst || p.estado === filtEst;
    const matchP = !filtPer || String(p.id_periodo_inicio) === String(filtPer);

    return matchQ && matchE && matchP;
  }));

  const paginatedProjects = $derived(
    filtered.slice((page - 1) * pageSize, page * pageSize)
  );

  // Navegación
  function seleccionarFacultad(fac) {
    facSeleccionada = fac;
    carreraSeleccionada = null;
    vistaModo = 'carreras';
    page = 1;
  }

  function seleccionarCarrera(carr) {
    carreraSeleccionada = carr;
    vistaModo = 'tabla';
    page = 1;
  }

  function verTodosFacultad() {
    carreraSeleccionada = null;
    vistaModo = 'tabla';
    page = 1;
  }

  function irAFacultades() {
    facSeleccionada = null;
    carreraSeleccionada = null;
    vistaModo = 'facultades';
    page = 1;
  }

  function irATodos() {
    facSeleccionada = null;
    carreraSeleccionada = null;
    vistaModo = 'todos';
    page = 1;
  }

  function onSearchInput() {
    page = 1;
    if (q.trim().length > 0 && (vistaModo === 'facultades' || vistaModo === 'carreras')) {
      vistaModo = 'todos';
    }
  }

  function limpiar() {
    q = '';
    filtEst = '';
    filtPer = '';
    page = 1;
  }

  function abrirDetalle(id) {
    modalProyectoId = id;
    modalProyectoOpen = true;
  }

  async function eliminarProyecto(p) {
    const nombre = p.nombre_corto || p.nombre;
    const confirmed = await confirmDialog({
      title: '¿Eliminar proyecto de vinculación?',
      message: `Se eliminará "${nombre}" (${p.codigo}). Se borrarán también sus ubicaciones, convenios vinculados y evidencias. Esta acción no se puede deshacer.`,
      confirmText: 'Sí, eliminar proyecto',
      type: 'danger'
    });

    if (!confirmed) return;

    try {
      const res = await fetch(`/api/proyectos/${p.id_proyecto}/eliminar/`, {
        method: 'DELETE', credentials: 'include',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        toast.error(data.error || 'No se pudo eliminar el proyecto');
      } else {
        items = items.filter(x => x.id_proyecto !== p.id_proyecto);
        toast.success(`Proyecto "${nombre}" eliminado correctamente`);
      }
    } catch {
      toast.error('Error de conexión al eliminar');
    }
  }
</script>

<svelte:head><title>Proyectos de Vinculación — SGV UTEQ</title></svelte:head>

<!-- SUBBAR SUPERIOR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <button type="button" class="btn-crumb" onclick={irAFacultades}>Proyectos</button>
    {#if facSeleccionada}
      <span class="sep">/</span>
      <button type="button" class="btn-crumb" onclick={() => { carreraSeleccionada = null; vistaModo = 'carreras'; }}>
        {facSeleccionada.nombre_corto || facSeleccionada.nombre}
      </button>
    {/if}
    {#if carreraSeleccionada}
      <span class="sep">/</span>
      <span class="current">{carreraSeleccionada.nombre_corto || carreraSeleccionada.nombre}</span>
    {:else if vistaModo === 'todos'}
      <span class="sep">/</span>
      <span class="current">Todos los proyectos</span>
    {/if}
  </nav>

  <!-- BOTÓN NUEVO PROYECTO (Con preselección de Facultad/Carrera si está en drill-down) -->
  <a
    href="/proyectos/nuevo{facSeleccionada ? `?facultad=${facSeleccionada.id_facultad}${carreraSeleccionada ? `&carrera=${carreraSeleccionada.id_carrera}` : ''}` : ''}"
    class="btn-nuevo"
  >
    <i class="bi bi-plus-lg"></i> Nuevo proyecto
  </a>
</div>

<div class="page-wrap">
  
  <!-- CABECERA PRINCIPAL Y TOGGLES DE VISTA -->
  <div class="page-top-header">
    <div>
      <h2 class="page-title"><i class="bi bi-folder2-open"></i> Proyectos de Vinculación</h2>
      <p class="page-sub">Organización institucional por Facultades, Carreras y avance temporal</p>
    </div>

    <div class="view-toggles">
      <button
        type="button"
        class="toggle-btn"
        class:active={vistaModo === 'facultades' || vistaModo === 'carreras' || (vistaModo === 'tabla' && facSeleccionada)}
        onclick={irAFacultades}
      >
        <i class="bi bi-diagram-3-fill"></i> Por Facultades y Carreras
      </button>
      <button
        type="button"
        class="toggle-btn"
        class:active={vistaModo === 'todos'}
        onclick={irATodos}
      >
        <i class="bi bi-table"></i> Lista General ({items.length})
      </button>
    </div>
  </div>

  {#if loading}
    <InstitutionalLoader fullscreen={true} texto="CARGANDO PROYECTOS" subtexto="Consultando proyectos institucionales UTEQ..." />
  {:else}

    <!-- ══════════════════════════════════════════════════════════════
         NIVEL 1: TARJETAS DE FACULTADES
    ═══════════════════════════════════════════════════════════════ -->
    {#if vistaModo === 'facultades'}
      <div class="section-intro">
        <div class="si-text">
          <span class="si-badge">Estructura Académica</span>
          <h3>Selecciona una Facultad para explorar sus carreras y proyectos</h3>
        </div>
        <div class="si-search">
          <div class="search-wrap compact">
            <i class="bi bi-search"></i>
            <input bind:value={q} placeholder="O buscar proyecto directamente…" oninput={onSearchInput} />
          </div>
        </div>
      </div>

      <div class="facultades-grid">
        {#each statsFacultades as fac}
          {@const cfg = getFacConfig(fac.nombre)}
          <div 
            class="fac-card" 
            style="--fac-color: {cfg.color}; --fac-bg: {cfg.bg}; --fac-border: {cfg.border}; --fac-glow: {cfg.glow};"
            onclick={() => seleccionarFacultad(fac)}
          >
            <!-- Acento de color superior -->
            <div class="fc-top-accent" style="background: {cfg.color};"></div>

            <div class="fc-head">
              <div class="fc-logo-wrap" style="background: {cfg.bg}; border-color: {cfg.border};">
                <img 
                  src={cfg.logo} 
                  alt="Logo {cfg.siglas}" 
                  class="fc-logo-img" 
                  width="48"
                  height="48"
                  style="width: 48px; height: 48px; max-width: 48px; max-height: 48px; object-fit: contain;"
                  onerror={(e) => {
                    if (!e.currentTarget.dataset.fallback) {
                      e.currentTarget.dataset.fallback = '1';
                      e.currentTarget.src = cfg.logoSvg;
                    }
                  }}
                />
              </div>
              <div class="fc-badges">
                <span class="fc-badge-siglas" style="color: {cfg.color}; background: {cfg.bg}; border-color: {cfg.border};">{cfg.siglas}</span>
                <span class="fc-badge-carrs">{fac.totalCarreras} {fac.totalCarreras === 1 ? 'Carrera' : 'Carreras'}</span>
              </div>
            </div>
            
            <h4 class="fc-title">{fac.nombre}</h4>
            
            <div class="fc-stats">
              <div class="fcs-item">
                <span class="fcs-val" style="color: {cfg.color};">{fac.totalProyectos}</span>
                <span class="fcs-lbl">Proyectos</span>
              </div>
              <div class="fcs-sep"></div>
              <div class="fcs-item">
                <span class="fcs-val text-blue">{fac.enEjecucion}</span>
                <span class="fcs-lbl">En ejecución</span>
              </div>
              <div class="fcs-sep"></div>
              <div class="fcs-item">
                <span class="fcs-val text-gray">{fac.finalizados}</span>
                <span class="fcs-lbl">Finalizados</span>
              </div>
            </div>

            <div class="fc-footer" style="color: {cfg.color};">
              <span>Explorar carreras y proyectos</span>
              <i class="bi bi-arrow-right"></i>
            </div>
          </div>
        {/each}
      </div>

    <!-- ══════════════════════════════════════════════════════════════
         NIVEL 2: TARJETAS DE CARRERAS DE LA FACULTAD SELECCIONADA
    ═══════════════════════════════════════════════════════════════ -->
    {:else if vistaModo === 'carreras' && facSeleccionada}
      {@const facCfg = getFacConfig(facSeleccionada.nombre)}
      <div class="fac-banner" style="border-color: {facCfg.border};">
        <button class="btn-volver" onclick={irAFacultades} title="Volver a todas las facultades">
          <i class="bi bi-arrow-left"></i>
        </button>
        <div class="fb-logo-wrap" style="background: {facCfg.bg}; border-color: {facCfg.border};">
          <img 
            src={facCfg.logo} 
            alt="Logo {facCfg.siglas}" 
            class="fb-logo-img" 
            width="48"
            height="48"
            style="width: 48px; height: 48px; max-width: 48px; max-height: 48px; object-fit: contain;"
            onerror={(e) => {
              if (!e.currentTarget.dataset.fallback) {
                e.currentTarget.dataset.fallback = '1';
                e.currentTarget.src = facCfg.logoSvg;
              }
            }}
          />
        </div>
        <div class="fb-info">
          <span class="fb-pre" style="color: {facCfg.color};">{facCfg.siglas} • Facultad</span>
          <h3>{facSeleccionada.nombre}</h3>
          <span class="fb-sub">{carrerasDeFacultad.length} Carreras académicas registradas</span>
        </div>
        <button class="btn-ver-todos-fac" onclick={verTodosFacultad} style="background: {facCfg.bg}; border-color: {facCfg.border}; color: {facCfg.color};">
          <i class="bi bi-eye-fill"></i> Ver todos los proyectos de la facultad
        </button>
      </div>

      {#if facSeleccionada.totalProyectos === 0 || facSeleccionada.codigo === 'FCC' || facSeleccionada.nombre?.includes('Computación')}
        <div class="fcc-transicion-banner">
          <div class="fcc-tb-icon"><i class="bi bi-info-circle-fill"></i></div>
          <div class="fcc-tb-content">
            <strong>Facultad de reciente creación institucional (Estatuto Orgánico UTEQ)</strong>
            <p>
              Esta facultad no cuenta con proyectos asignados en este ciclo académico. Los proyectos históricos de vinculación de las carreras de Software, Sistemas y Telemática se encuentran registrados y amparados bajo la <strong>Facultad de Ciencias de la Ingeniería (FCI)</strong>. Su cohorte de proyectos propios se encuentra en proceso de formulación.
            </p>
          </div>
        </div>
      {/if}

      <div class="section-sub-header">
        <h4><i class="bi bi-mortarboard-fill" style="color: {facCfg.color};"></i> Selecciona una Carrera:</h4>
      </div>

      <div class="carreras-grid">
        {#each carrerasDeFacultad as car}
          <div 
            class="carr-card" 
            style="--fac-color: {facCfg.color}; --fac-bg: {facCfg.bg}; --fac-border: {facCfg.border}; --fac-glow: {facCfg.glow};"
            onclick={() => seleccionarCarrera(car)}
          >
            <div class="cc-top">
              <div class="cc-icon" style="background: {facCfg.bg}; color: {facCfg.color}; border: 1px solid {facCfg.border};">
                <i class="bi bi-mortarboard-fill"></i>
              </div>
              <span class="cc-badge" style="color: {facCfg.color}; background: {facCfg.bg}; border-color: {facCfg.border};">
                {car.totalProyectos} {car.totalProyectos === 1 ? 'proyecto' : 'proyectos'}
              </span>
            </div>

            <h4 class="cc-title">{car.nombre}</h4>

            <div class="cc-footer" style="color: {facCfg.color};">
              <span>Ver proyectos de esta carrera</span>
              <i class="bi bi-chevron-right"></i>
            </div>
          </div>
        {/each}

        {#if carrerasDeFacultad.length === 0}
          <div class="empty-box col-full">
            <i class="bi bi-info-circle"></i>
            <span>No se encontraron carreras registradas para esta facultad.</span>
            <button class="btn-ver-todos-fac" onclick={verTodosFacultad}>Ver proyectos de la facultad</button>
          </div>
        {/if}
      </div>

    <!-- ══════════════════════════════════════════════════════════════
         NIVEL 3: TABLA DE PROYECTOS (FILTRADA O LISTA GLOBAL)
    ═══════════════════════════════════════════════════════════════ -->
    {:else}
      
      {#if facSeleccionada}
        <!-- ENCABEZADO DE CONTEXTO FACULTAD / CARRERA -->
        <div class="context-bar">
          <div class="cb-crumbs">
            <button type="button" class="cb-link" onclick={irAFacultades}><i class="bi bi-building"></i> Facultades</button>
            <i class="bi bi-chevron-right sep-ic"></i>
            <button type="button" class="cb-link" onclick={() => { carreraSeleccionada = null; vistaModo = 'carreras'; }}>
              {facSeleccionada.nombre_corto || facSeleccionada.nombre}
            </button>
            {#if carreraSeleccionada}
              <i class="bi bi-chevron-right sep-ic"></i>
              <span class="cb-current"><i class="bi bi-book"></i> {carreraSeleccionada.nombre}</span>
            {/if}
          </div>

          <div class="cb-actions">
            {#if carreraSeleccionada}
              <button class="btn-soft" onclick={() => { carreraSeleccionada = null; }}>
                <i class="bi bi-filter-circle"></i> Ver toda la facultad
              </button>
            {/if}
          </div>
        </div>
      {/if}

      <!-- FILTROS DE TABLA -->
      <div class="filtros-row">
        <div class="search-wrap">
          <i class="bi bi-search"></i>
          <input bind:value={q} placeholder="Buscar por nombre o código…" oninput={() => page = 1} />
        </div>

        <select bind:value={filtPer} onchange={() => page = 1}>
          <option value="">Todos los períodos</option>
          {#each periodos as p}
            <option value={p.id_periodo}>{p.nombre || p.codigo}</option>
          {/each}
        </select>

        <select bind:value={filtEst} onchange={() => page = 1}>
          <option value="">Todos los estados</option>
          {#each Object.entries(ESTADOS) as [val, info]}
            <option value={val}>{info.label}</option>
          {/each}
        </select>

        <button class="btn-limpiar" onclick={limpiar}><i class="bi bi-arrow-counterclockwise"></i> Limpiar</button>
        
        <span class="conteo-badge">
          <i class="bi bi-list-check"></i> {filtered.length} {filtered.length === 1 ? 'proyecto' : 'proyectos'}
        </span>
      </div>

      <!-- TABLA PRINCIPAL DE PROYECTOS -->
      <div class="table-card">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre del Proyecto</th>
              <th>Facultad / Carrera</th>
              <th>Período</th>
              <th style="min-width: 170px;">Avance Temporal</th>
              <th>Estado</th>
              <th style="text-align: center;">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each paginatedProjects as p}
              {@const av = calcularAvance(p.fecha_inicio, p.fecha_fin_planificada || p.fecha_fin_real, p.estado)}
              <tr>
                <td><span class="code">{p.codigo}</span></td>
                <td class="nombre-cell">
                  <span class="nombre-principal">{p.nombre_corto || p.nombre}</span>
                  {#if p.nombre_corto}
                    <span class="nombre-sec">{p.nombre}</span>
                  {/if}
                </td>
                <td>
                  <span class="fac-badge">{p.facultad_nombre}</span>
                  <span class="carrera-sec">{p.carrera_nombre}</span>
                </td>
                <td class="txt-small">{p.periodo_inicio_nombre || '—'}</td>
                <td>
                  <div class="avance-col">
                    <ProgressBar
                      value={av.pct}
                      max={100}
                      label={av.label}
                      sublabel={av.sub}
                      variant={av.variant}
                      size="sm"
                    />
                  </div>
                </td>
                <td>
                  <span class="badge est-{(ESTADOS[p.estado]?.cls) || 'finalizado'}">
                    {ESTADOS[p.estado]?.label || p.estado}
                  </span>
                </td>
                <td>
                  <div class="acciones center">
                    <button type="button" class="btn-accion" title="Ver detalle del proyecto" onclick={() => abrirDetalle(p.id_proyecto)}>
                      <i class="bi bi-eye"></i>
                    </button>
                    <a href="/proyectos/{p.id_proyecto}/editar" class="btn-accion editar" title="Editar proyecto">
                      <i class="bi bi-pencil"></i>
                    </a>
                    <button class="btn-accion eliminar" title="Eliminar proyecto" onclick={() => eliminarProyecto(p)}>
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            {/each}

            {#if filtered.length === 0}
              <tr>
                <td colspan="7" class="empty">
                  {#if facSeleccionada && (facSeleccionada.totalProyectos === 0 || facSeleccionada.codigo === 'FCC' || facSeleccionada.nombre?.includes('Computación'))}
                    <div class="fcc-transicion-banner" style="margin: 20px auto; max-width: 800px; text-align: left;">
                      <div class="fcc-tb-icon"><i class="bi bi-info-circle-fill"></i></div>
                      <div class="fcc-tb-content">
                        <strong>Facultad de reciente creación institucional (Estatuto Orgánico UTEQ)</strong>
                        <p>
                          Esta facultad no cuenta con proyectos asignados en este ciclo académico. Los proyectos históricos de vinculación de las carreras de Software, Sistemas y Telemática se encuentran registrados y amparados bajo la <strong>Facultad de Ciencias de la Ingeniería (FCI)</strong>. Su cohorte de proyectos propios se encuentra en proceso de formulación.
                        </p>
                      </div>
                    </div>
                  {:else}
                    <i class="bi bi-folder-x" style="font-size: 2rem; color: #cbd5e1; display: block; margin-bottom: 6px;"></i>
                    No se encontraron proyectos con los filtros seleccionados
                  {/if}
                </td>
              </tr>
            {/if}
          </tbody>
        </table>

        {#if filtered.length > 0}
          <Pagination totalItems={filtered.length} bind:page bind:pageSize itemLabel="proyectos" />
        {/if}
      </div>

    {/if}
  {/if}
</div>

<!-- MODAL DE DETALLE DEL PROYECTO -->
<ProyectoDetalleModal
  idProyecto={modalProyectoId}
  isOpen={modalProyectoOpen}
  onClose={() => modalProyectoOpen = false}
/>

<style>
  .subbar { display:flex;align-items:center;justify-content:space-between;padding:10px 24px;background:#fff;border-bottom:1px solid #e2e8f0; }
  .btn-crumb { background: none; border: none; font-size: inherit; font-weight: 700; color: #15803d; cursor: pointer; padding: 0; }
  .btn-crumb:hover { text-decoration: underline; }

  .btn-nuevo { display:inline-flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:8px 16px;border-radius:9px;font-weight:700;font-size:.85rem;text-decoration:none;transition:background .15s ease; }
  .btn-nuevo:hover { background:#145c04; }

  /* CABECERA Y TOGGLES */
  .page-top-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; margin-bottom: 20px; }
  .view-toggles { display: flex; gap: 6px; background: #f1f5f9; padding: 4px; border-radius: 10px; border: 1px solid #e2e8f0; }
  .toggle-btn {
    background: transparent; border: none; border-radius: 7px;
    padding: 7px 14px; font-size: 0.82rem; font-weight: 700; color: #64748b;
    cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
    transition: all 0.15s ease;
  }
  .toggle-btn:hover { color: #1e293b; }
  .toggle-btn.active { background: #ffffff; color: #15803d; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }

  /* INTRO SECCIÓN */
  .section-intro {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px 22px; margin-bottom: 20px;
  }
  .si-badge { font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #15803d; background: #dcfce7; padding: 3px 8px; border-radius: 6px; }
  .si-text h3 { font-size: 1.05rem; font-weight: 800; color: #0f172a; margin: 4px 0 0; }
  .search-wrap.compact { min-width: 280px; }

  /* CUADRÍCULA DE FACULTADES */
  .facultades-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin-bottom: 24px;
  }
  .fac-card {
    position: relative;
    overflow: hidden;
    background: #ffffff;
    border: 1.5px solid var(--fac-border, #e2e8f0);
    border-radius: 16px;
    padding: 22px 20px 18px 20px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 14px;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
  }
  .fac-card:hover {
    border-color: var(--fac-color, #16a34a);
    transform: translateY(-5px);
    box-shadow: 0 14px 28px var(--fac-glow, rgba(22, 163, 74, 0.14));
  }

  .fc-top-accent {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--fac-color, #16a34a);
  }

  .fc-head { display: flex; align-items: center; justify-content: space-between; }
  
  .fc-logo-wrap {
    width: 52px;
    height: 52px;
    min-width: 52px;
    max-width: 52px;
    max-height: 52px;
    border-radius: 14px;
    background: var(--fac-bg, #f0fdf4);
    border: 1.5px solid var(--fac-border, #bbf7d0);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease;
    overflow: hidden;
    flex-shrink: 0;
  }
  .fac-card:hover .fc-logo-wrap {
    transform: scale(1.06);
  }
  .fc-logo-img {
    width: 100%;
    height: 100%;
    max-width: 46px;
    max-height: 46px;
    object-fit: contain;
    border-radius: 10px;
  }

  .fc-badges {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .fc-badge-siglas {
    font-size: 0.72rem;
    font-weight: 900;
    padding: 4px 9px;
    border-radius: 8px;
    border: 1px solid var(--fac-border, #e2e8f0);
    background: var(--fac-bg, #f8fafc);
    letter-spacing: 0.04em;
  }

  .fc-badge-carrs {
    font-size: 0.72rem;
    font-weight: 700;
    color: #475569;
    background: #f1f5f9;
    padding: 4px 10px;
    border-radius: 20px;
  }

  .fc-title {
    font-size: 0.98rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.35;
    margin: 0;
    min-height: 44px;
    transition: color 0.15s ease;
  }
  .fac-card:hover .fc-title {
    color: var(--fac-color, #0f172a);
  }
  
  .fc-stats {
    display: flex;
    align-items: center;
    justify-content: space-around;
    background: #f8fafc;
    border: 1px solid #f1f5f9;
    border-radius: 12px;
    padding: 10px 8px;
  }
  .fcs-item { display: flex; flex-direction: column; align-items: center; }
  .fcs-val { font-size: 1.15rem; font-weight: 900; }
  .fcs-lbl { font-size: 0.68rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.02em; }
  .fcs-sep { width: 1px; height: 24px; background: #e2e8f0; }

  .fc-footer {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 0.78rem; font-weight: 800; color: #15803d; padding-top: 4px; border-top: 1px solid #f1f5f9;
  }

  /* BANNER FACULTAD EN NIVEL 2 */
  .fac-banner {
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    background: #ffffff; border: 1.5px solid #86efac; border-radius: 14px; padding: 18px 22px; margin-bottom: 20px;
  }
  .btn-volver {
    background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; width: 40px; height: 40px;
    display: flex; align-items: center; justify-content: center; font-size: 1.1rem; color: #334155; cursor: pointer;
    transition: all 0.15s;
  }
  .btn-volver:hover { background: #e2e8f0; color: #0f172a; }
  .fb-logo-wrap {
    width: 56px;
    height: 56px;
    min-width: 56px;
    max-width: 56px;
    max-height: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border: 1.5px solid #86efac;
    overflow: hidden;
    flex-shrink: 0;
  }
  .fb-logo-img {
    width: 100%;
    height: 100%;
    max-width: 48px;
    max-height: 48px;
    object-fit: contain;
    border-radius: 10px;
  }
  .fb-info { flex: 1; min-width: 200px; }
  .fb-pre { font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #15803d; letter-spacing: 0.05em; }
  .fb-info h3 { font-size: 1.2rem; font-weight: 900; color: #0f172a; margin: 2px 0 3px; }
  .fb-sub { font-size: 0.78rem; font-weight: 600; color: #64748b; }
  
  .btn-ver-todos-fac {
    background: #f0fdf4; color: #15803d; border: 1.5px solid #86efac; border-radius: 9px;
    padding: 9px 16px; font-size: 0.82rem; font-weight: 800; cursor: pointer;
    display: inline-flex; align-items: center; gap: 8px; transition: all 0.15s;
  }
  .btn-ver-todos-fac:hover { background: #15803d; color: #ffffff; }

  .section-sub-header { margin-bottom: 14px; }
  .section-sub-header h4 { font-size: 0.95rem; font-weight: 800; color: #334155; display: flex; align-items: center; gap: 8px; margin: 0; }

  /* CUADRÍCULA DE CARRERAS */
  .carreras-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px;
  }
  .carr-card {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 18px 16px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02);
  }
  .carr-card:hover {
    border-color: var(--fac-color, #15803d);
    transform: translateY(-3px);
    box-shadow: 0 10px 22px var(--fac-glow, rgba(21, 128, 61, 0.1));
  }
  .cc-top { display: flex; align-items: center; justify-content: space-between; }
  .cc-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3px;
    overflow: hidden;
    flex-shrink: 0;
  }
  .cc-badge {
    font-size: 0.72rem;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
  }
  .cc-title {
    font-size: 0.94rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.35;
    margin: 0;
    min-height: 40px;
    transition: color 0.15s ease;
  }
  .carr-card:hover .cc-title {
    color: var(--fac-color, #0f172a);
  }
  .cc-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.76rem;
    font-weight: 800;
    padding-top: 8px;
    border-top: 1px solid #f8fafc;
    transition: transform 0.2s ease;
  }
  .carr-card:hover .cc-footer i {
    transform: translateX(4px);
  }
  .cc-footer i {
    transition: transform 0.2s ease;
  }

  /* BARRA DE CONTEXTO EN TABLA */
  .context-bar {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 16px; margin-bottom: 14px;
  }
  .cb-crumbs { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 0.82rem; font-weight: 700; }
  .cb-link { background: none; border: none; color: #15803d; cursor: pointer; padding: 0; font-weight: 800; display: inline-flex; align-items: center; gap: 4px; }
  .cb-link:hover { text-decoration: underline; }
  .sep-ic { font-size: 0.65rem; color: #94a3b8; }
  .cb-current { color: #0f172a; font-weight: 800; display: inline-flex; align-items: center; gap: 4px; }
  .btn-soft {
    background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px;
    font-size: 0.74rem; font-weight: 700; color: #475569; cursor: pointer; display: inline-flex; align-items: center; gap: 5px;
  }
  .btn-soft:hover { background: #f1f5f9; color: #1e293b; }

  /* TABLA Y FILTROS */
  .filtros-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
  .filtros-row select { border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 8px 12px; font-size: .84rem; background: #fff; color: #334155; }
  .btn-limpiar { background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; border-radius: 9px; padding: 8px 16px; font-weight: 600; font-size: .84rem; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
  .btn-limpiar:hover { background: #e2e8f0; }
  .conteo-badge { margin-left: auto; font-size: 0.8rem; font-weight: 800; color: #475569; background: #f1f5f9; padding: 6px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px; }

  .nombre-cell { max-width: 260px; }
  .nombre-principal { display:block;font-weight:700;color:#1e293b; }
  .nombre-sec { display:block;font-size:.72rem;color:#64748b;margin-top:2px; }
  .fac-badge { display:inline-block;background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:6px;width:fit-content; }
  .carrera-sec { display:block;font-size:.72rem;color:#64748b;margin-top:3px; }
  .txt-small { font-size:.78rem; color:#475569; }
  .center { text-align:center; justify-content:center; }
  .acciones { display:flex;gap:6px;align-items:center; }
  .avance-col { width: 100%; min-width: 150px; }

  .empty-box {
    grid-column: 1 / -1; background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 12px;
    padding: 30px; display: flex; flex-direction: column; align-items: center; gap: 10px; color: #64748b; font-weight: 600;
  }
  .empty-box i { font-size: 2rem; color: #94a3b8; }

  .text-verde { color: #16a34a; }
  .text-blue  { color: #0284c7; }
  .text-gray  { color: #64748b; }

  .fcc-transicion-banner {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-left: 5px solid #0284c7;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    box-shadow: 0 2px 8px rgba(2, 132, 199, 0.06);
  }
  .fcc-tb-icon { font-size: 1.4rem; color: #0284c7; flex-shrink: 0; line-height: 1; margin-top: 2px; }
  .fcc-tb-content strong { color: #0369a1; font-size: 0.94rem; display: block; margin-bottom: 4px; }
  .fcc-tb-content p { color: #334155; font-size: 0.86rem; line-height: 1.5; margin: 0; }
</style>
