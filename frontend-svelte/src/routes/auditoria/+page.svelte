<script>
  import { onMount } from 'svelte';
  import { toast } from '$lib/toast';

  // Estados de datos
  let eventos = $state([]);
  let total = $state(0);
  let page = $state(1);
  let pageSize = $state(15);
  let cargando = $state(true);

  // KPIs
  let kpis = $state({
    total: 0,
    creaciones: 0,
    modificaciones: 0,
    eliminaciones: 0
  });

  // Filtros
  let filtroQ = $state('');
  let filtroEntidad = $state('');
  let filtroAccion = $state('');

  // Verificación criptográfica
  let verificando = $state(false);
  let resultadoVerificacion = $state(null);

  // Modal de evidencia digital
  let eventoSeleccionado = $state(null);
  let modalAbierto = $state(false);
  let jsonCopiado = $state(false);
  let hashCopiado = $state('');

  let debounceTimer = null;

  async function cargarEventos(resetPage = false) {
    if (resetPage) page = 1;
    cargando = true;
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        q: filtroQ.trim(),
        entidad: filtroEntidad,
        accion: filtroAccion,
      });
      const res = await fetch(`/api/auditoria/listar/?${params.toString()}`, {
        credentials: 'include'
      });
      if (!res.ok) {
        throw new Error('Error al cargar la bitácora de auditoría');
      }
      const data = await res.json();
      eventos = data.results || [];
      total = data.total || 0;
      if (data.kpis) {
        kpis = data.kpis;
      }
    } catch (e) {
      toast.error(e.message || 'Error de conexión');
    } finally {
      cargando = false;
    }
  }

  function onInputSearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      cargarEventos(true);
    }, 300);
  }

  async function ejecutarVerificacionForense() {
    verificando = true;
    resultadoVerificacion = null;
    try {
      const res = await fetch('/api/auditoria/verificar/', {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Error al consultar el servicio de verificación');
      const data = await res.json();
      resultadoVerificacion = data;
      if (data.valido) {
        toast.success(`Cadena 100% íntegra (${data.total_eventos} bloques validados)`);
      } else {
        toast.error('¡Alerta de Seguridad! Se detectaron inconsistencias en la cadena criptográfica');
      }
    } catch (e) {
      toast.error(e.message || 'Fallo en la verificación criptográfica');
    } finally {
      verificando = false;
    }
  }

  function abrirModalEvidencia(ev) {
    eventoSeleccionado = ev;
    modalAbierto = true;
    jsonCopiado = false;
    hashCopiado = '';
  }

  function cerrarModal() {
    modalAbierto = false;
    eventoSeleccionado = null;
  }

  async function copiarAlPortapapeles(texto, tipo = 'json') {
    try {
      await navigator.clipboard.writeText(texto);
      if (tipo === 'json') {
        jsonCopiado = true;
        setTimeout(() => jsonCopiado = false, 2000);
      } else {
        hashCopiado = tipo;
        setTimeout(() => hashCopiado = '', 2000);
      }
      toast.success('Copiado al portapapeles');
    } catch {
      toast.error('No se pudo copiar');
    }
  }

  function getBadgeClassAccion(accion) {
    if (!accion) return 'badge-neutral';
    const acc = accion.toUpperCase();
    if (acc.includes('CREACION') || acc.includes('CREAR')) return 'badge-success';
    if (acc.includes('MODIFICACION') || acc.includes('EDIT')) return 'badge-warning';
    if (acc.includes('ELIMINACION') || acc.includes('DELETE')) return 'badge-danger';
    if (acc.includes('DOC') || acc.includes('SUBIDA')) return 'badge-info';
    if (acc.includes('APROB') || acc.includes('ESTADO')) return 'badge-primary';
    return 'badge-neutral';
  }

  function getBadgeClassEntidad(entidad) {
    if (!entidad) return 'badge-neutral';
    const ent = entidad.toUpperCase();
    if (ent === 'PROYECTO') return 'entidad-proyecto';
    if (ent === 'CONVENIO') return 'entidad-convenio';
    if (ent === 'DOCUMENTO') return 'entidad-documento';
    if (ent === 'USUARIO') return 'entidad-usuario';
    if (ent === 'ENTIDAD') return 'entidad-cooperante';
    return 'badge-neutral';
  }

  function totalPaginas() {
    return Math.ceil(total / pageSize) || 1;
  }

  function cambiarPagina(nueva) {
    if (nueva >= 1 && nueva <= totalPaginas() && nueva !== page) {
      page = nueva;
      cargarEventos();
    }
  }

  function limpiarFiltros() {
    filtroQ = '';
    filtroEntidad = '';
    filtroAccion = '';
    cargarEventos(true);
  }

  onMount(() => {
    cargarEventos();
    ejecutarVerificacionForense();
  });
</script>

<svelte:head>
  <title>Auditoría y Trazabilidad Forense — SGV UTEQ</title>
</svelte:head>

<!-- SUBBAR / BREADCRUMB -->
<div class="sga-subbar">
  <div class="sga-subbar-inner">
    <nav class="breadcrumb">
      <a href="/dashboard"><i class="bi bi-house-door-fill"></i> Inicio</a>
      <span class="sep">/</span>
      <a href="/configuracion">Configuración</a>
      <span class="sep">/</span>
      <span class="current">Auditoría y Trazabilidad Forense</span>
    </nav>
  </div>
</div>

<div class="auditoria-page">
  <!-- ENCABEZADO PRINCIPAL -->
  <div class="page-header">
    <div class="header-titles">
      <h1 class="page-title">
        <i class="bi bi-shield-lock-fill"></i> Módulo de Auditoría y Trazabilidad Forense
      </h1>
      <p class="page-subtitle">
        Estándar UTEQ & CACES (Módulo G) • Registro inmutable con encadenamiento criptográfico SHA-256
      </p>
    </div>
    <div class="header-actions">
      <button
        class="btn-verificar"
        onclick={ejecutarVerificacionForense}
        disabled={verificando}
      >
        <i class="bi {verificando ? 'bi-arrow-repeat spin' : 'bi-shield-check'}"></i>
        <span>{verificando ? 'Auditando bloques...' : 'Verificar Cadena SHA-256'}</span>
      </button>
    </div>
  </div>

  <!-- PANEL DE VERIFICACIÓN CRIPTOGRÁFICA -->
  {#if resultadoVerificacion}
    <div class="forensic-banner {resultadoVerificacion.valido ? 'banner-valid' : 'banner-invalid'}">
      <div class="banner-icon">
        <i class="bi {resultadoVerificacion.valido ? 'bi-shield-fill-check' : 'bi-shield-fill-x'}"></i>
      </div>
      <div class="banner-content">
        <div class="banner-title">
          {resultadoVerificacion.valido
            ? 'CADENA CRIPTOGRÁFICA 100% ÍNTEGRA Y LIBRE DE MANIPULACIONES'
            : '¡ALERTA DE SEGURIDAD: INCONSISTENCIA O ALTERACIÓN DETECTADA!'}
        </div>
        <div class="banner-desc">
          {#if resultadoVerificacion.valido}
            Se han verificado <strong>{resultadoVerificacion.total_eventos} eslabones</strong> consecutivos mediante hashing SHA-256. 
            Todos los bloques coinciden con su huella padre anterior.
            <span class="banner-hash" title="Último Hash de la Cadena">
              <i class="bi bi-fingerprint"></i> Último Hash: <code>{resultadoVerificacion.ultimo_hash}</code>
            </span>
          {:else}
            La auditoría forense detectó manipulación directa en la base de datos o ruptura de la cadena en 
            <strong>{resultadoVerificacion.errores?.length || 0} registro(s)</strong>.
            <div class="error-list">
              {#each resultadoVerificacion.errores as err}
                <div class="error-item">
                  • Registro #{err.id_bitacora}: {err.error}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
      <div class="banner-status-badge">
        {resultadoVerificacion.valido ? 'VERIFICADO' : 'COMPROMETIDO'}
      </div>
    </div>
  {/if}

  <!-- TARJETAS KPIS DE GOBERNANZA -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-icon icon-blue"><i class="bi bi-journal-code"></i></div>
      <div class="kpi-info">
        <span class="kpi-value">{kpis.total}</span>
        <span class="kpi-label">Total de Eventos Forenses</span>
      </div>
    </div>

    <div class="kpi-card">
      <div class="kpi-icon icon-green"><i class="bi bi-plus-circle-fill"></i></div>
      <div class="kpi-info">
        <span class="kpi-value">{kpis.creaciones}</span>
        <span class="kpi-label">Operaciones de Creación</span>
      </div>
    </div>

    <div class="kpi-card">
      <div class="kpi-icon icon-amber"><i class="bi bi-pencil-square"></i></div>
      <div class="kpi-info">
        <span class="kpi-value">{kpis.modificaciones}</span>
        <span class="kpi-label">Modificaciones de Datos</span>
      </div>
    </div>

    <div class="kpi-card">
      <div class="kpi-icon icon-red"><i class="bi bi-trash3-fill"></i></div>
      <div class="kpi-info">
        <span class="kpi-value">{kpis.eliminaciones}</span>
        <span class="kpi-label">Eliminaciones Críticas</span>
      </div>
    </div>
  </div>

  <!-- BARRA DE FILTROS -->
  <div class="filters-card">
    <div class="filters-row">
      <div class="search-box">
        <i class="bi bi-search search-icon"></i>
        <input
          type="text"
          placeholder="Buscar por usuario, IP o contenido..."
          bind:value={filtroQ}
          oninput={onInputSearch}
        />
        {#if filtroQ}
          <button class="clear-search" onclick={() => { filtroQ = ''; cargarEventos(true); }}>
            <i class="bi bi-x-circle-fill"></i>
          </button>
        {/if}
      </div>

      <div class="filter-select">
        <label for="filtro-entidad"><i class="bi bi-folder2-open"></i> Entidad:</label>
        <select id="filtro-entidad" bind:value={filtroEntidad} onchange={() => cargarEventos(true)}>
          <option value="">Todas las entidades</option>
          <option value="PROYECTO">PROYECTO</option>
          <option value="CONVENIO">CONVENIO</option>
          <option value="DOCUMENTO">DOCUMENTO</option>
          <option value="USUARIO">USUARIO</option>
          <option value="ENTIDAD">ENTIDAD COOPERANTE</option>
        </select>
      </div>

      <div class="filter-select">
        <label for="filtro-accion"><i class="bi bi-lightning-charge"></i> Tipo de Acción:</label>
        <select id="filtro-accion" bind:value={filtroAccion} onchange={() => cargarEventos(true)}>
          <option value="">Todas las acciones</option>
          <option value="CREACION">Creaciones</option>
          <option value="MODIFICACION">Modificaciones</option>
          <option value="ELIMINACION">Eliminaciones</option>
          <option value="SUBIDA_DOC">Subida de Documentos</option>
        </select>
      </div>

      {#if filtroQ || filtroEntidad || filtroAccion}
        <button class="btn-reset" onclick={limpiarFiltros} title="Limpiar todos los filtros">
          <i class="bi bi-arrow-counterclockwise"></i> Limpiar
        </button>
      {/if}
    </div>
  </div>

  <!-- TABLA DE EVENTOS -->
  <div class="table-card">
    {#if cargando}
      <div class="loading-state">
        <i class="bi bi-arrow-repeat spin"></i>
        <span>Consultando bitácora criptográfica...</span>
      </div>
    {:else if eventos.length === 0}
      <div class="empty-state">
        <i class="bi bi-shield-slash"></i>
        <h3>No se encontraron eventos en la bitácora</h3>
        <p>No hay registros de auditoría que coincidan con los criterios de búsqueda.</p>
        {#if filtroQ || filtroEntidad || filtroAccion}
          <button class="btn-secondary" onclick={limpiarFiltros}>Restablecer filtros</button>
        {/if}
      </div>
    {:else}
      <div class="table-responsive">
        <table class="sga-table">
          <thead>
            <tr>
              <th style="width: 70px;">ID</th>
              <th style="width: 160px;">Sello Temporal</th>
              <th style="width: 140px;">Entidad</th>
              <th style="width: 190px;">Acción Forense</th>
              <th style="width: 160px;">Operador</th>
              <th style="width: 120px;">IP Origen</th>
              <th>Huella Criptográfica SHA-256</th>
              <th style="width: 110px; text-align: center;">Acción</th>
            </tr>
          </thead>
          <tbody>
            {#each eventos as ev}
              <tr>
                <td class="cell-id">#{ev.id}</td>
                <td class="cell-time">
                  <i class="bi bi-clock-history"></i> {ev.creado_en}
                </td>
                <td>
                  <span class="badge {getBadgeClassEntidad(ev.entidad)}">
                    {ev.entidad} #{ev.id_registro}
                  </span>
                </td>
                <td>
                  <span class="badge {getBadgeClassAccion(ev.accion)}">
                    {ev.accion}
                  </span>
                </td>
                <td class="cell-user">
                  <i class="bi bi-person-badge"></i>
                  <span>{ev.username}</span>
                </td>
                <td class="cell-ip">
                  <code>{ev.ip_origen}</code>
                </td>
                <td class="cell-hash">
                  <div class="hash-preview" title="SHA-256: {ev.hash_actual}">
                    <i class="bi bi-key-fill"></i>
                    <code>{ev.hash_actual.slice(0, 8)}...{ev.hash_actual.slice(-8)}</code>
                    <button
                      class="btn-copy-sm"
                      title="Copiar Hash Completo"
                      onclick={() => copiarAlPortapapeles(ev.hash_actual, 'hash-' + ev.id)}
                    >
                      <i class="bi {hashCopiado === 'hash-' + ev.id ? 'bi-check-lg text-green' : 'bi-copy'}"></i>
                    </button>
                  </div>
                </td>
                <td style="text-align: center;">
                  <button
                    class="btn-evidence"
                    title="Inspeccionar Evidencia Digital"
                    onclick={() => abrirModalEvidencia(ev)}
                  >
                    <i class="bi bi-search"></i> Inspeccionar
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- PAGINACIÓN -->
      <div class="pagination-footer">
        <div class="pagination-info">
          Mostrando <strong>{(page - 1) * pageSize + 1}</strong> a <strong>{Math.min(page * pageSize, total)}</strong> de <strong>{total}</strong> eventos
        </div>
        <div class="pagination-controls">
          <button
            class="btn-page"
            disabled={page <= 1}
            onclick={() => cambiarPagina(page - 1)}
          >
            <i class="bi bi-chevron-left"></i> Anterior
          </button>
          
          <span class="page-current">
            Página {page} de {totalPaginas()}
          </span>

          <button
            class="btn-page"
            disabled={page >= totalPaginas()}
            onclick={() => cambiarPagina(page + 1)}
          >
            Siguiente <i class="bi bi-chevron-right"></i>
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<!-- MODAL DE INSPECCIÓN FORENSE (EVIDENCIA DIGITAL) -->
{#if modalAbierto && eventoSeleccionado}
  <div class="modal-overlay" onclick={cerrarModal} role="presentation">
    <div class="modal-dialog forensic-modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <div class="modal-header">
        <div class="modal-title-wrap">
          <div class="modal-icon"><i class="bi bi-fingerprint"></i></div>
          <div>
            <h3 class="modal-title">Inspección Forense de Evidencia Digital</h3>
            <p class="modal-subtitle">Registro de Auditoría #{eventoSeleccionado.id} • Cadena Inmutable SHA-256</p>
          </div>
        </div>
        <button class="btn-close-modal" onclick={cerrarModal} title="Cerrar"><i class="bi bi-x-lg"></i></button>
      </div>

      <div class="modal-body">
        <!-- METADATOS DE CABECERA -->
        <div class="meta-grid">
          <div class="meta-item">
            <span class="meta-label">Entidad Afectada</span>
            <span class="meta-value highlight">{eventoSeleccionado.entidad} #{eventoSeleccionado.id_registro}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Acción Registrada</span>
            <span class="meta-value"><span class="badge {getBadgeClassAccion(eventoSeleccionado.accion)}">{eventoSeleccionado.accion}</span></span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Operador Responsable</span>
            <span class="meta-value">{eventoSeleccionado.username} (ID: {eventoSeleccionado.usuario_id || 'Sistema'})</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Dirección IP de Red</span>
            <span class="meta-value"><code>{eventoSeleccionado.ip_origen}</code></span>
          </div>
          <div class="meta-item full">
            <span class="meta-label">Sello de Tiempo (Timestamp UTC/Local)</span>
            <span class="meta-value"><i class="bi bi-calendar3"></i> {eventoSeleccionado.creado_en}</span>
          </div>
        </div>

        <!-- ENCADENAMIENTO CRIPTOGRÁFICO -->
        <div class="crypto-box">
          <div class="crypto-hdr"><i class="bi bi-link-45deg"></i> Eslabón Criptográfico (Proof of Chain)</div>
          <div class="crypto-row">
            <div class="crypto-label">Hash Anterior (Padre):</div>
            <div class="crypto-code-wrap">
              <code>{eventoSeleccionado.hash_anterior}</code>
              <button class="btn-copy-xs" onclick={() => copiarAlPortapapeles(eventoSeleccionado.hash_anterior, 'h-ant')}>
                <i class="bi {hashCopiado === 'h-ant' ? 'bi-check-lg text-green' : 'bi-copy'}"></i>
              </button>
            </div>
          </div>
          <div class="crypto-row">
            <div class="crypto-label">Hash Actual (SHA-256):</div>
            <div class="crypto-code-wrap active-hash">
              <code>{eventoSeleccionado.hash_actual}</code>
              <button class="btn-copy-xs" onclick={() => copiarAlPortapapeles(eventoSeleccionado.hash_actual, 'h-act')}>
                <i class="bi {hashCopiado === 'h-act' ? 'bi-check-lg text-green' : 'bi-copy'}"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- PAYLOAD JSON FORMATEADO -->
        <div class="payload-section">
          <div class="payload-header">
            <span class="payload-title"><i class="bi bi-code-square"></i> Payload de la Transacción (Detalles JSON)</span>
            <button
              class="btn-copy-payload"
              onclick={() => copiarAlPortapapeles(JSON.stringify(eventoSeleccionado.detalles, null, 2), 'json')}
            >
              <i class="bi {jsonCopiado ? 'bi-check2' : 'bi-clipboard'}"></i>
              <span>{jsonCopiado ? '¡Copiado!' : 'Copiar JSON'}</span>
            </button>
          </div>
          <pre class="json-viewer"><code>{JSON.stringify(eventoSeleccionado.detalles, null, 2)}</code></pre>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-modal-close" onclick={cerrarModal}>
          Cerrar Inspección
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* ── LAYOUT & GENERAL ────────────────────────────────────────── */
  .sga-subbar {
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 24px;
  }
  .sga-subbar-inner {
    max-width: 1400px;
    margin: 0 auto;
  }
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: #64748b;
  }
  .breadcrumb a {
    color: #0f172a;
    text-decoration: none;
    font-weight: 500;
  }
  .breadcrumb a:hover {
    color: #1b7505;
  }
  .breadcrumb .sep {
    color: #cbd5e1;
  }
  .breadcrumb .current {
    color: #1b7505;
    font-weight: 600;
  }

  .auditoria-page {
    max-width: 1400px;
    margin: 20px auto 40px;
    padding: 0 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  /* ── HEADER ─────────────────────────────────────────────────── */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  .page-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .page-title i {
    color: #1b7505;
  }
  .page-subtitle {
    font-size: 0.875rem;
    color: #64748b;
    margin: 4px 0 0;
  }
  .btn-verificar {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #1b7505;
    color: #fff;
    border: none;
    padding: 10px 18px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(27, 117, 5, 0.2);
    transition: all 0.2s;
  }
  .btn-verificar:hover:not(:disabled) {
    background: #155c04;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(27, 117, 5, 0.3);
  }
  .btn-verificar:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  /* ── BANNER FORENSE CRIPTOGRÁFICO ────────────────────────────── */
  .forensic-banner {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px 20px;
    border-radius: 12px;
    border: 1px solid;
    position: relative;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }
  .banner-valid {
    background: #f0fdf4;
    border-color: #86efac;
    color: #14532d;
  }
  .banner-invalid {
    background: #fef2f2;
    border-color: #fca5a5;
    color: #7f1d1d;
  }
  .banner-icon {
    font-size: 2rem;
    line-height: 1;
  }
  .banner-valid .banner-icon { color: #16a34a; }
  .banner-invalid .banner-icon { color: #dc2626; }
  .banner-content {
    flex: 1;
  }
  .banner-title {
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 4px;
    letter-spacing: 0.3px;
  }
  .banner-desc {
    font-size: 0.875rem;
    line-height: 1.4;
  }
  .banner-hash {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    padding: 3px 8px;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 6px;
    font-size: 0.8rem;
  }
  .banner-hash code {
    font-family: monospace;
    font-weight: 600;
  }
  .banner-status-badge {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.5px;
  }
  .banner-valid .banner-status-badge {
    background: #22c55e;
    color: #fff;
  }
  .banner-invalid .banner-status-badge {
    background: #ef4444;
    color: #fff;
  }
  .error-list {
    margin-top: 8px;
    font-size: 0.825rem;
    font-family: monospace;
    background: #fff;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #fecaca;
  }

  /* ── KPIS ───────────────────────────────────────────────────── */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
  }
  .kpi-card {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
  .kpi-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
  }
  .icon-blue  { background: #eff6ff; color: #2563eb; }
  .icon-green { background: #f0fdf4; color: #16a34a; }
  .icon-amber { background: #fffbeb; color: #d97706; }
  .icon-red   { background: #fef2f2; color: #dc2626; }
  .kpi-info {
    display: flex;
    flex-direction: column;
  }
  .kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
  }
  .kpi-label {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
    margin-top: 2px;
  }

  /* ── FILTROS ─────────────────────────────────────────────────── */
  .filters-card {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
  .filters-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
  }
  .search-box {
    position: relative;
    flex: 1;
    min-width: 260px;
  }
  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
    font-size: 0.95rem;
  }
  .search-box input {
    width: 100%;
    padding: 9px 36px 9px 36px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.875rem;
    background: #f8fafc;
    transition: all 0.2s;
  }
  .search-box input:focus {
    outline: none;
    border-color: #1b7505;
    background: #fff;
    box-shadow: 0 0 0 3px rgba(27, 117, 5, 0.1);
  }
  .clear-search {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.95rem;
  }
  .filter-select {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: #475569;
    font-weight: 500;
  }
  .filter-select select {
    padding: 9px 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.875rem;
    background: #fff;
    color: #0f172a;
    cursor: pointer;
  }
  .filter-select select:focus {
    outline: none;
    border-color: #1b7505;
  }
  .btn-reset {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-reset:hover {
    background: #e2e8f0;
  }

  /* ── TABLA DE BITÁCORA ───────────────────────────────────────── */
  .table-card {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
  .table-responsive {
    overflow-x: auto;
  }
  .sga-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    text-align: left;
  }
  .sga-table th {
    background: #f8fafc;
    color: #475569;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
  }
  .sga-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
    vertical-align: middle;
  }
  .sga-table tbody tr:hover {
    background: #f8fafc;
  }
  .cell-id {
    font-weight: 700;
    color: #64748b;
  }
  .cell-time {
    font-size: 0.8rem;
    color: #64748b;
    white-space: nowrap;
  }
  .cell-user {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
  }
  .cell-ip code {
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.8rem;
    color: #475569;
  }
  .hash-preview {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 4px 8px;
    border-radius: 6px;
    width: fit-content;
    font-size: 0.8rem;
  }
  .hash-preview i { color: #94a3b8; }
  .hash-preview code {
    color: #0f172a;
    font-family: monospace;
    font-weight: 600;
  }
  .btn-copy-sm {
    background: none;
    border: none;
    color: #64748b;
    cursor: pointer;
    padding: 2px;
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
  }
  .btn-copy-sm:hover { color: #1b7505; }
  .btn-evidence {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 0.775rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-evidence:hover {
    background: #1b7505;
    color: #fff;
    border-color: #1b7505;
  }

  /* BADGES */
  .badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.3px;
  }
  .badge-success { background: #dcfce7; color: #166534; }
  .badge-warning { background: #fef3c7; color: #92400e; }
  .badge-danger  { background: #fee2e2; color: #991b1b; }
  .badge-info    { background: #e0f2fe; color: #075985; }
  .badge-primary { background: #e0e7ff; color: #3730a3; }
  .badge-neutral { background: #f1f5f9; color: #475569; }

  .entidad-proyecto   { background: #ede9fe; color: #5b21b6; }
  .entidad-convenio   { background: #ffe4e6; color: #9f1239; }
  .entidad-documento  { background: #fef9c3; color: #854d0e; }
  .entidad-usuario    { background: #f3e8ff; color: #6b21a8; }
  .entidad-cooperante { background: #ffedd5; color: #9a3412; }

  /* ── PAGINACIÓN ─────────────────────────────────────────────── */
  .pagination-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 0.85rem;
    color: #64748b;
  }
  .pagination-controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .btn-page {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border: 1px solid #cbd5e1;
    background: #fff;
    color: #334155;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-page:hover:not(:disabled) {
    background: #f1f5f9;
  }
  .btn-page:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .page-current {
    font-weight: 600;
    color: #0f172a;
  }

  /* ── MODAL DE INSPECCIÓN ────────────────────────────────────── */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 16px;
  }
  .forensic-modal {
    background: #fff;
    border-radius: 16px;
    width: 100%;
    max-width: 760px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    overflow: hidden;
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 24px;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
  }
  .modal-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .modal-icon {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: #dcfce7;
    color: #166534;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
  }
  .modal-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }
  .modal-subtitle {
    font-size: 0.8rem;
    color: #64748b;
    margin: 2px 0 0;
  }
  .btn-close-modal {
    background: none;
    border: none;
    font-size: 1.1rem;
    color: #94a3b8;
    cursor: pointer;
    padding: 4px;
  }
  .btn-close-modal:hover { color: #0f172a; }

  .modal-body {
    padding: 20px 24px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  /* METADATOS */
  .meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    background: #f8fafc;
    padding: 14px 16px;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
  }
  .meta-item.full {
    grid-column: span 2;
  }
  .meta-label {
    display: block;
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 2px;
  }
  .meta-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: #0f172a;
  }
  .meta-value.highlight {
    color: #1b7505;
  }

  /* CRIPTO BOX */
  .crypto-box {
    background: #0f172a;
    color: #f8fafc;
    padding: 14px 18px;
    border-radius: 10px;
    font-size: 0.825rem;
  }
  .crypto-hdr {
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.5px;
  }
  .crypto-row {
    margin-bottom: 8px;
  }
  .crypto-row:last-child {
    margin-bottom: 0;
  }
  .crypto-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-bottom: 2px;
  }
  .crypto-code-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255, 255, 255, 0.06);
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .crypto-code-wrap.active-hash {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.3);
  }
  .crypto-code-wrap.active-hash code {
    color: #4ade80;
  }
  .crypto-code-wrap code {
    font-family: monospace;
    font-size: 0.775rem;
    word-break: break-all;
    color: #cbd5e1;
  }
  .btn-copy-xs {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.85rem;
    padding: 2px 6px;
    margin-left: 8px;
  }
  .btn-copy-xs:hover { color: #fff; }

  /* PAYLOAD */
  .payload-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .payload-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .payload-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #334155;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .btn-copy-payload {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
    cursor: pointer;
  }
  .btn-copy-payload:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
  .json-viewer {
    background: #1e293b;
    color: #e2e8f0;
    padding: 14px 16px;
    border-radius: 8px;
    font-size: 0.825rem;
    font-family: monospace;
    overflow-x: auto;
    max-height: 240px;
    margin: 0;
  }

  .modal-footer {
    padding: 14px 24px;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
    background: #f8fafc;
  }
  .btn-modal-close {
    background: #334155;
    color: #fff;
    border: none;
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-modal-close:hover {
    background: #1e293b;
  }

  .text-green { color: #22c55e !important; }
  .spin { animation: spin 1s linear infinite; display: inline-block; }
  @keyframes spin { 100% { transform: rotate(360deg); } }

  .loading-state, .empty-state {
    padding: 48px 24px;
    text-align: center;
    color: #64748b;
  }
  .loading-state i, .empty-state i {
    font-size: 2.5rem;
    margin-bottom: 12px;
    display: block;
  }
  .empty-state h3 {
    font-size: 1.1rem;
    color: #0f172a;
    margin: 0 0 6px;
  }
  .btn-secondary {
    margin-top: 12px;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
  }
</style>
