<script>
  import { onMount } from 'svelte';
  import { toast } from '$lib/toast';
  import Pagination from '$lib/Pagination.svelte';

  // Estados de datos
  let eventos = $state([]);
  let total = $state(0);
  let page = $state(1);
  let pageSize = $state(10);
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
    if (!accion) return 'neutral';
    const acc = accion.toUpperCase();
    if (acc.includes('CREACION') || acc.includes('CREAR')) return 'verde';
    if (acc.includes('MODIFICACION') || acc.includes('EDIT')) return 'amarillo';
    if (acc.includes('ELIMINACION') || acc.includes('DELETE')) return 'rojo';
    if (acc.includes('DOC') || acc.includes('SUBIDA')) return 'azul';
    if (acc.includes('APROB') || acc.includes('ESTADO')) return 'morado';
    return 'neutral';
  }

  function getBadgeClassEntidad(entidad) {
    if (!entidad) return 'ent-neutral';
    const ent = entidad.toUpperCase();
    if (ent === 'PROYECTO') return 'ent-proyecto';
    if (ent === 'CONVENIO') return 'ent-convenio';
    if (ent === 'DOCUMENTO') return 'ent-documento';
    if (ent === 'USUARIO') return 'ent-usuario';
    if (ent === 'ENTIDAD') return 'ent-cooperante';
    return 'ent-neutral';
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

<!-- SUBBAR SUPERIOR (OBLIGATORIO PARA GRID AREA DE SGV) -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard"><i class="bi bi-house-door-fill"></i> Inicio</a>
    <span class="sep">/</span>
    <a href="/configuracion">Configuración</a>
    <span class="sep">/</span>
    <span class="current">Auditoría Forense</span>
  </nav>

  <button
    type="button"
    class="btn-verificar"
    onclick={ejecutarVerificacionForense}
    disabled={verificando}
  >
    <i class="bi {verificando ? 'bi-arrow-repeat spin' : 'bi-shield-check'}"></i>
    <span>{verificando ? 'Auditando...' : 'Verificar Cadena SHA-256'}</span>
  </button>
</div>

<!-- CONTENEDOR PRINCIPAL DE PÁGINA -->
<div class="page-wrap">
  
  <!-- CABECERA -->
  <div class="page-top-header">
    <div>
      <h2 class="page-title"><i class="bi bi-shield-lock-fill"></i> Auditoría y Trazabilidad Forense</h2>
      <p class="page-sub">Estándar UTEQ & CACES (Módulo G) • Registro inmutable con encadenamiento SHA-256</p>
    </div>
  </div>

  <!-- BANNER DE VERIFICACIÓN CRIPTOGRÁFICA FORENSE -->
  {#if resultadoVerificacion}
    <div class="forensic-banner {resultadoVerificacion.valido ? 'banner-ok' : 'banner-err'}">
      <div class="fb-icon">
        <i class="bi {resultadoVerificacion.valido ? 'bi-shield-fill-check' : 'bi-shield-fill-x'}"></i>
      </div>
      <div class="fb-body">
        <div class="fb-title">
          {resultadoVerificacion.valido
            ? 'CADENA CRIPTOGRÁFICA ÍNTEGRA (100% INALTERADA)'
            : '¡ALERTA: INCONSISTENCIA O MANIPULACIÓN DETECTADA!'}
        </div>
        <div class="fb-text">
          {#if resultadoVerificacion.valido}
            Se verificaron con éxito <strong>{resultadoVerificacion.total_eventos} bloques</strong> consecutivos.
            <span class="fb-hash">
              <i class="bi bi-key-fill"></i> Último Hash: <code>{resultadoVerificacion.ultimo_hash}</code>
            </span>
          {:else}
            Se detectó alteración manual o ruptura en la cadena en 
            <strong>{resultadoVerificacion.errores?.length || 0} registro(s)</strong>.
          {/if}
        </div>
      </div>
      <div class="fb-badge">
        {resultadoVerificacion.valido ? 'VÁLIDO' : 'FALLA'}
      </div>
    </div>
  {/if}

  <!-- KPIS DE GOBERNANZA -->
  <div class="kpis-banner">
    <div class="kpi-mini-card">
      <div class="kmc-icon azul"><i class="bi bi-journal-code"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{kpis.total}</span>
        <span class="kmc-label">Total Eventos</span>
      </div>
    </div>

    <div class="kpi-mini-card">
      <div class="kmc-icon verde"><i class="bi bi-plus-circle-fill"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{kpis.creaciones}</span>
        <span class="kmc-label">Creaciones</span>
      </div>
    </div>

    <div class="kpi-mini-card">
      <div class="kmc-icon amarillo"><i class="bi bi-pencil-square"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{kpis.modificaciones}</span>
        <span class="kmc-label">Modificaciones</span>
      </div>
    </div>

    <div class="kpi-mini-card">
      <div class="kmc-icon rojo"><i class="bi bi-trash3-fill"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{kpis.eliminaciones}</span>
        <span class="kmc-label">Eliminaciones</span>
      </div>
    </div>
  </div>

  <!-- BARRA DE FILTROS -->
  <div class="filtros-bar">
    <div class="search-input-wrap">
      <i class="bi bi-search search-ico"></i>
      <input
        type="text"
        placeholder="Buscar por usuario, IP o contenido..."
        bind:value={filtroQ}
        oninput={onInputSearch}
      />
      {#if filtroQ}
        <button class="clear-btn" onclick={() => { filtroQ = ''; cargarEventos(true); }}>
          <i class="bi bi-x-circle-fill"></i>
        </button>
      {/if}
    </div>

    <div class="select-group">
      <label for="f-entidad">Entidad:</label>
      <select id="f-entidad" bind:value={filtroEntidad} onchange={() => cargarEventos(true)}>
        <option value="">Todas</option>
        <option value="PROYECTO">PROYECTO</option>
        <option value="CONVENIO">CONVENIO</option>
        <option value="DOCUMENTO">DOCUMENTO</option>
        <option value="USUARIO">USUARIO</option>
        <option value="ENTIDAD">ENTIDAD</option>
      </select>
    </div>

    <div class="select-group">
      <label for="f-accion">Acción:</label>
      <select id="f-accion" bind:value={filtroAccion} onchange={() => cargarEventos(true)}>
        <option value="">Todas</option>
        <option value="CREACION">Creaciones</option>
        <option value="MODIFICACION">Modificaciones</option>
        <option value="ELIMINACION">Eliminaciones</option>
        <option value="SUBIDA_DOC">Documentos</option>
      </select>
    </div>

    {#if filtroQ || filtroEntidad || filtroAccion}
      <button class="btn-limpiar" onclick={limpiarFiltros} title="Limpiar filtros">
        <i class="bi bi-arrow-counterclockwise"></i> Limpiar
      </button>
    {/if}
  </div>

  <!-- TABLA DE AUDITORÍA FORENSE -->
  <div class="table-wrap">
    {#if cargando}
      <div class="loading-box">
        <i class="bi bi-arrow-repeat spin"></i>
        <span>Consultando bitácora forense...</span>
      </div>
    {:else if eventos.length === 0}
      <div class="empty-box">
        <i class="bi bi-shield-slash"></i>
        <h4>No se encontraron registros de auditoría</h4>
        <p>No hay eventos que coincidan con los filtros aplicados.</p>
        {#if filtroQ || filtroEntidad || filtroAccion}
          <button class="btn-limpiar" onclick={limpiarFiltros}>Restablecer filtros</button>
        {/if}
      </div>
    {:else}
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th style="width: 60px;">ID</th>
              <th style="width: 140px;">Fecha / Hora</th>
              <th style="width: 130px;">Entidad</th>
              <th style="width: 170px;">Acción Forense</th>
              <th style="width: 130px;">Operador</th>
              <th style="width: 110px;">IP Origen</th>
              <th>Huella Criptográfica SHA-256</th>
              <th style="width: 90px; text-align: center;">Acción</th>
            </tr>
          </thead>
          <tbody>
            {#each eventos as ev}
              <tr>
                <td class="col-id">#{ev.id}</td>
                <td class="col-time">{ev.creado_en}</td>
                <td>
                  <span class="ent-tag {getBadgeClassEntidad(ev.entidad)}">
                    {ev.entidad} #{ev.id_registro}
                  </span>
                </td>
                <td>
                  <span class="acc-tag {getBadgeClassAccion(ev.accion)}">
                    {ev.accion}
                  </span>
                </td>
                <td class="col-user">
                  <i class="bi bi-person-fill user-ico"></i>
                  <span>{ev.username}</span>
                </td>
                <td class="col-ip">
                  <code>{ev.ip_origen}</code>
                </td>
                <td class="col-hash">
                  <div class="hash-tag" title="SHA-256: {ev.hash_actual}">
                    <i class="bi bi-fingerprint"></i>
                    <code>{ev.hash_actual.slice(0, 8)}...{ev.hash_actual.slice(-6)}</code>
                    <button
                      type="button"
                      class="btn-copy"
                      title="Copiar Hash Completo"
                      onclick={() => copiarAlPortapapeles(ev.hash_actual, 'hash-' + ev.id)}
                    >
                      <i class="bi {hashCopiado === 'hash-' + ev.id ? 'bi-check-lg' : 'bi-copy'}"></i>
                    </button>
                  </div>
                </td>
                <td style="text-align: center;">
                  <button
                    type="button"
                    class="btn-inspeccionar"
                    title="Inspeccionar Evidencia"
                    onclick={() => abrirModalEvidencia(ev)}
                  >
                    <i class="bi bi-search"></i> Ver
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- PAGINACIÓN -->
      {#if total > 0}
        <div class="table-pagination-bar">
          <Pagination
            totalItems={total}
            bind:page
            bind:pageSize
            itemLabel="eventos"
          />
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- MODAL FORENSE DE EVIDENCIA DIGITAL -->
{#if modalAbierto && eventoSeleccionado}
  <div class="modal-backdrop" onclick={cerrarModal} role="presentation">
    <div class="sga-modal-window" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      
      <!-- HEADER MODAL -->
      <div class="sga-modal-header">
        <div class="sga-modal-title">
          <i class="bi bi-fingerprint green-icon"></i>
          <span>EVIDENCIA DIGITAL FORENSE #{eventoSeleccionado.id}</span>
        </div>
        <button class="sga-modal-close" onclick={cerrarModal} title="Cerrar">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="sga-modal-subtitle">
        • REGISTRO CRIPTOGRÁFICO INMUTABLE CON ENCADENAMIENTO SHA-256
      </div>

      <!-- BODY MODAL -->
      <div class="sga-modal-body">
        
        <!-- RESUMEN EN TARJETAS -->
        <div class="modal-meta-grid">
          <div class="meta-box">
            <span class="m-lbl">Entidad Afectada</span>
            <span class="m-val">{eventoSeleccionado.entidad} #{eventoSeleccionado.id_registro}</span>
          </div>
          <div class="meta-box">
            <span class="m-lbl">Acción Registrada</span>
            <span class="m-val">
              <span class="acc-tag {getBadgeClassAccion(eventoSeleccionado.accion)}">{eventoSeleccionado.accion}</span>
            </span>
          </div>
          <div class="meta-box">
            <span class="m-lbl">Operador / Usuario</span>
            <span class="m-val">{eventoSeleccionado.username}</span>
          </div>
          <div class="meta-box">
            <span class="m-lbl">IP de Origen</span>
            <span class="m-val"><code>{eventoSeleccionado.ip_origen}</code></span>
          </div>
          <div class="meta-box full">
            <span class="m-lbl">Sello de Tiempo Registrado</span>
            <span class="m-val"><i class="bi bi-clock-history"></i> {eventoSeleccionado.creado_en}</span>
          </div>
        </div>

        <!-- PRUEBA CRIPTOGRÁFICA -->
        <div class="crypto-chain-card">
          <div class="cc-header">
            <i class="bi bi-link-45deg"></i>
            <span>Encadenamiento Criptográfico (Proof of Chain)</span>
          </div>
          
          <div class="cc-item">
            <span class="cc-lbl">Hash Anterior (Padre):</span>
            <div class="cc-hash-row">
              <code>{eventoSeleccionado.hash_anterior}</code>
              <button class="btn-copy-mini" onclick={() => copiarAlPortapapeles(eventoSeleccionado.hash_anterior, 'h-ant')}>
                <i class="bi {hashCopiado === 'h-ant' ? 'bi-check-lg' : 'bi-copy'}"></i>
              </button>
            </div>
          </div>

          <div class="cc-item">
            <span class="cc-lbl">Hash Actual (Bloque #{eventoSeleccionado.id}):</span>
            <div class="cc-hash-row current-hash">
              <code>{eventoSeleccionado.hash_actual}</code>
              <button class="btn-copy-mini" onclick={() => copiarAlPortapapeles(eventoSeleccionado.hash_actual, 'h-act')}>
                <i class="bi {hashCopiado === 'h-act' ? 'bi-check-lg' : 'bi-copy'}"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- PAYLOAD JSON -->
        <div class="payload-box">
          <div class="pb-header">
            <span><i class="bi bi-code-slash"></i> Payload Transaccional (JSON)</span>
            <button
              type="button"
              class="btn-copy-json"
              onclick={() => copiarAlPortapapeles(JSON.stringify(eventoSeleccionado.detalles, null, 2), 'json')}
            >
              <i class="bi {jsonCopiado ? 'bi-check-lg' : 'bi-clipboard'}"></i>
              <span>{jsonCopiado ? '¡Copiado!' : 'Copiar JSON'}</span>
            </button>
          </div>
          <pre class="json-code"><code>{JSON.stringify(eventoSeleccionado.detalles, null, 2)}</code></pre>
        </div>

      </div>

      <!-- FOOTER MODAL -->
      <div class="sga-modal-footer">
        <button type="button" class="sga-btn-cancel" onclick={cerrarModal}>
          Cerrar
        </button>
      </div>

    </div>
  </div>
{/if}

<style>
  /* ── SUBBAR (ESTILO SGA UTEQ) ── */
  .subbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 24px;
    background: #fff;
    border-bottom: 1px solid #e2e8f0;
    flex-wrap: wrap;
    gap: 10px;
  }
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.84rem;
  }
  .breadcrumb a {
    color: #1b7505;
    text-decoration: none;
    font-weight: 700;
  }
  .breadcrumb a:hover {
    text-decoration: underline;
  }
  .breadcrumb .sep {
    color: #94a3b8;
  }
  .breadcrumb .current {
    color: #1e293b;
    font-weight: 800;
  }

  .btn-verificar {
    background: #1b7505;
    color: #ffffff;
    border: none;
    border-radius: 9px;
    padding: 8px 16px;
    font-size: 0.84rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(27, 117, 5, 0.2);
  }
  .btn-verificar:hover:not(:disabled) {
    background: #155e04;
    transform: translateY(-1px);
  }
  .btn-verificar:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  /* ── WRAPPER DE PÁGINA ── */
  .page-wrap {
    padding: 20px 24px 40px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 100%;
    box-sizing: border-box;
    min-width: 0;
  }

  .page-top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .page-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .page-title i {
    color: #1b7505;
  }
  .page-sub {
    font-size: 0.84rem;
    color: #64748b;
    margin: 2px 0 0;
  }

  /* ── BANNER CRIPTOGRÁFICO ── */
  .forensic-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 18px;
    border-radius: 12px;
    border: 1.5px solid;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
  }
  .banner-ok {
    background: #f0fdf4;
    border-color: #86efac;
    color: #166534;
  }
  .banner-err {
    background: #fef2f2;
    border-color: #fca5a5;
    color: #991b1b;
  }
  .fb-icon {
    font-size: 1.8rem;
    line-height: 1;
  }
  .banner-ok .fb-icon { color: #16a34a; }
  .banner-err .fb-icon { color: #dc2626; }
  .fb-body {
    flex: 1;
  }
  .fb-title {
    font-weight: 800;
    font-size: 0.9rem;
    letter-spacing: 0.3px;
  }
  .fb-text {
    font-size: 0.8rem;
    margin-top: 2px;
  }
  .fb-hash {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-left: 8px;
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.76rem;
  }
  .fb-hash code {
    font-family: monospace;
    font-weight: 700;
  }
  .fb-badge {
    padding: 3px 8px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
  }
  .banner-ok .fb-badge { background: #22c55e; color: #fff; }
  .banner-err .fb-badge { background: #ef4444; color: #fff; }

  /* ── KPIS BANNER ── */
  .kpis-banner {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }
  .kpi-mini-card {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
  }
  .kmc-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
  }
  .kmc-icon.azul { background: #eff6ff; color: #2563eb; }
  .kmc-icon.verde { background: #f0fdf4; color: #16a34a; }
  .kmc-icon.amarillo { background: #fefce8; color: #ca8a04; }
  .kmc-icon.rojo { background: #fef2f2; color: #dc2626; }
  .kmc-info { display: flex; flex-direction: column; gap: 1px; }
  .kmc-num { font-size: 1.3rem; font-weight: 900; color: #0f172a; line-height: 1; }
  .kmc-label { font-size: 0.72rem; font-weight: 800; color: #64748b; text-transform: uppercase; }

  /* ── FILTROS ── */
  .filtros-bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
    background: #ffffff;
    padding: 10px 14px;
    border-radius: 12px;
    border: 1.5px solid #e2e8f0;
  }
  .search-input-wrap {
    position: relative;
    flex: 1;
    min-width: 240px;
  }
  .search-ico {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
    font-size: 0.85rem;
  }
  .search-input-wrap input {
    width: 100%;
    box-sizing: border-box;
    padding: 7px 30px 7px 30px;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.82rem;
    outline: none;
  }
  .search-input-wrap input:focus {
    border-color: #1b7505;
  }
  .clear-btn {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.85rem;
  }
  .select-group {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 700;
    color: #475569;
  }
  .select-group select {
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 0.82rem;
    background: #fff;
    color: #334155;
    outline: none;
  }
  .select-group select:focus {
    border-color: #1b7505;
  }
  .btn-limpiar {
    background: #f1f5f9;
    color: #475569;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px 12px;
    font-weight: 700;
    font-size: 0.8rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .btn-limpiar:hover {
    background: #e2e8f0;
  }

  /* ── TABLA FORENSE ── */
  .table-wrap {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
  }
  .table-scroll {
    overflow-x: auto;
    width: 100%;
  }
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    text-align: left;
    white-space: nowrap;
  }
  .data-table th {
    background: #f8fafc;
    color: #475569;
    font-weight: 800;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 14px;
    border-bottom: 1.5px solid #e2e8f0;
  }
  .data-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
    vertical-align: middle;
  }
  .data-table tbody tr:hover {
    background: #fbfcfe;
  }

  .col-id { font-weight: 800; color: #64748b; }
  .col-time { font-size: 0.78rem; color: #64748b; }
  .col-user { display: flex; align-items: center; gap: 5px; font-weight: 600; }
  .user-ico { color: #94a3b8; }
  .col-ip code {
    background: #f1f5f9;
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 0.76rem;
    color: #475569;
  }

  .hash-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 3px 6px;
    border-radius: 6px;
    font-size: 0.76rem;
  }
  .hash-tag i { color: #94a3b8; }
  .hash-tag code {
    font-family: monospace;
    font-weight: 700;
    color: #0f172a;
  }
  .btn-copy {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0 2px;
    font-size: 0.8rem;
  }
  .btn-copy:hover { color: #1b7505; }

  .btn-inspeccionar {
    background: #f1f5f9;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.76rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s;
  }
  .btn-inspeccionar:hover {
    background: #1b7505;
    color: #fff;
    border-color: #1b7505;
  }

  /* TAGS & BADGES */
  .ent-tag {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 800;
  }
  .ent-proyecto   { background: #ede9fe; color: #5b21b6; }
  .ent-convenio   { background: #ffe4e6; color: #9f1239; }
  .ent-documento  { background: #fef9c3; color: #854d0e; }
  .ent-usuario    { background: #f3e8ff; color: #6b21a8; }
  .ent-cooperante { background: #ffedd5; color: #9a3412; }
  .ent-neutral    { background: #f1f5f9; color: #475569; }

  .acc-tag {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 800;
  }
  .acc-tag.verde    { background: #dcfce7; color: #166534; }
  .acc-tag.amarillo { background: #fef3c7; color: #92400e; }
  .acc-tag.rojo     { background: #fee2e2; color: #991b1b; }
  .acc-tag.azul     { background: #e0f2fe; color: #075985; }
  .acc-tag.morado   { background: #e0e7ff; color: #3730a3; }
  .acc-tag.neutral  { background: #f1f5f9; color: #475569; }

  .loading-box, .empty-box {
    padding: 40px 20px;
    text-align: center;
    color: #64748b;
  }
  .loading-box i, .empty-box i {
    font-size: 2.2rem;
    display: block;
    margin-bottom: 10px;
  }
  .empty-box h4 {
    font-size: 1rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px;
  }

  .table-pagination-bar {
    padding: 8px 14px;
    border-top: 1px solid #eef2f6;
  }

  /* ── MODAL ESTILO SGA INSTITUCIONAL ── */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 16px;
    box-sizing: border-box;
  }

  .sga-modal-window {
    background: #ffffff;
    border-radius: 16px;
    width: 100%;
    max-width: 680px;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
    overflow: hidden;
  }

  .sga-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    background: #ffffff;
    border-bottom: 1px solid #eef2f6;
  }

  .sga-modal-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.95rem;
    font-weight: 800;
    color: #1e293b;
  }
  .green-icon { color: #1b7a2b; font-size: 1.15rem; }

  .sga-modal-close {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1.1rem;
  }
  .sga-modal-close:hover { color: #dc2626; }

  .sga-modal-subtitle {
    font-size: 0.7rem;
    font-weight: 700;
    color: #888888;
    padding: 6px 20px;
    background: #f8fafc;
    border-bottom: 1px solid #eef2f6;
  }

  .sga-modal-body {
    padding: 16px 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .modal-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  .meta-box {
    background: #f8fafc;
    border: 1px solid #eef2f6;
    border-radius: 8px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .meta-box.full { grid-column: span 2; }
  .m-lbl { font-size: 0.68rem; font-weight: 800; color: #64748b; text-transform: uppercase; }
  .m-val { font-size: 0.82rem; font-weight: 700; color: #0f172a; }

  .crypto-chain-card {
    background: #0f172a;
    color: #f8fafc;
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .cc-header {
    font-size: 0.74rem;
    font-weight: 800;
    color: #38bdf8;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .cc-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .cc-lbl {
    font-size: 0.7rem;
    color: #94a3b8;
  }
  .cc-hash-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.74rem;
  }
  .cc-hash-row.current-hash {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.3);
  }
  .cc-hash-row.current-hash code {
    color: #4ade80;
  }
  .cc-hash-row code {
    font-family: monospace;
    word-break: break-all;
    color: #cbd5e1;
  }
  .btn-copy-mini {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0 4px;
    margin-left: 6px;
  }
  .btn-copy-mini:hover { color: #fff; }

  .payload-box {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .pb-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.78rem;
    font-weight: 800;
    color: #334155;
  }
  .btn-copy-json {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .btn-copy-json:hover { background: #e2e8f0; }

  .json-code {
    background: #1e293b;
    color: #e2e8f0;
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-family: monospace;
    max-height: 180px;
    overflow-y: auto;
    margin: 0;
  }

  .sga-modal-footer {
    display: flex;
    justify-content: flex-end;
    padding: 12px 20px;
    background: #f8fafc;
    border-top: 1px solid #eef2f6;
  }
  .sga-btn-cancel {
    background: #e2e8f0;
    color: #475569;
    border: none;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 0.82rem;
    font-weight: 700;
    cursor: pointer;
  }
  .sga-btn-cancel:hover { background: #cbd5e1; color: #1e293b; }

  .spin { animation: spin 1s linear infinite; display: inline-block; }
  @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
