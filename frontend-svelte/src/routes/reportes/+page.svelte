<script>
  import { onMount } from 'svelte';
  import { fetchAPI, fetchAPICached } from '$lib/stores';

  let stats = $state(null);
  let periodos = $state([]);
  let periodoFiltro = $state('');
  let loading = $state(true);
  let ChartModule = $state(null);
  let activeTab = $state('estadisticas'); // 'estadisticas' | 'proyectos' | 'convenios'

  const ESTADO_COLORES = {
    EN_EJECUCION: '#16a34a',
    PROPUESTO: '#d97706',
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
    VIGENTE: '#16a34a',
    VENCIDO: '#dc2626',
    RENOVADO: '#0284c7',
    CANCELADO: '#64748b',
  };
  const PALETTE = [
    '#16a34a', '#0284c7', '#d97706', '#9333ea', '#0891b2',
    '#ea580c', '#4f46e5', '#059669', '#ca8a04', '#e11d48'
  ];

  const commonTooltip = {
    backgroundColor: 'rgba(15, 23, 42, 0.94)',
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

    cargarEstadisticas();
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

  function imprimirReporte() {
    window.print();
  }
</script>

<svelte:head>
  <title>Reportes y Estadísticas — SGV UTEQ</title>
</svelte:head>

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
    <button class="btn-print" onclick={imprimirReporte} title="Imprimir o guardar como PDF oficial">
      <i class="bi bi-printer"></i> Imprimir Reporte
    </button>
  </div>
</div>

<div class="page-container">
  
  <aside class="sidebar-reportes">
    <div class="sb-box">
      <span class="sb-title">MÓDULOS DE ANÁLISIS</span>
      <button
        type="button"
        class="sb-btn"
        class:active={activeTab === 'estadisticas'}
        onclick={() => activeTab = 'estadisticas'}
      >
        <i class="bi bi-graph-up-arrow"></i>
        <span>Estadísticas & Probabilidad</span>
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
    </div>
  </aside>

  <main class="content-reportes">
    {#if loading || !ChartModule}
      <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Generando análisis estadístico e inferencial...</div>
    {:else if stats}

      <!-- ══════════════════════════════════════════════════════════════
           PESTAÑA 1: ESTADÍSTICAS Y MODELO PREDICTIVO
      ═══════════════════════════════════════════════════════════════ -->
      {#if activeTab === 'estadisticas'}
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

          <!-- BLOQUE DE ANÁLISIS PREDICTIVO Y RIESGO TEMPORAL -->
          {#if stats.analisis_riesgo}
            <div class="analytics-banner">
              <div class="ab-header">
                <div class="abh-title">
                  <i class="bi bi-shield-check text-verde"></i>
                  <h4>Modelo de Probabilidad y Monitoreo de Riesgo Temporal</h4>
                </div>
                <span class="badge-prob">P(A tiempo): {stats.analisis_riesgo.probabilidad_cumplimiento}%</span>
              </div>

              <div class="risk-breakdown">
                <div class="rb-card green">
                  <span class="rb-num">{stats.analisis_riesgo.bajo}</span>
                  <span class="rb-title">🟢 En Cronograma (>85%)</span>
                  <span class="rb-sub">Proyectos con margen temporal</span>
                </div>
                <div class="rb-card yellow">
                  <span class="rb-num">{stats.analisis_riesgo.medio}</span>
                  <span class="rb-title">🟡 Alerta Preventiva (65-85%)</span>
                  <span class="rb-sub">Tiempo transcurrido avanzado</span>
                </div>
                <div class="rb-card red">
                  <span class="rb-num">{stats.analisis_riesgo.alto}</span>
                  <span class="rb-title">🔴 Riesgo Crítico / Vencidos</span>
                  <span class="rb-sub">Requieren prórroga o cierre</span>
                </div>
              </div>

              {#if stats.analisis_riesgo.criticos && stats.analisis_riesgo.criticos.length > 0}
                <div class="criticos-box">
                  <span class="criticos-title"><i class="bi bi-exclamation-triangle-fill"></i> Proyectos que requieren atención inmediata:</span>
                  <div class="criticos-list">
                    {#each stats.analisis_riesgo.criticos as cp}
                      <div class="critico-item">
                        <div class="ci-main">
                          <span class="ci-code">{cp.codigo}</span>
                          <span class="ci-name">{cp.nombre}</span>
                          <span class="ci-fac">{cp.facultad}</span>
                        </div>
                        <div class="ci-tag" class:vencido={cp.vencido}>
                          {#if cp.vencido}
                            <i class="bi bi-x-circle-fill"></i> Plazo vencido
                          {:else}
                            <i class="bi bi-clock-history"></i> {cp.dias_restantes} días restantes ({cp.pct_tiempo}%)
                          {/if}
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/if}

          <!-- BLOQUE DE ESTADÍSTICA DESCRIPTIVA DE PRESUPUESTOS (ESTÁNDAR UTEQ) -->
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
              <div class="chart-wrap h200">
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
              <div class="chart-wrap h300">
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
                      y: { grid: { display: false } }
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
                      backgroundColor: '#16a34a',
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
                      backgroundColor: '#d97706',
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
                      backgroundColor: '#059669',
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
              <div class="chart-wrap h180">
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

          <!-- ÚLTIMOS PROYECTOS -->
          <div class="chart-card full-card">
            <div class="card-hdr-flex">
              <h4 class="chart-title"><i class="bi bi-clock-history text-verde"></i> ÚLTIMOS PROYECTOS REGISTRADOS</h4>
              <a href="/proyectos" class="link-proys">Ver todos los proyectos →</a>
            </div>
            <table class="mini-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Nombre del Proyecto</th>
                  <th>Facultad</th>
                  <th>Período de inicio</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {#each stats.ultimos_proyectos || [] as p}
                  <tr>
                    <td><span class="code">{p.codigo}</span></td>
                    <td class="td-trunc" title={p.nombre}>{p.nombre}</td>
                    <td class="txt-sm">{p.facultad}</td>
                    <td class="txt-sm">{p.periodo}</td>
                    <td>
                      <span class="badge-est" style="background:{ESTADO_COLORES[p.estado]}18;color:{ESTADO_COLORES[p.estado]};border:1px solid {ESTADO_COLORES[p.estado]}40">
                        {ESTADO_LABEL[p.estado] || p.estado}
                      </span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>

        </div>

      <!-- ══════════════════════════════════════════════════════════════
           PESTAÑA 2: REPORTE EJECUTIVO DE PROYECTOS (OFICIAL)
      ═══════════════════════════════════════════════════════════════ -->
      {:else if activeTab === 'proyectos'}
        <div class="report-document-card">
          <div class="doc-header">
            <div class="doc-title-box">
              <h3>UNIVERSIDAD TÉCNICA ESTATAL DE QUEVEDO</h3>
              <p>Dirección de Vinculación con la Sociedad · Matriz General de Proyectos</p>
              <small>Período: {periodoFiltro ? (periodos.find(p => String(p.id_periodo) === String(periodoFiltro))?.nombre || 'Filtrado') : 'Todos los períodos'}</small>
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
                  <th>Período</th>
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
                    <td>{p.periodo}</td>
                    <td>{ESTADO_LABEL[p.estado] || p.estado}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>

      <!-- ══════════════════════════════════════════════════════════════
           PESTAÑA 3: MATRIZ DE CONVENIOS (OFICIAL)
      ═══════════════════════════════════════════════════════════════ -->
      {:else}
        <div class="report-document-card">
          <div class="doc-header">
            <div class="doc-title-box">
              <h3>UNIVERSIDAD TÉCNICA ESTATAL DE QUEVEDO</h3>
              <p>Dirección de Vinculación con la Sociedad · Registro de Convenios Institucionales</p>
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
            <p class="txt-sub">Utiliza el botón superior "Imprimir Reporte" para generar la versión física firmada.</p>
          </div>
        </div>
      {/if}

    {:else}
      <div class="loading">No se pudieron cargar los datos del reporte.</div>
    {/if}
  </main>
</div>

<style>
  .subbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 24px; background: #ffffff; border-bottom: 1px solid #e2e8f0;
  }
  .rep-actions { display: flex; align-items: center; gap: 12px; }
  .filter-group {
    display: flex; align-items: center; gap: 8px;
    background: #f8fafc; border: 1.5px solid #cbd5e1;
    border-radius: 20px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700; color: #475569;
  }
  .rep-select {
    border: none; background: transparent; font-family: inherit; font-size: 0.8rem;
    font-weight: 700; color: #1e293b; outline: none; cursor: pointer;
  }
  .btn-print {
    display: inline-flex; align-items: center; gap: 8px;
    background: #16a34a; color: #ffffff; border: none; border-radius: 20px;
    padding: 7px 18px; font-size: 0.8rem; font-weight: 800; cursor: pointer;
    transition: background 0.15s; font-family: inherit;
  }
  .btn-print:hover { background: #15803d; }

  .page-container {
    display: flex; min-height: calc(100vh - 120px); background: #f8fafc;
  }

  /* SIDEBAR DE REPORTES */
  .sidebar-reportes {
    width: 260px; background: #ffffff; border-right: 1px solid #e2e8f0;
    padding: 20px 16px; flex-shrink: 0;
  }
  .sb-box { display: flex; flex-direction: column; gap: 6px; }
  .sb-title { font-size: 0.68rem; font-weight: 800; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 8px; padding-left: 6px; }
  .sb-btn {
    display: flex; align-items: center; gap: 10px; padding: 10px 14px;
    border: none; border-radius: 10px; background: transparent;
    font-family: inherit; font-size: 0.83rem; font-weight: 700; color: #475569;
    cursor: pointer; transition: all 0.15s ease; text-align: left;
  }
  .sb-btn i { font-size: 1.1rem; color: #64748b; }
  .sb-btn:hover { background: #f1f5f9; color: #0f172a; }
  .sb-btn.active {
    background: #f0fdf4; color: #15803d; font-weight: 800;
  }
  .sb-btn.active i { color: #16a34a; }

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
    background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0;
    padding: 16px 18px; display: flex; align-items: center; gap: 14px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02); transition: transform 0.18s, box-shadow 0.18s;
  }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
  .kpi-icon {
    width: 44px; height: 44px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;
  }
  .kpi-card.verde .kpi-icon { background: #f0fdf4; color: #16a34a; }
  .kpi-card.dorado .kpi-icon { background: #fffbeb; color: #d97706; }
  .kpi-card.azul .kpi-icon { background: #f0f9ff; color: #0284c7; }
  .kpi-card.esmeralda .kpi-icon { background: #ecfdf5; color: #059669; }
  .kpi-card.naranja .kpi-icon { background: #fff7ed; color: #ea580c; }

  .kpi-body { display: flex; flex-direction: column; gap: 2px; }
  .kpi-num { font-size: 1.35rem; font-weight: 900; color: #0f172a; line-height: 1.1; }
  .kpi-label { font-size: 0.68rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }
  .kpi-sub { font-size: 0.68rem; color: #64748b; font-weight: 600; }

  /* BANNER ANALÍTICO DE RIESGO */
  .analytics-banner {
    background: #ffffff; border: 1.5px solid #86efac; border-radius: 14px;
    padding: 20px 24px; display: flex; flex-direction: column; gap: 16px;
    box-shadow: 0 4px 16px rgba(22, 163, 74, 0.06);
  }
  .ab-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
  .abh-title { display: flex; align-items: center; gap: 10px; }
  .abh-title i { font-size: 1.3rem; }
  .abh-title h4 { font-size: 1.05rem; font-weight: 800; color: #0f172a; margin: 0; }
  .badge-prob { background: #dcfce7; color: #15803d; font-size: 0.8rem; font-weight: 800; padding: 4px 12px; border-radius: 20px; }

  .risk-breakdown { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
  .rb-card {
    padding: 14px 16px; border-radius: 10px; display: flex; flex-direction: column; gap: 2px;
    border: 1px solid #e2e8f0;
  }
  .rb-card.green { background: #f0fdf4; border-color: #bbf7d0; color: #15803d; }
  .rb-card.yellow { background: #fffbeb; border-color: #fde68a; color: #b45309; }
  .rb-card.red { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }
  .rb-num { font-size: 1.3rem; font-weight: 900; }
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
  .ci-tag { font-size: 0.74rem; font-weight: 700; color: #b45309; display: flex; align-items: center; gap: 5px; }
  .ci-tag.vencido { color: #dc2626; font-weight: 800; }

  /* ESTADÍSTICA DESCRIPTIVA */
  .stats-metric-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 10px;
  }
  .smg-item {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px;
    display: flex; flex-direction: column; gap: 2px;
  }
  .smg-val { font-size: 1.15rem; font-weight: 900; color: #0f172a; }
  .smg-label { font-size: 0.7rem; font-weight: 800; color: #475569; text-transform: uppercase; }
  .smg-sub { font-size: 0.68rem; color: #64748b; }

  /* Charts Row */
  .charts-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
  .chart-card {
    background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0;
    padding: 20px 22px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); display: flex; flex-direction: column;
  }
  .chart-card.sm { min-width: 0; }
  .chart-card.lg { grid-column: span 2; }
  .chart-card.full-card { grid-column: 1 / -1; }

  .chart-title {
    font-size: 0.84rem; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.04em;
    margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
  }
  .chart-wrap { position: relative; width: 100%; }
  .h180 { height: 180px; }
  .h200 { height: 200px; }
  .h240 { height: 240px; }
  .h260 { height: 260px; }
  .h300 { height: 300px; }

  /* Estado bars */
  .estado-bars { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
  .sm-bars { gap: 6px; }
  .ebar { display: flex; align-items: center; gap: 10px; font-size: 0.75rem; }
  .ebar-label { min-width: 90px; color: #475569; font-weight: 700; }
  .ebar-track { flex: 1; height: 7px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
  .ebar-fill { height: 100%; border-radius: 4px; transition: width 0.4s; }
  .ebar-val { min-width: 50px; text-align: right; font-weight: 800; color: #0f172a; }
  .ebar-val small { font-size: 0.7rem; color: #64748b; font-weight: 600; }

  /* Mini table */
  .card-hdr-flex { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .link-proys { font-size: 0.8rem; font-weight: 800; color: #15803d; text-decoration: none; }
  .link-proys:hover { text-decoration: underline; }

  .mini-table { width: 100%; border-collapse: collapse; text-align: left; }
  .mini-table th { font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.04em; padding: 10px 14px; border-bottom: 1.5px dashed #e2e8f0; }
  .mini-table td { padding: 11px 14px; font-size: 0.84rem; border-bottom: 1px solid #f1f5f9; }
  .code { background: #f0fdf4; color: #15803d; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; font-family: monospace; }
  .td-trunc { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 700; color: #1e293b; }
  .txt-sm { font-size: 0.78rem; color: #64748b; font-weight: 600; }
  .badge-est { padding: 4px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 800; }

  /* DOCUMENTOS OFICIALES IMPRIMIBLES */
  .report-document-card {
    background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; padding: 30px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.03);
  }
  .doc-header { text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }
  .doc-title-box h3 { font-size: 1.15rem; font-weight: 900; color: #0f172a; margin: 0; }
  .doc-title-box p { font-size: 0.86rem; color: #475569; font-weight: 700; margin: 4px 0; }
  .doc-title-box small { font-size: 0.76rem; color: #64748b; }

  .doc-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }
  .doc-table th { background: #f8fafc; border: 1px solid #cbd5e1; padding: 10px 12px; font-size: 0.74rem; font-weight: 800; color: #0f172a; text-transform: uppercase; }
  .doc-table td { border: 1px solid #e2e8f0; padding: 10px 12px; color: #1e293b; }

  .text-verde { color: #16a34a; }
  .text-azul  { color: #0284c7; }
  .text-dorado { color: #d97706; }
  .mb-16 { margin-bottom: 16px; }
  .txt-sub { font-size: 0.82rem; color: #64748b; }

  @media (max-width: 992px) {
    .chart-card.lg { grid-column: span 1; }
    .page-container { flex-direction: column; }
    .sidebar-reportes { width: 100%; border-right: none; border-bottom: 1px solid #e2e8f0; }
  }
  @media print {
    .subbar, .sidebar-reportes, .btn-print, .rep-actions { display: none !important; }
    .page-container { background: #ffffff !important; }
    .content-reportes { padding: 0 !important; }
    .rep-wrap { padding: 0 !important; gap: 10px !important; }
    .chart-card, .report-document-card { break-inside: avoid; border: 1px solid #ddd !important; box-shadow: none !important; }
  }
</style>
