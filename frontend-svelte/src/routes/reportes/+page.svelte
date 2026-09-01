<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI, fetchAPICached } from '$lib/stores';
  import Pagination from '$lib/Pagination.svelte';
  import ProyectoDetalleModal from '$lib/ProyectoDetalleModal.svelte';

  let stats = $state(null);
  let periodos = $state([]);
  let periodoFiltro = $state('');
  let loading = $state(true);
  let ChartModule = $state(null);
  let activeTab = $state('estadisticas'); // 'estadisticas' | 'riesgo' | 'proyectos' | 'convenios'

  // Modales
  let modalProyectoId = $state(null);
  let modalProyectoOpen = $state(false);

  let modalRiesgoOpen = $state(false);
  let modalRiesgoTipo = $state('alto'); // 'bajo' | 'medio' | 'alto'

  // Modal de Configuración de Impresión (Template Method)
  let modalPrintOpen = $state(false);
  let printOptKpis = $state(true);
  let printOptRiesgo = $state(true);
  let printOptStats = $state(true);
  let printOptFacultades = $state(true);
  let printOptProvincias = $state(true);
  let printOptProyectos = $state(true);
  let printOptConvenios = $state(false);
  let isPrintingView = $state(false);

  // Paginación de proyectos en reportes
  let pageProy = $state(1);
  let pageSizeProy = $state(8);

  const ESTADO_COLORES = {
    EN_EJECUCION: '#1b7505',
    PROPUESTO: '#dba112',
    APROBADO: '#0284c7',
    EN_CIERRE: '#ea580c',
    DETENIDO: '#dc2626',
    FINALIZADO: '#64748b',
    RECHAZADO: '#94a3b8',
  };
  const ESTADO_LABEL = {
    EN_EJECUCION: 'En ejecución',
    PROPUESTO: 'Propuesto',
    APROBADO: 'Aprobado',
    EN_CIERRE: 'En cierre',
    DETENIDO: 'Detenido',
    FINALIZADO: 'Finalizado',
    RECHAZADO: 'Rechazado',
  };
  const CONV_COLORES = {
    VIGENTE: '#1b7505',
    VENCIDO: '#dc2626',
    RENOVADO: '#0284c7',
    CANCELADO: '#64748b',
  };
  const PALETTE = [
    '#1b7505', '#2db80a', '#0284c7', '#dba112', '#9333ea',
    '#ea580c', '#0891b2', '#059669', '#ca8a04', '#e11d48'
  ];

  const commonTooltip = {
    backgroundColor: 'rgba(13, 25, 16, 0.94)',
    padding: 10,
    cornerRadius: 8,
    titleFont: { weight: '800', size: 12 },
    bodyFont: { weight: '600', size: 12 },
  };

  onMount(async () => {
    try {
      const { Chart, registerables } = await import('chart.js');
      Chart.register(...registerables);
      Chart.defaults.font.family = "'Nunito', sans-serif";
      Chart.defaults.font.weight = '600';
      Chart.defaults.color = '#475569';
      ChartModule = Chart;
    } catch (e) {
      console.error('Error cargando Chart.js', e);
    }

    try {
      periodos = await fetchAPICached('/api/periodos/');
    } catch {}

    await cargarEstadisticas();
  });

  async function cargarEstadisticas() {
    loading = true;
    try {
      const url = periodoFiltro ? `/api/reportes/stats/?periodo=${periodoFiltro}` : '/api/reportes/stats/';
      stats = await fetchAPI(url);
    } catch {
      stats = null;
    } finally {
      loading = false;
    }
  }

  function chartAction(node, config) {
    if (!ChartModule || !config) return;
    let chart = new ChartModule(node, config);
    return {
      update(newConfig) {
        if (chart && newConfig) {
          chart.data = newConfig.data;
          chart.options = newConfig.options;
          chart.update();
        }
      },
      destroy() {
        if (chart) chart.destroy();
      }
    };
  }

  function abrirModalRiesgo(tipo) {
    modalRiesgoTipo = tipo;
    modalRiesgoOpen = true;
  }

  function abrirDetalleProyecto(id) {
    modalProyectoId = id;
    modalProyectoOpen = true;
  }

  function irAEditarProyecto(id) {
    modalRiesgoOpen = false;
    goto(`/proyectos/${id}/editar`);
  }

  function ejecutarImpresionConfigurada() {
    modalPrintOpen = false;
    isPrintingView = true;
    setTimeout(() => {
      window.print();
      isPrintingView = false;
    }, 300);
  }

  let nombrePeriodoSeleccionado = $derived.by(() => {
    if (!periodoFiltro) return 'Todos los períodos';
    const p = periodos.find(x => String(x.id_periodo) === String(periodoFiltro));
    return p ? (p.nombre || p.codigo) : 'Período Activo';
  });

  let fechaActualFormateada = $derived(
    new Date().toLocaleDateString('es-EC', { day: '2-digit', month: 'long', year: 'numeric' })
  );

  let proyectosPaginados = $derived.by(() => {
    const list = stats?.ultimos_proyectos || [];
    const start = (pageProy - 1) * pageSizeProy;
    return list.slice(start, start + pageSizeProy);
  });

  let listaRiesgoActual = $derived.by(() => {
    if (!stats?.analisis_riesgo) return [];
    if (modalRiesgoTipo === 'bajo') return stats.analisis_riesgo.lista_bajo || [];
    if (modalRiesgoTipo === 'medio') return stats.analisis_riesgo.lista_medio || [];
    return stats.analisis_riesgo.lista_alto || [];
  });
</script>

<svelte:head>
  <title>Reportes y Estadísticas — SGV UTEQ</title>
</svelte:head>

<!-- SUBBAR SUPERIOR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Reportes y Estadísticas</span>
  </nav>

  <div class="rep-actions">
    <div class="filter-group">
      <i class="bi bi-funnel"></i>
      <select bind:value={periodoFiltro} onchange={cargarEstadisticas} class="rep-select">
        <option value="">Todos los períodos</option>
        {#each periodos as p}
          <option value={p.id_periodo}>{p.nombre || p.codigo}</option>
        {/each}
      </select>
    </div>
    <button class="btn-print" onclick={() => modalPrintOpen = true} title="Configurar e imprimir reporte oficial PDF">
      <i class="bi bi-printer-fill"></i> Imprimir Reporte
    </button>
  </div>
</div>

<div class="page-container">
  
  <!-- MENÚ LATERAL PRINCIPAL -->
  <aside class="sidebar-reportes">
    <div class="sb-box">
      <span class="sb-title">MÓDULO</span>
      <button
        type="button"
        class="sb-btn"
        class:active={activeTab === 'estadisticas'}
        onclick={() => activeTab = 'estadisticas'}
      >
        <i class="bi bi-graph-up-arrow"></i>
        <span>Estadísticas & Gráficos</span>
      </button>

      <button
        type="button"
        class="sb-btn"
        class:active={activeTab === 'riesgo'}
        onclick={() => activeTab = 'riesgo'}
      >
        <i class="bi bi-shield-exclamation"></i>
        <span>Monitoreo de Riesgo</span>
      </button>

      <button
        type="button"
        class="sb-btn"
        class:active={activeTab === 'proyectos'}
        onclick={() => activeTab = 'proyectos'}
      >
        <i class="bi bi-folder2-open"></i>
        <span>Reporte de Proyectos</span>
      </button>

      <button
        type="button"
        class="sb-btn"
        class:active={activeTab === 'convenios'}
        onclick={() => activeTab = 'convenios'}
      >
        <i class="bi bi-file-earmark-text"></i>
        <span>Matriz de Convenios</span>
      </button>

      <hr class="sb-divider" />

      <a href="/dashboard" class="sb-btn">
        <i class="bi bi-house-door"></i>
        <span>Volver al inicio</span>
      </a>
    </div>
  </aside>

  <!-- CONTENIDO CENTRAL -->
  <main class="content-reportes">
    {#if loading || !ChartModule}
      <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Generando análisis estadístico e inferencial...</div>
    {:else if stats}

      <!-- ══════════════════════════════════════════════════════════════
           PESTAÑA 1: ESTADÍSTICAS & GRÁFICOS ANALÍTICOS
      ═══════════════════════════════════════════════════════════════ -->
      {#if activeTab === 'estadisticas' || activeTab === 'riesgo'}
        <div class="rep-wrap">

          <!-- KPIS PRINCIPALES -->
          <div class="kpis-grid">
            <div class="kpi-card verde">
              <div class="kpi-icon"><i class="bi bi-folder2-open"></i></div>
              <div class="kpi-body">
                <span class="kpi-num">{stats.kpis.total_proyectos}</span>
                <span class="kpi-label">Total Proyectos</span>
                <span class="kpi-sub">{stats.kpis.en_ejecucion} en ejecución</span>
              </div>
            </div>

            <div class="kpi-card dorado">
              <div class="kpi-icon"><i class="bi bi-building"></i></div>
              <div class="kpi-body">
                <span class="kpi-num">{stats.kpis.total_entidades}</span>
                <span class="kpi-label">Entidades Cooperantes</span>
                <span class="kpi-sub">Activas</span>
              </div>
            </div>

            <div class="kpi-card azul">
              <div class="kpi-icon"><i class="bi bi-file-earmark-text"></i></div>
              <div class="kpi-body">
                <span class="kpi-num">{stats.kpis.total_convenios}</span>
                <span class="kpi-label">Convenios</span>
                <span class="kpi-sub">Registrados</span>
              </div>
            </div>

            <div class="kpi-card esmeralda">
              <div class="kpi-icon"><i class="bi bi-cash-stack"></i></div>
              <div class="kpi-body">
                <span class="kpi-num">${(stats.kpis.presupuesto_total || 0).toLocaleString('es-EC', { minimumFractionDigits: 2 })}</span>
                <span class="kpi-label">Presupuesto Acumulado</span>
                <span class="kpi-sub">Inversión planificada</span>
              </div>
            </div>

            <div class="kpi-card verde">
              <div class="kpi-icon"><i class="bi bi-geo-alt-fill"></i></div>
              <div class="kpi-body">
                <span class="kpi-num">{stats.kpis.con_geo}</span>
                <span class="kpi-label">Georreferenciados</span>
                <span class="kpi-sub">{stats.kpis.cantones_cobertura || 0} cantones impactados</span>
              </div>
            </div>

            <div class="kpi-card naranja">
              <div class="kpi-icon"><i class="bi bi-speedometer2"></i></div>
              <div class="kpi-body">
                <span class="kpi-num">{stats.kpis.prob_a_tiempo_pct}%</span>
                <span class="kpi-label">P(Cumplimiento a Tiempo)</span>
                <span class="kpi-sub">Modelo predictivo</span>
              </div>
            </div>
          </div>

          <!-- BLOQUE: MODELO DE MONITOREO DE RIESGO TEMPORAL -->
          {#if stats.analisis_riesgo}
            <div class="analytics-banner">
              <div class="ab-header">
                <div class="abh-title">
                  <i class="bi bi-shield-check text-verde"></i>
                  <h4>Modelo de Monitoreo de Riesgo Temporal</h4>
                </div>
                <span class="badge-prob">P(A tiempo): {stats.analisis_riesgo.probabilidad_cumplimiento}%</span>
              </div>

              <!-- BOTONES INTERACTIVOS DE SEMÁFORO -->
              <div class="risk-breakdown">
                <button type="button" class="rb-card green" onclick={() => abrirModalRiesgo('bajo')}>
                  <div class="rb-top">
                    <span class="rb-num">{stats.analisis_riesgo.bajo}</span>
                    <i class="bi bi-arrow-right-circle"></i>
                  </div>
                  <span class="rb-title">🟢 En Cronograma (>85%)</span>
                  <span class="rb-sub">Clic para ver proyectos al día</span>
                </button>

                <button type="button" class="rb-card yellow" onclick={() => abrirModalRiesgo('medio')}>
                  <div class="rb-top">
                    <span class="rb-num">{stats.analisis_riesgo.medio}</span>
                    <i class="bi bi-arrow-right-circle"></i>
                  </div>
                  <span class="rb-title">🟡 Alerta Preventiva (65-85%)</span>
                  <span class="rb-sub">Clic para ver proyectos en seguimiento</span>
                </button>

                <button type="button" class="rb-card red" onclick={() => abrirModalRiesgo('alto')}>
                  <div class="rb-top">
                    <span class="rb-num">{stats.analisis_riesgo.alto}</span>
                    <i class="bi bi-arrow-right-circle"></i>
                  </div>
                  <span class="rb-title">🔴 Riesgo Crítico / Vencidos</span>
                  <span class="rb-sub">Clic para ver proyectos por vencer</span>
                </button>
              </div>

              <!-- LISTA DE PROYECTOS CRÍTICOS -->
              {#if stats.analisis_riesgo.criticos && stats.analisis_riesgo.criticos.length > 0}
                <div class="criticos-box">
                  <span class="criticos-title"><i class="bi bi-exclamation-triangle-fill"></i> Proyectos que requieren atención inmediata:</span>
                  <div class="criticos-list">
                    {#each stats.analisis_riesgo.criticos as cp}
                      <div class="critico-item">
                        <div class="ci-main">
                          <span class="ci-code">{cp.codigo}</span>
                          <span class="ci-name" title={cp.nombre}>{cp.nombre}</span>
                          <span class="ci-fac">{cp.facultad}</span>
                        </div>
                        <div class="ci-actions">
                          <span class="ci-tag" class:vencido={cp.vencido}>
                            {#if cp.vencido}
                              <i class="bi bi-x-circle-fill"></i> Plazo vencido
                            {:else}
                              <i class="bi bi-clock-history"></i> {cp.dias_restantes} días ({cp.pct_tiempo}%)
                            {/if}
                          </span>
                          <button class="btn-ci-view" onclick={() => abrirDetalleProyecto(cp.id_proyecto)}>
                            <i class="bi bi-eye"></i> Ver
                          </button>
                          <button class="btn-ci-edit" onclick={() => goto(`/proyectos/${cp.id_proyecto}/editar`)}>
                            <i class="bi bi-pencil-square"></i> Gestionar
                          </button>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/if}

          <!-- ESTADÍSTICA DESCRIPTIVA DE PRESUPUESTOS -->
          {#if stats.estadisticas_presupuesto}
            <div class="chart-card full-card">
              <h4 class="chart-title"><i class="bi bi-calculator-fill text-verde"></i> Análisis Estadístico Descriptivo de Inversión (USD)</h4>
              <div class="stats-metric-grid">
                <div class="smg-item">
                  <span class="smg-val">${stats.estadisticas_presupuesto.mediana.toLocaleString('es-EC')}</span>
                  <span class="smg-label">Mediana (Q2)</span>
                  <span class="smg-sub">Valor central robusto</span>
                </div>
                <div class="smg-item">
                  <span class="smg-val">${stats.estadisticas_presupuesto.media.toLocaleString('es-EC')}</span>
                  <span class="smg-label">Media Aritmética (μ)</span>
                  <span class="smg-sub">Promedio presupuestario</span>
                </div>
                <div class="smg-item">
                  <span class="smg-val">${stats.estadisticas_presupuesto.desviacion.toLocaleString('es-EC')}</span>
                  <span class="smg-label">Desviación Estándar (σ)</span>
                  <span class="smg-sub">Dispersión de montos</span>
                </div>
                <div class="smg-item">
                  <span class="smg-val">${stats.estadisticas_presupuesto.iqr.toLocaleString('es-EC')}</span>
                  <span class="smg-label">Rango Intercuartílico (IQR)</span>
                  <span class="smg-sub">Q1: ${stats.estadisticas_presupuesto.q1} | Q3: ${stats.estadisticas_presupuesto.q3}</span>
                </div>
                <div class="smg-item">
                  <span class="smg-val">{stats.kpis.duracion_mediana_meses} meses</span>
                  <span class="smg-label">Duración Mediana</span>
                  <span class="smg-sub">Promedio: {stats.kpis.duracion_promedio_meses}m</span>
                </div>
              </div>
            </div>
          {/if}

          <!-- FILA 1: ESTADOS + FACULTADES -->
          <div class="charts-row">
            <div class="chart-card sm">
              <h4 class="chart-title"><i class="bi bi-pie-chart-fill text-verde"></i> Proyectos por estado</h4>
              <div class="chart-wrap h220">
                <canvas use:chartAction={{
                  type: 'doughnut',
                  data: {
                    labels: Object.keys(stats.estados || {}).map(k => ESTADO_LABEL[k] || k),
                    datasets: [{
                      data: Object.keys(stats.estados || {}).map(k => stats.estados[k]),
                      backgroundColor: Object.keys(stats.estados || {}).map(k => ESTADO_COLORES[k] || '#888'),
                      borderWidth: 2,
                      borderColor: '#ffffff',
                      hoverOffset: 6,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: { legend: { display: false }, tooltip: commonTooltip }
                  }
                }}></canvas>
              </div>
              <div class="estado-bars">
                {#each Object.entries(stats.estados || {}) as [k, v]}
                  <div class="ebar">
                    <span class="ebar-label">{ESTADO_LABEL[k] || k}</span>
                    <div class="ebar-track">
                      <div class="ebar-fill" style="width:{(v/(stats.kpis.total_proyectos||1)*100).toFixed(0)}%;background:{ESTADO_COLORES[k]}"></div>
                    </div>
                    <span class="ebar-val">{v} <small>({(v/(stats.kpis.total_proyectos||1)*100).toFixed(0)}%)</small></span>
                  </div>
                {/each}
              </div>
            </div>

            <div class="chart-card lg">
              <h4 class="chart-title"><i class="bi bi-bar-chart-line-fill text-verde"></i> Proyectos por facultad UTEQ</h4>
              <div class="chart-wrap h320">
                <canvas use:chartAction={{
                  type: 'bar',
                  data: {
                    labels: stats.por_facultad?.labels || [],
                    datasets: [{
                      label: 'Proyectos',
                      data: stats.por_facultad?.values || [],
                      backgroundColor: PALETTE,
                      borderRadius: 6,
                      barThickness: 18,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false }, tooltip: commonTooltip },
                    scales: {
                      x: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } },
                      y: { grid: { display: false }, ticks: { font: { size: 11, weight: '700' } } }
                    }
                  }
                }}></canvas>
              </div>
            </div>
          </div>

          <!-- FILA 2: GEOGRAFÍA (PROVINCIAS + CANTONES) -->
          <div class="charts-row">
            <div class="chart-card">
              <h4 class="chart-title"><i class="bi bi-map-fill text-verde"></i> Cobertura por provincia</h4>
              <div class="chart-wrap h260">
                <canvas use:chartAction={{
                  type: 'bar',
                  data: {
                    labels: stats.por_provincia?.labels || [],
                    datasets: [{
                      label: 'Proyectos',
                      data: stats.por_provincia?.values || [],
                      backgroundColor: '#1b7505',
                      borderRadius: 6,
                      barThickness: 18,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false }, tooltip: commonTooltip },
                    scales: {
                      x: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } },
                      y: { grid: { display: false } }
                    }
                  }
                }}></canvas>
              </div>
            </div>

            <div class="chart-card">
              <h4 class="chart-title"><i class="bi bi-geo-fill text-dorado"></i> Cantones impactados</h4>
              <div class="chart-wrap h260">
                <canvas use:chartAction={{
                  type: 'bar',
                  data: {
                    labels: stats.por_canton?.labels || [],
                    datasets: [{
                      label: 'Proyectos',
                      data: stats.por_canton?.values || [],
                      backgroundColor: '#dba112',
                      borderRadius: 6,
                      barThickness: 18,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false }, tooltip: commonTooltip },
                    scales: {
                      x: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } },
                      y: { grid: { display: false } }
                    }
                  }
                }}></canvas>
              </div>
            </div>
          </div>

          <!-- FILA 3: ODS Y CARRERAS -->
          <div class="charts-row">
            <div class="chart-card">
              <h4 class="chart-title"><i class="bi bi-globe-americas text-azul"></i> Alineación con Objetivos ODS</h4>
              <div class="chart-wrap h260">
                <canvas use:chartAction={{
                  type: 'bar',
                  data: {
                    labels: stats.por_ods?.labels || [],
                    datasets: [{
                      label: 'Proyectos alineados',
                      data: stats.por_ods?.values || [],
                      backgroundColor: '#0284c7',
                      borderRadius: 6,
                      barThickness: 18,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false }, tooltip: commonTooltip },
                    scales: {
                      x: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } },
                      y: { grid: { display: false } }
                    }
                  }
                }}></canvas>
              </div>
            </div>

            <div class="chart-card">
              <h4 class="chart-title"><i class="bi bi-mortarboard-fill text-verde"></i> Proyectos por carrera académica</h4>
              <div class="chart-wrap h260">
                <canvas use:chartAction={{
                  type: 'bar',
                  data: {
                    labels: stats.por_carrera?.labels || [],
                    datasets: [{
                      label: 'Proyectos',
                      data: stats.por_carrera?.values || [],
                      backgroundColor: '#2db80a',
                      borderRadius: 6,
                      barThickness: 18,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false }, tooltip: commonTooltip },
                    scales: {
                      x: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } },
                      y: { grid: { display: false } }
                    }
                  }
                }}></canvas>
              </div>
            </div>
          </div>

          <!-- FILA 4: CONVENIOS + ENTIDADES + PERÍODOS -->
          <div class="charts-row">
            <div class="chart-card sm">
              <h4 class="chart-title"><i class="bi bi-file-earmark-check-fill text-verde"></i> Convenios por estado</h4>
              <div class="chart-wrap h200">
                <canvas use:chartAction={{
                  type: 'doughnut',
                  data: {
                    labels: Object.keys(stats.convenios_estados || {}),
                    datasets: [{
                      data: Object.keys(stats.convenios_estados || {}).map(k => stats.convenios_estados[k]),
                      backgroundColor: Object.keys(stats.convenios_estados || {}).map(k => CONV_COLORES[k] || '#888'),
                      borderWidth: 2,
                      borderColor: '#ffffff',
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: { legend: { display: false }, tooltip: commonTooltip }
                  }
                }}></canvas>
              </div>
              <div class="estado-bars sm-bars">
                {#each Object.entries(stats.convenios_estados || {}) as [k, v]}
                  <div class="ebar">
                    <span class="ebar-label">{k}</span>
                    <div class="ebar-track">
                      <div class="ebar-fill" style="width:{(v/(stats.kpis.total_convenios||1)*100).toFixed(0)}%;background:{CONV_COLORES[k]}"></div>
                    </div>
                    <span class="ebar-val">{v}</span>
                  </div>
                {/each}
              </div>
            </div>

            <div class="chart-card sm">
              <h4 class="chart-title"><i class="bi bi-buildings-fill text-dorado"></i> Entidades por tipo</h4>
              <div class="chart-wrap h240">
                <canvas use:chartAction={{
                  type: 'doughnut',
                  data: {
                    labels: stats.entidades_tipos?.labels || [],
                    datasets: [{
                      data: stats.entidades_tipos?.values || [],
                      backgroundColor: PALETTE,
                      borderWidth: 2,
                      borderColor: '#ffffff',
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: {
                      legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                      tooltip: commonTooltip
                    }
                  }
                }}></canvas>
              </div>
            </div>

            <div class="chart-card sm">
              <h4 class="chart-title"><i class="bi bi-calendar-week-fill text-azul"></i> Proyectos por período</h4>
              <div class="chart-wrap h240">
                <canvas use:chartAction={{
                  type: 'bar',
                  data: {
                    labels: stats.por_periodo?.labels || [],
                    datasets: [{
                      label: 'Proyectos',
                      data: stats.por_periodo?.values || [],
                      backgroundColor: '#0284c7',
                      borderRadius: 6,
                      barThickness: 24,
                    }]
                  },
                  options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: commonTooltip },
                    scales: {
                      x: { grid: { display: false } },
                      y: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } }
                    }
                  }
                }}></canvas>
              </div>
            </div>
          </div>

          <!-- ÚLTIMOS PROYECTOS CON PAGINACIÓN -->
          <div class="chart-card full-card">
            <div class="card-hdr-flex">
              <h4 class="chart-title"><i class="bi bi-clock-history text-verde"></i> ÚLTIMOS PROYECTOS REGISTRADOS</h4>
              <a href="/proyectos" class="link-proys">Ir a lista completa de proyectos →</a>
            </div>
            
            <div class="table-responsive">
              <table class="mini-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre del Proyecto</th>
                    <th>Facultad & Carrera</th>
                    <th>Fechas Planificadas</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {#each proyectosPaginados as p}
                    <tr>
                      <td><span class="code">{p.codigo}</span></td>
                      <td class="td-trunc">
                        <button type="button" class="btn-link-proy" onclick={() => abrirDetalleProyecto(p.id_proyecto)}>
                          {p.nombre}
                        </button>
                      </td>
                      <td class="txt-sm">
                        <div><strong>{p.facultad}</strong></div>
                        <div class="txt-muted">{p.carrera}</div>
                      </td>
                      <td class="txt-sm">{p.fecha_inicio} a {p.fecha_fin}</td>
                      <td>
                        <span class="badge-est" style="background:{ESTADO_COLORES[p.estado]}18;color:{ESTADO_COLORES[p.estado]};border:1px solid {ESTADO_COLORES[p.estado]}40">
                          {ESTADO_LABEL[p.estado] || p.estado}
                        </span>
                      </td>
                      <td>
                        <div class="actions-cell">
                          <button class="btn-action-sm" title="Ver Detalle" onclick={() => abrirDetalleProyecto(p.id_proyecto)}>
                            <i class="bi bi-eye"></i>
                          </button>
                          <button class="btn-action-sm edit" title="Editar Proyecto" onclick={() => goto(`/proyectos/${p.id_proyecto}/editar`)}>
                            <i class="bi bi-pencil"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>

            <div class="pag-wrapper">
              <Pagination
                bind:page={pageProy}
                bind:pageSize={pageSizeProy}
                totalItems={stats.ultimos_proyectos?.length || 0}
                itemLabel="proyectos"
              />
            </div>
          </div>

        </div>

      <!-- ══════════════════════════════════════════════════════════════
           PESTAÑA 2: REPORTE EJECUTIVO DE PROYECTOS (OFICIAL)
      ═══════════════════════════════════════════════════════════════ -->
      {:else if activeTab === 'proyectos'}
        <div class="report-document-card">
          <div class="doc-header">
            <div class="doc-logo-box">
              <img src="/logo-uteq.png" alt="UTEQ" class="doc-logo" />
            </div>
            <div class="doc-title-box">
              <h3>UNIVERSIDAD TÉCNICA ESTATAL DE QUEVEDO</h3>
              <h4>DIRECCIÓN DE VINCULACIÓN CON LA SOCIEDAD</h4>
              <p class="doc-subtitle">MATRIZ GENERAL DE PROYECTOS DE VINCULACIÓN</p>
              <div class="doc-meta-row">
                <span><strong>Período:</strong> {nombrePeriodoSeleccionado}</span>
                <span><strong>Fecha de emisión:</strong> {fechaActualFormateada}</span>
              </div>
            </div>
          </div>

          <div class="doc-body">
            <table class="doc-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Código</th>
                  <th>Proyecto de Vinculación</th>
                  <th>Facultad</th>
                  <th>Carrera</th>
                  <th>Vigencia</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {#each stats.ultimos_proyectos || [] as p, i}
                  <tr>
                    <td>{i + 1}</td>
                    <td><strong>{p.codigo}</strong></td>
                    <td>{p.nombre}</td>
                    <td>{p.facultad}</td>
                    <td>{p.carrera}</td>
                    <td>{p.fecha_inicio} a {p.fecha_fin}</td>
                    <td>
                      <span class="badge-est" style="background:{ESTADO_COLORES[p.estado]}18;color:{ESTADO_COLORES[p.estado]}">
                        {ESTADO_LABEL[p.estado] || p.estado}
                      </span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>

          <div class="doc-firmas">
            <div class="firma-col">
              <div class="firma-linea"></div>
              <span>DIRECTOR(A) DE VINCULACIÓN</span>
              <small>Universidad Técnica Estatal de Quevedo</small>
            </div>
            <div class="firma-col">
              <div class="firma-linea"></div>
              <span>RESPONSABLE DE PROYECTOS</span>
              <small>Comisión de Vinculación con la Sociedad</small>
            </div>
          </div>
        </div>

      <!-- ══════════════════════════════════════════════════════════════
           PESTAÑA 3: MATRIZ DE CONVENIOS (OFICIAL)
      ═══════════════════════════════════════════════════════════════ -->
      {:else if activeTab === 'convenios'}
        <div class="report-document-card">
          <div class="doc-header">
            <div class="doc-logo-box">
              <img src="/logo-uteq.png" alt="UTEQ" class="doc-logo" />
            </div>
            <div class="doc-title-box">
              <h3>UNIVERSIDAD TÉCNICA ESTATAL DE QUEVEDO</h3>
              <h4>DIRECCIÓN DE VINCULACIÓN CON LA SOCIEDAD</h4>
              <p class="doc-subtitle">MATRIZ INSTITUCIONAL DE CONVENIOS DE VINCULACIÓN</p>
              <div class="doc-meta-row">
                <span><strong>Período:</strong> {nombrePeriodoSeleccionado}</span>
                <span><strong>Fecha de emisión:</strong> {fechaActualFormateada}</span>
              </div>
            </div>
          </div>

          <div class="doc-body">
            <div class="kpis-grid mb-16">
              <div class="kpi-card verde">
                <div class="kpi-icon"><i class="bi bi-file-earmark-check-fill"></i></div>
                <div class="kpi-body">
                  <span class="kpi-num">{stats.kpis.total_convenios}</span>
                  <span class="kpi-label">Convenios Totales</span>
                </div>
              </div>
              <div class="kpi-card dorado">
                <div class="kpi-icon"><i class="bi bi-building"></i></div>
                <div class="kpi-body">
                  <span class="kpi-num">{stats.kpis.total_entidades}</span>
                  <span class="kpi-label">Entidades Vinculadas</span>
                </div>
              </div>
            </div>
            <p class="txt-sub">Utiliza el botón superior "Imprimir Reporte" para generar el informe oficial con firmas institucionales.</p>
          </div>

          <div class="doc-firmas">
            <div class="firma-col">
              <div class="firma-linea"></div>
              <span>DIRECTOR(A) DE VINCULACIÓN</span>
              <small>Universidad Técnica Estatal de Quevedo</small>
            </div>
            <div class="firma-col">
              <div class="firma-linea"></div>
              <span>COORDINADOR(A) DE CONVENIOS</span>
              <small>Comisión de Vinculación con la Sociedad</small>
            </div>
          </div>
        </div>
      {/if}

    {:else}
      <div class="loading">No se pudieron cargar los datos del reporte.</div>
    {/if}
  </main>
</div>

<!-- ══════════════════════════════════════════════════════════════
     MODAL DE CONFIGURACIÓN DE IMPRESIÓN (TEMPLATE METHOD)
═══════════════════════════════════════════════════════════════ -->
{#if modalPrintOpen}
  <div class="modal-backdrop" onclick={() => modalPrintOpen = false} role="presentation">
    <div class="modal-card modal-print-setup" onclick={e => e.stopPropagation()} role="dialog">
      <div class="modal-hdr-uteq">
        <div class="modal-hdr-info">
          <div class="modal-hdr-icon-green">
            <i class="bi bi-printer-fill"></i>
          </div>
          <div>
            <h3 class="modal-hdr-title">Generador de Reporte Institucional UTEQ</h3>
            <span class="modal-hdr-sub">Selecciona los módulos y secciones que deseas incluir en el PDF</span>
          </div>
        </div>
        <button class="btn-close-modal" onclick={() => modalPrintOpen = false} aria-label="Cerrar modal">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="modal-body-scroll">
        <div class="print-config-section">
          <span class="pcs-title"><i class="bi bi-sliders"></i> Secciones del Informe:</span>
          
          <div class="pcs-grid">
            <label class="pcs-item">
              <input type="checkbox" bind:checked={printOptKpis} />
              <div class="pcs-text">
                <strong>Resumen Ejecutivo y KPIs Generales</strong>
                <small>Total de proyectos, presupuesto acumulado y cobertura</small>
              </div>
            </label>

            <label class="pcs-item">
              <input type="checkbox" bind:checked={printOptRiesgo} />
              <div class="pcs-text">
                <strong>Modelo de Monitoreo de Riesgo Temporal</strong>
                <small>Semáforo predictivo y lista de proyectos en riesgo crítico</small>
              </div>
            </label>

            <label class="pcs-item">
              <input type="checkbox" bind:checked={printOptStats} />
              <div class="pcs-text">
                <strong>Estadística Descriptiva e Inferencia (USD)</strong>
                <small>Mediana (Q2), Media, Desviación Estándar (σ) y Cuartiles</small>
              </div>
            </label>

            <label class="pcs-item">
              <input type="checkbox" bind:checked={printOptFacultades} />
              <div class="pcs-text">
                <strong>Proyectos por Estado y Facultad UTEQ</strong>
                <small>Gráficos y distribución porcentual por facultades</small>
              </div>
            </label>

            <label class="pcs-item">
              <input type="checkbox" bind:checked={printOptProvincias} />
              <div class="pcs-text">
                <strong>Cobertura Territorial y Cantones</strong>
                <small>Provincias impactadas y alineación ODS</small>
              </div>
            </label>

            <label class="pcs-item">
              <input type="checkbox" bind:checked={printOptProyectos} />
              <div class="pcs-text">
                <strong>Matriz General de Proyectos</strong>
                <small>Listado tabular completo con código, facultad y vigencia</small>
              </div>
            </label>
          </div>
        </div>

        <div class="print-preview-meta">
          <div class="ppm-item">
            <span class="ppm-label">Período Académico:</span>
            <span class="ppm-val">{nombrePeriodoSeleccionado}</span>
          </div>
          <div class="ppm-item">
            <span class="ppm-label">Formato de Salida:</span>
            <span class="ppm-val">Membrete Oficial UTEQ con Firmas de Responsabilidad</span>
          </div>
        </div>
      </div>

      <div class="modal-footer-bar">
        <button class="btn-sec" onclick={() => modalPrintOpen = false}>Cancelar</button>
        <button class="btn-prim-uteq" onclick={ejecutarImpresionConfigurada}>
          <i class="bi bi-file-earmark-pdf-fill"></i> Generar & Imprimir PDF
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ══════════════════════════════════════════════════════════════
     MODAL DE CATEGORÍAS DE RIESGO (VERDE / AMARILLO / ROJO)
═══════════════════════════════════════════════════════════════ -->
{#if modalRiesgoOpen}
  <div class="modal-backdrop" onclick={() => modalRiesgoOpen = false} role="presentation">
    <div class="modal-card" onclick={e => e.stopPropagation()} role="dialog">
      <div class="modal-hdr" class:green={modalRiesgoTipo === 'bajo'} class:yellow={modalRiesgoTipo === 'medio'} class:red={modalRiesgoTipo === 'alto'}>
        <div class="modal-hdr-info">
          <div class="modal-hdr-icon">
            {#if modalRiesgoTipo === 'bajo'}
              <i class="bi bi-check-circle-fill"></i>
            {:else if modalRiesgoTipo === 'medio'}
              <i class="bi bi-exclamation-triangle-fill"></i>
            {:else}
              <i class="bi bi-x-circle-fill"></i>
            {/if}
          </div>
          <div>
            <h3 class="modal-hdr-title">
              {#if modalRiesgoTipo === 'bajo'}
                Proyectos en Cronograma (&gt;85% Probabilidad)
              {:else if modalRiesgoTipo === 'medio'}
                Proyectos con Alerta Preventiva (65-85%)
              {:else}
                Proyectos en Riesgo Crítico / Vencidos (&lt;65%)
              {/if}
            </h3>
            <span class="modal-hdr-sub">{listaRiesgoActual.length} proyectos encontrados en esta categoría</span>
          </div>
        </div>
        <button class="btn-close-modal" onclick={() => modalRiesgoOpen = false} aria-label="Cerrar modal">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="modal-body-scroll">
        {#if listaRiesgoActual.length === 0}
          <div class="empty-state-modal">
            <i class="bi bi-inbox"></i>
            <p>No hay proyectos en esta categoría de riesgo.</p>
          </div>
        {:else}
          <div class="risk-modal-list">
            {#each listaRiesgoActual as p}
              <div class="rml-item">
                <div class="rml-main">
                  <div class="rml-code-row">
                    <span class="code">{p.codigo}</span>
                    <span class="rml-fac">{p.facultad} · {p.carrera}</span>
                  </div>
                  <h4 class="rml-title">{p.nombre}</h4>
                  <div class="rml-dates">
                    <span><i class="bi bi-calendar"></i> {p.fecha_inicio} a {p.fecha_fin}</span>
                    <span class="rml-tag" class:tag-red={p.vencido} class:tag-green={!p.vencido && p.pct_tiempo < 65} class:tag-yellow={!p.vencido && p.pct_tiempo >= 65}>
                      {#if p.vencido}
                        <i class="bi bi-exclamation-octagon-fill"></i> Plazo vencido
                      {:else}
                        <i class="bi bi-hourglass-split"></i> {p.dias_restantes} días restantes ({p.pct_tiempo}% consumido)
                      {/if}
                    </span>
                  </div>
                </div>

                <div class="rml-actions">
                  <button class="btn-rml-view" onclick={() => { modalRiesgoOpen = false; abrirDetalleProyecto(p.id_proyecto); }}>
                    <i class="bi bi-eye"></i> Ver Detalle
                  </button>
                  <button class="btn-rml-edit" onclick={() => irAEditarProyecto(p.id_proyecto)}>
                    <i class="bi bi-pencil-square"></i> Ir a Proyecto
                  </button>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="modal-footer-bar">
        <button class="btn-sec" onclick={() => modalRiesgoOpen = false}>Cerrar</button>
      </div>
    </div>
  </div>
{/if}

<!-- MODAL DE DETALLE DEL PROYECTO -->
<ProyectoDetalleModal
  idProyecto={modalProyectoId}
  isOpen={modalProyectoOpen}
  onClose={() => { modalProyectoOpen = false; modalProyectoId = null; }}
/>

<style>
  .subbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 24px; background: #ffffff; border-bottom: 1px solid var(--borde, #e0e0e0);
  }
  .rep-actions { display: flex; align-items: center; gap: 12px; }
  .filter-group {
    display: flex; align-items: center; gap: 8px;
    background: #f8fafc; border: 1.5px solid var(--borde, #e0e0e0);
    border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #475569;
  }
  .rep-select {
    border: none; background: transparent; font-family: inherit; font-size: 0.8rem;
    font-weight: 700; color: #1e293b; outline: none; cursor: pointer;
  }
  .btn-print {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--verde, #1b7505); color: #ffffff; border: none; border-radius: 20px;
    padding: 7px 18px; font-size: 0.8rem; font-weight: 800; cursor: pointer;
    transition: background 0.15s; font-family: inherit;
  }
  .btn-print:hover { background: #134217; }

  .page-container {
    display: flex; min-height: calc(100vh - 120px); background: #f4f6f3;
  }

  /* SIDEBAR DE REPORTES */
  .sidebar-reportes {
    width: 260px; background: #ffffff; border-right: 1px solid var(--borde, #e0e0e0);
    padding: 20px 16px; flex-shrink: 0;
  }
  .sb-box { display: flex; flex-direction: column; gap: 6px; }
  .sb-title { font-size: 0.68rem; font-weight: 800; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 8px; padding-left: 6px; }
  .sb-btn {
    display: flex; align-items: center; gap: 10px; padding: 10px 14px;
    border: none; border-radius: 10px; background: transparent;
    font-family: inherit; font-size: 0.83rem; font-weight: 700; color: #475569;
    cursor: pointer; transition: all 0.15s ease; text-align: left; text-decoration: none;
  }
  .sb-btn i { font-size: 1.1rem; color: #64748b; }
  .sb-btn:hover { background: #f1f5f9; color: #0f172a; }
  .sb-btn.active {
    background: var(--verde-claro, #e8f5e0); color: var(--verde, #1b7505); font-weight: 800;
  }
  .sb-btn.active i { color: var(--verde, #1b7505); }
  .sb-divider { border: none; border-top: 1px solid #e2e8f0; margin: 10px 0; }

  .content-reportes { flex: 1; padding: 22px 26px; min-width: 0; }

  .loading {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    padding: 60px; font-size: 0.9rem; font-weight: 700; color: #64748b;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 0.7s linear infinite; }

  .rep-wrap { display: flex; flex-direction: column; gap: 18px; }

  /* KPIs Grid */
  .kpis-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
  .kpi-card {
    background: #ffffff; border-radius: 14px; border: 1px solid var(--borde, #e0e0e0);
    padding: 16px 18px; display: flex; align-items: center; gap: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03); transition: transform 0.18s, box-shadow 0.18s;
  }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
  .kpi-icon {
    width: 44px; height: 44px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;
  }
  .kpi-card.verde .kpi-icon { background: var(--verde-claro, #e8f5e0); color: var(--verde, #1b7505); }
  .kpi-card.dorado .kpi-icon { background: #fff8e1; color: var(--dorado, #dba112); }
  .kpi-card.azul .kpi-icon { background: #f0f9ff; color: #0284c7; }
  .kpi-card.esmeralda .kpi-icon { background: #ecfdf5; color: #059669; }
  .kpi-card.naranja .kpi-icon { background: #fff7ed; color: #ea580c; }

  .kpi-body { display: flex; flex-direction: column; gap: 2px; }
  .kpi-num { font-size: 1.35rem; font-weight: 900; color: #0f172a; line-height: 1.1; }
  .kpi-label { font-size: 0.68rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }
  .kpi-sub { font-size: 0.68rem; color: #64748b; font-weight: 600; }

  /* BANNER ANALÍTICO DE RIESGO */
  .analytics-banner {
    background: #ffffff; border: 1.5px solid #a3e635; border-radius: 14px;
    padding: 20px 24px; display: flex; flex-direction: column; gap: 16px;
    box-shadow: 0 4px 16px rgba(27, 117, 5, 0.06);
  }
  .ab-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
  .abh-title { display: flex; align-items: center; gap: 10px; }
  .abh-title i { font-size: 1.3rem; }
  .abh-title h4 { font-size: 1.05rem; font-weight: 800; color: #0f172a; margin: 0; }
  .badge-prob { background: var(--verde-claro, #e8f5e0); color: var(--verde, #1b7505); font-size: 0.8rem; font-weight: 800; padding: 4px 12px; border-radius: 20px; }

  .risk-breakdown { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
  .rb-card {
    padding: 16px; border-radius: 12px; display: flex; flex-direction: column; gap: 4px;
    border: 1.5px solid var(--borde, #e0e0e0); cursor: pointer; text-align: left; font-family: inherit;
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .rb-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.06); }
  .rb-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; }
  .rb-card.green { background: #f0fdf4; border-color: #bbf7d0; color: #15803d; }
  .rb-card.yellow { background: #fffbeb; border-color: #fde68a; color: #b45309; }
  .rb-card.red { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }
  .rb-num { font-size: 1.4rem; font-weight: 900; }
  .rb-title { font-size: 0.74rem; font-weight: 800; text-transform: uppercase; }
  .rb-sub { font-size: 0.68rem; opacity: 0.85; font-weight: 600; }

  .criticos-box {
    background: #fff1f2; border: 1px solid #fecdd3; border-radius: 10px; padding: 14px;
    display: flex; flex-direction: column; gap: 10px;
  }
  .criticos-title { font-size: 0.78rem; font-weight: 800; color: #9f1239; display: flex; align-items: center; gap: 6px; }
  .criticos-list { display: flex; flex-direction: column; gap: 6px; }
  .critico-item {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
    background: #ffffff; border: 1px solid #fda4af; border-radius: 8px; padding: 8px 12px; font-size: 0.8rem;
  }
  .ci-main { display: flex; align-items: center; gap: 8px; min-width: 0; }
  .ci-code { font-family: monospace; font-weight: 800; color: #be123c; background: #ffe4e6; padding: 2px 6px; border-radius: 4px; }
  .ci-name { font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 320px; }
  .ci-fac { font-size: 0.72rem; color: #64748b; }
  .ci-actions { display: flex; align-items: center; gap: 8px; }
  .ci-tag { font-size: 0.74rem; font-weight: 700; color: #b45309; display: flex; align-items: center; gap: 5px; }
  .ci-tag.vencido { color: #dc2626; font-weight: 800; }
  .btn-ci-view {
    background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; border-radius: 6px;
    padding: 4px 10px; font-size: 0.74rem; font-weight: 700; cursor: pointer;
  }
  .btn-ci-view:hover { background: #e2e8f0; }
  .btn-ci-edit {
    background: var(--verde, #1b7505); color: #ffffff; border: none; border-radius: 6px;
    padding: 4px 10px; font-size: 0.74rem; font-weight: 700; cursor: pointer;
  }
  .btn-ci-edit:hover { background: #134217; }

  /* ESTADÍSTICA DESCRIPTIVA */
  .stats-metric-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 10px;
  }
  .smg-item {
    background: #f8fafc; border: 1px solid var(--borde, #e0e0e0); border-radius: 10px; padding: 12px 14px;
    display: flex; flex-direction: column; gap: 2px;
  }
  .smg-val { font-size: 1.15rem; font-weight: 900; color: #0f172a; }
  .smg-label { font-size: 0.7rem; font-weight: 800; color: #475569; text-transform: uppercase; }
  .smg-sub { font-size: 0.68rem; color: #64748b; }

  /* Charts Row */
  .charts-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
  .chart-card {
    background: #ffffff; border-radius: 14px; border: 1px solid var(--borde, #e0e0e0);
    padding: 20px 22px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); display: flex; flex-direction: column;
  }
  .chart-card.sm { min-width: 0; }
  .chart-card.lg { grid-column: span 2; }
  .chart-card.full-card { grid-column: 1 / -1; }

  .chart-title {
    font-size: 0.84rem; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.04em;
    margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
  }
  .chart-wrap { position: relative; width: 100%; }
  .h200 { height: 200px; }
  .h220 { height: 220px; }
  .h240 { height: 240px; }
  .h260 { height: 260px; }
  .h320 { height: 320px; }

  /* Estado bars */
  .estado-bars { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
  .sm-bars { gap: 6px; }
  .ebar { display: flex; align-items: center; gap: 10px; font-size: 0.75rem; }
  .ebar-label { min-width: 90px; color: #475569; font-weight: 700; }
  .ebar-track { flex: 1; height: 7px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
  .ebar-fill { height: 100%; border-radius: 4px; transition: width 0.4s; }
  .ebar-val { min-width: 50px; text-align: right; font-weight: 800; color: #0f172a; }
  .ebar-val small { font-size: 0.7rem; color: #64748b; font-weight: 600; }

  /* Mini table & Paginación */
  .card-hdr-flex { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .link-proys { font-size: 0.8rem; font-weight: 800; color: var(--verde, #1b7505); text-decoration: none; }
  .link-proys:hover { text-decoration: underline; }

  .table-responsive { width: 100%; overflow-x: auto; }
  .mini-table { width: 100%; border-collapse: collapse; text-align: left; }
  .mini-table th { font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.04em; padding: 10px 14px; border-bottom: 1.5px dashed var(--borde, #e0e0e0); }
  .mini-table td { padding: 11px 14px; font-size: 0.84rem; border-bottom: 1px solid #f1f5f9; }
  .code { background: var(--verde-claro, #e8f5e0); color: var(--verde, #1b7505); padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; font-family: monospace; }
  .td-trunc { max-width: 300px; }
  .btn-link-proy {
    background: transparent; border: none; font-weight: 700; color: #0f172a;
    padding: 0; text-align: left; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 280px; display: block;
  }
  .btn-link-proy:hover { color: var(--verde, #1b7505); text-decoration: underline; }
  .txt-sm { font-size: 0.78rem; color: #334155; font-weight: 600; }
  .txt-muted { font-size: 0.72rem; color: #64748b; }
  .badge-est { padding: 4px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 800; }

  .actions-cell { display: flex; align-items: center; gap: 6px; }
  .btn-action-sm {
    width: 30px; height: 30px; border-radius: 6px; border: 1px solid #cbd5e1;
    background: #ffffff; color: #475569; display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all 0.15s ease;
  }
  .btn-action-sm:hover { background: #f1f5f9; color: #0f172a; }
  .btn-action-sm.edit:hover { background: var(--verde-claro, #e8f5e0); color: var(--verde, #1b7505); border-color: #86efac; }
  .pag-wrapper { margin-top: 14px; }

  /* DOCUMENTOS OFICIALES IMPRIMIBLES */
  .report-document-card {
    background: #ffffff; border-radius: 14px; border: 1px solid var(--borde, #e0e0e0); padding: 36px 40px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.03);
  }
  .doc-header { display: flex; align-items: center; gap: 20px; border-bottom: 2.5px solid #0f172a; padding-bottom: 20px; margin-bottom: 24px; }
  .doc-logo { width: 70px; height: auto; object-fit: contain; }
  .doc-title-box h3 { font-size: 1.2rem; font-weight: 900; color: #0f172a; margin: 0; }
  .doc-title-box h4 { font-size: 0.95rem; font-weight: 800; color: var(--verde, #1b7505); margin: 2px 0; }
  .doc-subtitle { font-size: 0.86rem; color: #475569; font-weight: 800; margin: 4px 0; }
  .doc-meta-row { display: flex; gap: 20px; font-size: 0.78rem; color: #64748b; margin-top: 6px; }

  .doc-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
  .doc-table th { background: #f8fafc; border: 1px solid #cbd5e1; padding: 10px 12px; font-size: 0.74rem; font-weight: 800; color: #0f172a; text-transform: uppercase; }
  .doc-table td { border: 1px solid #e2e8f0; padding: 10px 12px; color: #1e293b; }

  .doc-firmas { display: flex; justify-content: space-around; margin-top: 60px; padding-top: 20px; }
  .firma-col { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; }
  .firma-linea { width: 220px; border-top: 1.5px solid #334155; margin-bottom: 8px; }
  .firma-col span { font-size: 0.78rem; font-weight: 800; color: #0f172a; }
  .firma-col small { font-size: 0.7rem; color: #64748b; }

  /* MODAL DE CONFIGURACIÓN DE IMPRESIÓN */
  .modal-print-setup { max-width: 650px; }
  .modal-hdr-uteq {
    padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;
    background: #f8fafc; border-bottom: 1px solid var(--borde, #e0e0e0);
  }
  .modal-hdr-icon-green {
    width: 40px; height: 40px; border-radius: 10px; background: var(--verde-claro, #e8f5e0);
    color: var(--verde, #1b7505); display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
  }
  .print-config-section { display: flex; flex-direction: column; gap: 12px; }
  .pcs-title { font-size: 0.82rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 6px; }
  .pcs-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
  .pcs-item {
    display: flex; align-items: flex-start; gap: 12px; background: #ffffff; border: 1.5px solid var(--borde, #e0e0e0);
    border-radius: 10px; padding: 12px 14px; cursor: pointer; transition: all 0.15s ease;
  }
  .pcs-item:hover { border-color: var(--verde, #1b7505); background: #fdfefe; }
  .pcs-item input { margin-top: 3px; accent-color: var(--verde, #1b7505); width: 16px; height: 16px; }
  .pcs-text { display: flex; flex-direction: column; gap: 1px; }
  .pcs-text strong { font-size: 0.84rem; color: #0f172a; font-weight: 800; }
  .pcs-text small { font-size: 0.72rem; color: #64748b; }

  .print-preview-meta {
    background: #f8fafc; border: 1px solid var(--borde, #e0e0e0); border-radius: 10px;
    padding: 12px 16px; margin-top: 14px; display: flex; flex-direction: column; gap: 6px;
  }
  .ppm-item { display: flex; justify-content: space-between; font-size: 0.76rem; }
  .ppm-label { color: #64748b; font-weight: 700; }
  .ppm-val { color: #0f172a; font-weight: 800; }

  .btn-prim-uteq {
    background: var(--verde, #1b7505); color: #ffffff; border: none; border-radius: 8px;
    padding: 8px 18px; font-size: 0.84rem; font-weight: 800; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;
  }
  .btn-prim-uteq:hover { background: #134217; }

  /* MODAL DE RIESGO */
  .modal-backdrop {
    position: fixed; inset: 0; background: rgba(13, 25, 16, 0.65);
    backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center;
    z-index: 9999; padding: 20px;
  }
  .modal-card {
    background: #ffffff; width: 100%; max-width: 740px; border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.2); overflow: hidden; display: flex; flex-direction: column; max-height: 85vh;
  }
  .modal-hdr {
    padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--borde, #e0e0e0);
  }
  .modal-hdr.green { background: #f0fdf4; border-color: #bbf7d0; }
  .modal-hdr.yellow { background: #fffbeb; border-color: #fde68a; }
  .modal-hdr.red { background: #fef2f2; border-color: #fecaca; }

  .modal-hdr-info { display: flex; align-items: center; gap: 12px; }
  .modal-hdr-icon {
    width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
  }
  .modal-hdr.green .modal-hdr-icon { background: #dcfce7; color: #15803d; }
  .modal-hdr.yellow .modal-hdr-icon { background: #fef3c7; color: #d97706; }
  .modal-hdr.red .modal-hdr-icon { background: #fee2e2; color: #dc2626; }

  .modal-hdr-title { font-size: 0.98rem; font-weight: 800; color: #0f172a; margin: 0; }
  .modal-hdr-sub { font-size: 0.74rem; color: #64748b; font-weight: 600; }

  .btn-close-modal {
    background: transparent; border: none; font-size: 1.1rem; color: #64748b;
    cursor: pointer; padding: 6px; border-radius: 8px;
  }
  .btn-close-modal:hover { background: rgba(0,0,0,0.05); color: #0f172a; }

  .modal-body-scroll { padding: 20px; overflow-y: auto; flex: 1; }
  .empty-state-modal { text-align: center; padding: 40px; color: #64748b; }
  .empty-state-modal i { font-size: 2.5rem; color: #cbd5e1; margin-bottom: 8px; display: block; }

  .risk-modal-list { display: flex; flex-direction: column; gap: 12px; }
  .rml-item {
    background: #ffffff; border: 1.5px solid var(--borde, #e0e0e0); border-radius: 12px; padding: 14px 16px;
    display: flex; align-items: center; justify-content: space-between; gap: 14px;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  .rml-item:hover { border-color: var(--verde, #1b7505); box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
  .rml-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
  .rml-code-row { display: flex; align-items: center; gap: 8px; }
  .rml-fac { font-size: 0.72rem; color: #64748b; font-weight: 700; }
  .rml-title { font-size: 0.88rem; font-weight: 800; color: #0f172a; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .rml-dates { display: flex; align-items: center; gap: 12px; font-size: 0.74rem; color: #64748b; flex-wrap: wrap; }
  .rml-tag { padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.7rem; display: inline-flex; align-items: center; gap: 4px; }
  .tag-green { background: #dcfce7; color: #15803d; }
  .tag-yellow { background: #fef3c7; color: #b45309; }
  .tag-red { background: #fee2e2; color: #b91c1c; font-weight: 800; }

  .rml-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  .btn-rml-view {
    background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; border-radius: 8px;
    padding: 6px 12px; font-size: 0.76rem; font-weight: 700; cursor: pointer;
  }
  .btn-rml-view:hover { background: #e2e8f0; color: #0f172a; }
  .btn-rml-edit {
    background: var(--verde, #1b7505); color: #ffffff; border: none; border-radius: 8px;
    padding: 6px 12px; font-size: 0.76rem; font-weight: 800; cursor: pointer;
  }
  .btn-rml-edit:hover { background: #134217; }

  .modal-footer-bar {
    padding: 12px 20px; background: #f8fafc; border-top: 1px solid var(--borde, #e0e0e0);
    display: flex; justify-content: flex-end; gap: 10px;
  }
  .btn-sec {
    background: #ffffff; border: 1px solid var(--borde, #e0e0e0); border-radius: 8px;
    padding: 8px 16px; font-size: 0.8rem; font-weight: 700; color: #475569; cursor: pointer;
  }
  .btn-sec:hover { background: #f1f5f9; }

  .text-verde { color: var(--verde, #1b7505); }
  .text-azul  { color: #0284c7; }
  .text-dorado { color: var(--dorado, #dba112); }
  .mb-16 { margin-bottom: 16px; }
  .txt-sub { font-size: 0.82rem; color: #64748b; }

  @media (max-width: 992px) {
    .chart-card.lg { grid-column: span 1; }
    .page-container { flex-direction: column; }
    .sidebar-reportes { width: 100%; border-right: none; border-bottom: 1px solid var(--borde, #e0e0e0); }
  }

  @media print {
    .subbar, .sidebar-reportes, .btn-print, .rep-actions, .modal-backdrop { display: none !important; }
    .page-container { background: #ffffff !important; display: block !important; }
    .content-reportes { padding: 0 !important; }
    .rep-wrap { padding: 0 !important; gap: 14px !important; }
    .chart-card, .report-document-card { break-inside: avoid; border: 1px solid #ccc !important; box-shadow: none !important; margin-bottom: 16px; }
    .doc-firmas { break-inside: avoid; }
  }
</style>
