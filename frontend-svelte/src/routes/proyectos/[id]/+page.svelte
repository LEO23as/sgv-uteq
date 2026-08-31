<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';

  const API_BASE = 'http://127.0.0.1:8000';
  const id = $derived($page.params.id);

  let proy = $state(null);
  let loading = $state(true);
  let fotoActiva = $state(null);

  let documentos = $state([]);
  let tiposDoc = $state([]);
  let codigoTipoSubir = $state('');
  let archivoSubir = $state(null);
  let subiendoDoc = $state(false);

  const ESTADOS = {
    EN_EJECUCION: { label:'En ejecución', cls:'ejecucion' },
    PROPUESTO:    { label:'Propuesto',    cls:'propuesto'  },
    APROBADO:     { label:'Aprobado',     cls:'aprobado'   },
    EN_CIERRE:    { label:'En cierre',    cls:'cierre'     },
    DETENIDO:     { label:'Detenido',     cls:'detenido'   },
    FINALIZADO:   { label:'Finalizado',   cls:'finalizado' },
    RECHAZADO:    { label:'Rechazado',    cls:'rechazado'  },
  };

  function calcularAvanceTemporal(fechaInicio, fechaFin, estado) {
    if (estado === 'FINALIZADO') return { pct: 100, label: 'Proyecto Finalizado (100%)', variant: 'success', rest: 0 };
    if (!fechaInicio || !fechaFin) return { pct: 0, label: 'Fechas no definidas', variant: 'info', rest: null };
    
    const ini = new Date(fechaInicio);
    const fin = new Date(fechaFin);
    const hoy = new Date();
    
    const total = fin.getTime() - ini.getTime();
    if (total <= 0) return { pct: 100, label: 'Plazo culminado', variant: 'warning', rest: 0 };
    
    const rest = Math.ceil((fin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    const transcurrido = hoy.getTime() - ini.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurrido / total) * 100)));
    
    if (rest <= 0) {
      return { pct: 100, label: 'Plazo culminado', variant: 'danger', rest };
    } else if (rest <= 30) {
      return { pct, label: `${pct}% transcurrido · ${rest} días restantes`, variant: 'warning', rest };
    } else {
      return { pct, label: `${pct}% transcurrido · ${rest} días restantes`, variant: 'auto', rest };
    }
  }

  onMount(async () => {
    try {
      [proy, tiposDoc] = await Promise.all([
        fetchAPI(`/api/proyectos/${id}/detalle/`),
        fetchAPI('/api/tipos-documento/'),
      ]);
      await cargarDocumentos();
    } catch {
      toast.error('No se pudo cargar el proyecto seleccionado');
    } finally { loading = false; }
  });

  async function cargarDocumentos() {
    try { documentos = await fetchAPI(`/api/proyectos/${id}/documentos/`); } catch { documentos = []; }
  }

  function onArchivoSubirChange(e) { archivoSubir = e.target.files[0] || null; }

  async function subirDocumento() {
    if (!codigoTipoSubir || !archivoSubir) { toast.error('Selecciona el tipo de documento y el archivo.'); return; }
    subiendoDoc = true;
    try {
      const fd = new FormData();
      fd.append('codigo_tipo', codigoTipoSubir);
      fd.append('archivo', archivoSubir);
      const res = await fetch(`/api/proyectos/${id}/documentos/subir/`, { method:'POST', credentials:'include', body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { toast.error(data.error || 'Error al subir el documento'); return; }
      archivoSubir = null; codigoTipoSubir = '';
      await cargarDocumentos();
      toast.success('Documento incorporado al portafolio');
    } catch { toast.error('Error de conexión al subir documento'); }
    finally { subiendoDoc = false; }
  }

  async function eliminarDocumento(d) {
    const ok = await confirmDialog({
      title: '¿Eliminar documento del portafolio?',
      message: `Se eliminará el documento "${d.nombre}". Esta acción es irreversible.`,
      confirmText: 'Sí, eliminar',
      type: 'danger'
    });
    if (!ok) return;

    try {
      const res = await fetch(`/api/documentos/${d.id}/`, { method:'DELETE', credentials:'include' });
      if (res.ok) {
        await cargarDocumentos();
        toast.success('Documento eliminado correctamente');
      } else {
        toast.error('No se pudo eliminar el documento');
      }
    } catch { toast.error('Error de conexión al eliminar'); }
  }
</script>

<svelte:head><title>{proy?.nombre || 'Proyecto'} — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/proyectos">Proyectos</a>
    <span class="sep">/</span>
    <span class="current">Detalle</span>
  </nav>
  {#if proy}
    <a href="/proyectos/{id}/editar" class="btn-editar">
      <i class="bi bi-pencil-square"></i> Editar proyecto
    </a>
  {/if}
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando proyecto...</div>
{:else if proy}
  {@const av = calcularAvanceTemporal(proy.fecha_inicio, proy.fecha_fin_planificada, proy.estado)}
  <div class="detalle-wrap">

    <!-- HEADER CARD -->
    <div class="header-card">
      <div class="hc-left">
        <span class="hc-code"><i class="bi bi-bookmark-fill"></i> {proy.codigo}</span>
        <h1 class="hc-title">{proy.nombre}</h1>
        {#if proy.nombre_corto}
          <p class="hc-short">{proy.nombre_corto}</p>
        {/if}
      </div>
      <div class="hc-right">
        <span class="badge est-{ESTADOS[proy.estado]?.cls || 'ejecucion'}">
          <span class="dot"></span>
          {ESTADOS[proy.estado]?.label || proy.estado}
        </span>
      </div>
    </div>

    <!-- TARJETA DE AVANCE Y ESTADO TEMPORAL -->
    <div class="progreso-card">
      <div class="progreso-header">
        <div class="ph-title">
          <i class="bi bi-speedometer2"></i>
          <span>Progreso y Cronograma del Proyecto</span>
        </div>
        <span class="ph-badge">{av.label}</span>
      </div>
      <ProgressBar
        value={av.pct}
        max={100}
        label="Avance del período de ejecución"
        sublabel="{proy.fecha_inicio || 'Inicio'} → {proy.fecha_fin_planificada || 'Fin previsto'}"
        showPercentage={true}
        variant={av.variant}
        size="md"
        animated={proy.estado === 'EN_EJECUCION'}
      />
    </div>

    <div class="detalle-grid">
      <!-- COLUMNA PRINCIPAL -->
      <div class="col-main">

        <!-- Información General -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-info-circle-fill"></i> Información General</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Facultad</span>
              <span class="info-val">{proy.facultad}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Carrera</span>
              <span class="info-val">{proy.carrera}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Período de inicio</span>
              <span class="info-val">{proy.periodo}</span>
            </div>
            {#if proy.linea_vinculacion}
            <div class="info-item">
              <span class="info-label">Línea de vinculación</span>
              <span class="info-val">{proy.linea_vinculacion}</span>
            </div>
            {/if}
            {#if proy.ods}
            <div class="info-item">
              <span class="info-label">ODS Atendidos</span>
              <span class="info-val">{proy.ods}</span>
            </div>
            {/if}
            {#if proy.alcance}
            <div class="info-item">
              <span class="info-label">Alcance</span>
              <span class="info-val">{proy.alcance}</span>
            </div>
            {/if}
            {#if proy.fecha_inicio}
            <div class="info-item">
              <span class="info-label">Fecha de inicio</span>
              <span class="info-val">{proy.fecha_inicio}</span>
            </div>
            {/if}
            {#if proy.fecha_fin_planificada}
            <div class="info-item">
              <span class="info-label">Fecha fin planificada</span>
              <span class="info-val">{proy.fecha_fin_planificada}</span>
            </div>
            {/if}
            {#if proy.provincia}
            <div class="info-item full">
              <span class="info-label">Ubicación geográfica</span>
              <span class="info-val"><i class="bi bi-geo-alt-fill text-verde"></i> {proy.canton}, {proy.parroquia ? proy.parroquia + ', ' : ''}{proy.provincia}</span>
            </div>
            {/if}
            {#if proy.presupuesto_planificado}
            <div class="info-item">
              <span class="info-label">Presupuesto planificado</span>
              <span class="info-val text-verde font-bold">$ {proy.presupuesto_planificado}</span>
            </div>
            {/if}
            {#if proy.resolucion_aprobacion}
            <div class="info-item">
              <span class="info-label">Resolución de aprobación</span>
              <span class="info-val">{proy.resolucion_aprobacion}</span>
            </div>
            {/if}
          </div>
          {#if proy.descripcion}
            <div class="sec-section">
              <span class="info-label">Descripción del proyecto</span>
              <p class="info-text">{proy.descripcion}</p>
            </div>
          {/if}
          {#if proy.objetivo_general}
            <div class="sec-section">
              <span class="info-label">Objetivo general</span>
              <p class="info-text">{proy.objetivo_general}</p>
            </div>
          {/if}
          {#if proy.terminos_negociacion}
            <div class="sec-section">
              <span class="info-label">Términos de negociación</span>
              <p class="info-text">{proy.terminos_negociacion}</p>
            </div>
          {/if}
        </div>

        <!-- Fotos -->
        {#if proy.fotos?.length}
          <div class="sec-card">
            <h3 class="sec-title"><i class="bi bi-images"></i> Evidencia fotográfica ({proy.fotos.length})</h3>
            <div class="fotos-grid">
              {#each proy.fotos as foto}
                <button class="foto-thumb" onclick={() => fotoActiva = foto}>
                  <img src={API_BASE + foto.url} alt={foto.titulo || 'Evidencia'} />
                </button>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Documentos del portafolio -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-folder-fill"></i> Documentos del portafolio ({documentos.length})</h3>
          {#if documentos.length}
            <div class="docs-list">
              {#each documentos as d}
                <div class="doc-row">
                  <i class="bi bi-file-earmark-pdf-fill"></i>
                  <div class="doc-info">
                    <a href={API_BASE + d.url} target="_blank">{d.tipo}</a>
                    <span class="doc-meta">{d.codigo_tipo} — {d.nombre} · {d.tamanio_kb} KB</span>
                  </div>
                  <button class="doc-del" onclick={() => eliminarDocumento(d)} title="Eliminar documento"><i class="bi bi-trash"></i></button>
                </div>
              {/each}
            </div>
          {:else}
            <p class="empty-side">Aún no se han subido documentos al portafolio.</p>
          {/if}

          <div class="doc-upload">
            <select bind:value={codigoTipoSubir}>
              <option value="">— Tipo de documento —</option>
              {#each tiposDoc as t}<option value={t.codigo}>{t.numero_carpeta}. {t.nombre}</option>{/each}
            </select>
            <input type="file" accept="application/pdf,image/*" onchange={onArchivoSubirChange} />
            <button class="btn-side-add primary" onclick={subirDocumento} disabled={subiendoDoc}>
              {#if subiendoDoc}<i class="bi bi-arrow-repeat spin"></i> Subiendo...{:else}<i class="bi bi-cloud-arrow-up"></i> Subir{/if}
            </button>
          </div>
          {#if subiendoDoc}
            <div style="margin-top: 8px;">
              <ProgressBar value={100} animated={true} striped={true} label="Subiendo archivo..." size="sm" />
            </div>
          {/if}
        </div>

      </div>

      <!-- COLUMNA LATERAL -->
      <div class="col-side">
        <!-- Convenios -->
        <div class="sec-card">
          <h3 class="sec-title"><i class="bi bi-file-earmark-text-fill"></i> Convenios vinculados</h3>
          {#if proy.convenios && proy.convenios.length > 0}
            <div class="convenios-list">
              {#each proy.convenios as conv}
                <div class="conv-card">
                  <div class="conv-head">
                    <span class="conv-entidad"><i class="bi bi-building"></i> {conv.entidad_nombre}</span>
                    <span class="conv-badge {conv.estado?.toLowerCase()}">{conv.estado}</span>
                  </div>
                  {#if conv.numero_memorando}
                    <div class="conv-memo"><i class="bi bi-file-text"></i> Memo: {conv.numero_memorando}</div>
                  {/if}
                  <div class="conv-dates">
                    <span>Firma: {conv.fecha_firma || 'N/A'}</span> · <span>Vence: {conv.fecha_fin || 'N/A'}</span>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <p class="empty-side">No hay convenios registrados para este proyecto.</p>
          {/if}
          <a href="/convenios/nuevo?proyecto={id}" class="btn-side-add primary block">
            <i class="bi bi-plus-lg"></i> Agregar convenio
          </a>
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="loading-wrap">Proyecto no encontrado</div>
{/if}

<!-- LIGHTBOX -->
{#if fotoActiva}
  <div class="lightbox" onclick={() => fotoActiva = null}>
    <button class="lb-close" onclick={() => fotoActiva = null}><i class="bi bi-x-lg"></i></button>
    <img src={API_BASE + fotoActiva.url} alt={fotoActiva.titulo || 'Evidencia'} onclick={(e) => e.stopPropagation()} />
    {#if fotoActiva.titulo}<p class="lb-caption">{fotoActiva.titulo}</p>{/if}
  </div>
{/if}

<style>
  .subbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px; background: #fff; border-bottom: 1px solid var(--borde, #e0e0e0);
  }
  .breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: var(--gris, #777); font-weight: 700; }
  .breadcrumb a { color: var(--gris, #777); text-decoration: none; transition: color 0.2s; }
  .breadcrumb a:hover { color: var(--verde, #1b5e20); }
  .btn-editar { display: flex; align-items: center; gap: 6px; background: #1b7505; color: #fff; text-decoration: none; padding: 7px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; }
  .btn-editar:hover { background: #145c04; }

  .loading-wrap { text-align: center; padding: 60px; color: #64748b; font-weight: 600; }
  .detalle-wrap { max-width: 1140px; margin: 24px auto; padding: 0 20px; display: flex; flex-direction: column; gap: 18px; }

  .header-card { background: #fff; border-radius: 14px; padding: 22px 26px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: flex-start; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
  .hc-code { font-size: 0.75rem; font-weight: 800; color: #1b7505; background: #e8f8e8; padding: 3px 10px; border-radius: 6px; display: inline-flex; align-items: center; gap: 5px; margin-bottom: 8px; }
  .hc-title { font-size: 1.35rem; font-weight: 800; color: #0f172a; margin: 0 0 4px 0; }
  .hc-short { font-size: 0.9rem; color: #64748b; margin: 0; }

  .progreso-card { background: #fff; border-radius: 14px; padding: 18px 24px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,.04); display: flex; flex-direction: column; gap: 10px; }
  .progreso-header { display: flex; justify-content: space-between; align-items: center; }
  .ph-title { display: flex; align-items: center; gap: 8px; font-weight: 700; color: #1e293b; font-size: 0.92rem; }
  .ph-badge { font-size: 0.75rem; font-weight: 700; color: #475569; background: #f1f5f9; padding: 3px 10px; border-radius: 20px; }

  .detalle-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 18px; }
  .col-main { display: flex; flex-direction: column; gap: 18px; }
  .col-side { display: flex; flex-direction: column; gap: 18px; }

  .sec-card { background: #fff; border-radius: 14px; padding: 20px 24px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
  .sec-title { font-size: 1rem; font-weight: 800; color: #1e293b; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; }

  .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 18px; }
  .info-item { display: flex; flex-direction: column; gap: 2px; }
  .info-item.full { grid-column: span 2; }
  .info-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.3px; }
  .info-val { font-size: 0.88rem; color: #1e293b; font-weight: 600; }
  .text-verde { color: #1b7505; }
  .font-bold { font-weight: 700; }

  .sec-section { margin-top: 14px; border-top: 1px dashed #e2e8f0; padding-top: 10px; display: flex; flex-direction: column; gap: 4px; }
  .info-text { font-size: 0.85rem; color: #334155; line-height: 1.5; margin: 0; }

  .fotos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px; }
  .foto-thumb { border: none; background: none; padding: 0; border-radius: 8px; overflow: hidden; height: 80px; cursor: pointer; }
  .foto-thumb img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.2s; }
  .foto-thumb:hover img { transform: scale(1.05); }

  .docs-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
  .doc-row { display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
  .doc-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
  .doc-info a { font-size: 0.85rem; font-weight: 700; color: #0284c7; text-decoration: none; }
  .doc-meta { font-size: 0.75rem; color: #64748b; }
  .doc-del { background: #fee2e2; border: none; color: #dc2626; width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
  .doc-del:hover { background: #fecaca; }

  .doc-upload { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .doc-upload select, .doc-upload input[type="file"] { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: 0.8rem; }
  .btn-side-add { background: #1b7505; color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-size: 0.82rem; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
  .btn-side-add:hover { background: #145c04; }
  .btn-side-add.block { width: 100%; margin-top: 12px; }

  .convenios-list { display: flex; flex-direction: column; gap: 10px; }
  .conv-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
  .conv-head { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; font-weight: 700; }
  .conv-entidad { color: #1e293b; }
  .conv-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; font-weight: 700; }
  .conv-badge.vigente { background: #e8f8e8; color: #1b7505; }
  .conv-badge.vencido { background: #fee2e2; color: #dc2626; }
  .conv-memo, .conv-dates { font-size: 0.75rem; color: #64748b; }
  .empty-side { font-size: 0.82rem; color: #94a3b8; font-style: italic; }

  .lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 10000; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }
  .lightbox img { max-width: 90vw; max-height: 80vh; border-radius: 8px; object-fit: contain; }
  .lb-close { position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2); border: none; color: #fff; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; }
  .lb-caption { color: #fff; margin-top: 10px; font-size: 0.9rem; }

  /* Badges */
  .badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
  .est-ejecucion { background: #e8f8e8; color: #1b7505; }
  .est-propuesto { background: #fef3c7; color: #b45309; }
  .est-aprobado { background: #e0f2fe; color: #0284c7; }
  .est-cierre { background: #fff3e0; color: #ea580c; }
  .est-detenido { background: #fee2e2; color: #dc2626; }
  .est-finalizado { background: #f1f5f9; color: #64748b; }
  .est-rechazado { background: #f1f5f9; color: #94a3b8; }

  @media (max-width: 860px) {
    .detalle-grid { grid-template-columns: 1fr; }
  }
</style>
