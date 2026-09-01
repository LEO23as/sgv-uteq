<script>
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';

  let { idProyecto = null, isOpen = false, onClose } = $props();

  const API_BASE = 'http://127.0.0.1:8000';
  let proy = $state(null);
  let documentos = $state([]);
  let tiposDoc = $state([]);
  let loading = $state(true);
  let fotoActiva = $state(null);
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

  function calcularAvanceTemporal(fechaInicio, fechaFin, estado) {
    if (estado === 'FINALIZADO') return { pct: 100, label: '100% Finalizado', sub: 'Culminado', variant: 'success', rest: 0 };
    
    const ini = parsearFecha(fechaInicio);
    const fin = parsearFecha(fechaFin);
    
    if (!ini || !fin) return { pct: 0, label: '0%', sub: 'Fechas no definidas', variant: 'info', rest: null };
    
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const iniN = new Date(ini); iniN.setHours(0, 0, 0, 0);
    const finN = new Date(fin); finN.setHours(0, 0, 0, 0);
    
    const totalMs = finN.getTime() - iniN.getTime();
    if (totalMs <= 0) return { pct: 100, label: '100%', sub: 'Plazo culminado', variant: 'warning', rest: 0 };
    
    const restDias = Math.ceil((finN.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    const transcurrido = hoy.getTime() - iniN.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurrido / totalMs) * 100)));
    
    if (restDias < 0) {
      return { pct: 100, label: '100%', sub: `Venció ${formatFechaLocal(fin)}`, variant: 'danger', rest: restDias };
    } else if (restDias <= 30) {
      return { pct, label: `${pct}% avance`, sub: `${restDias} días restantes`, variant: 'warning', rest: restDias };
    } else {
      return { pct, label: `${pct}% avance`, sub: `${restDias} días restantes`, variant: 'auto', rest: restDias };
    }
  }

  $effect(() => {
    if (isOpen && idProyecto) {
      cargarDetalle(idProyecto);
    } else {
      proy = null;
      documentos = [];
    }
  });

  async function cargarDetalle(id) {
    loading = true;
    try {
      const [pRes, dRes, tRes] = await Promise.all([
        fetch(`/api/proyectos/${id}/detalle/`, { credentials: 'include' }).then(r => r.json()),
        fetch(`/api/proyectos/${id}/documentos/`, { credentials: 'include' }).then(r => r.json()).catch(() => []),
        fetch(`/api/tipos-documento/`, { credentials: 'include' }).then(r => r.json()).catch(() => [])
      ]);
      proy = pRes;
      documentos = Array.isArray(dRes) ? dRes : [];
      tiposDoc = Array.isArray(tRes) ? tRes : [];
    } catch {
      toast.error('Error al cargar datos del proyecto');
    } finally {
      loading = false;
    }
  }

  async function subirDocumento() {
    if (!codigoTipoSubir || !archivoSubir || !idProyecto) {
      toast.error('Selecciona el tipo de documento y el archivo.');
      return;
    }
    subiendoDoc = true;
    try {
      const fd = new FormData();
      fd.append('codigo_tipo', codigoTipoSubir);
      fd.append('archivo', archivoSubir);
      const res = await fetch(`/api/proyectos/${idProyecto}/documentos/subir/`, {
        method: 'POST', credentials: 'include', body: fd
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        archivoSubir = null; codigoTipoSubir = '';
        const docReload = await fetch(`/api/proyectos/${idProyecto}/documentos/`, { credentials: 'include' }).then(r => r.json());
        documentos = Array.isArray(docReload) ? docReload : [];
        toast.success('Documento subido al portafolio');
      } else {
        toast.error(data.error || 'Error al subir documento');
      }
    } catch {
      toast.error('Error de conexión al subir');
    } finally {
      subiendoDoc = false;
    }
  }

  async function eliminarDocumento(d) {
    const ok = await confirmDialog({
      title: '¿Eliminar documento?',
      message: `Se eliminará el documento "${d.nombre}". Esta acción es irreversible.`,
      confirmText: 'Sí, eliminar',
      type: 'danger'
    });
    if (!ok) return;

    try {
      const res = await fetch(`/api/documentos/${d.id}/`, { method: 'DELETE', credentials: 'include' });
      if (res.ok) {
        documentos = documentos.filter(x => x.id !== d.id);
        toast.success('Documento eliminado');
      } else {
        toast.error('No se pudo eliminar el documento');
      }
    } catch {
      toast.error('Error de conexión');
    }
  }

  function imprimirFicha() {
    window.print();
  }

  function onKeydown(e) {
    if (e.key === 'Escape' && isOpen) {
      if (fotoActiva) fotoActiva = null;
      else onClose?.();
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if isOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="modal-backdrop" onclick={() => onClose?.()}>
    <div class="modal-card printable-modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      
      <!-- ENCABEZADO INSTITUCIONAL OFICIAL UTEQ PARA IMPRESIÓN -->
      <div class="print-official-header">
        <img src="/logo-uteq.png" alt="UTEQ" class="poh-logo" />
        <div class="poh-title-box">
          <h3>UNIVERSIDAD TÉCNICA ESTATAL DE QUEVEDO</h3>
          <h4>DIRECCIÓN DE VINCULACIÓN CON LA SOCIEDAD</h4>
          <p>FICHA TÉCNICA OFICIAL DEL PROYECTO DE VINCULACIÓN</p>
        </div>
      </div>

      <!-- HEADER EN PANTALLA -->
      <div class="modal-header">
        <div class="mh-left">
          {#if proy?.codigo}
            <span class="mh-code"><i class="bi bi-bookmark-fill"></i> {proy.codigo}</span>
          {/if}
          <h2 class="mh-title">{proy?.nombre || (loading ? 'Cargando...' : 'Detalle del Proyecto')}</h2>
          {#if proy?.nombre_corto}
            <p class="mh-sub">{proy.nombre_corto}</p>
          {/if}
        </div>
        <div class="mh-right">
          {#if proy}
            <span class="badge est-{ESTADOS[proy.estado]?.cls || 'ejecucion'}">
              {ESTADOS[proy.estado]?.label || proy.estado}
            </span>
          {/if}
          <button class="btn-close-x" onclick={() => onClose?.()} title="Cerrar modal">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>

      <!-- BODY -->
      <div class="modal-body">
        {#if loading}
          <div class="loading-box"><i class="bi bi-arrow-repeat spin"></i> Cargando detalles del proyecto...</div>
        {:else if proy}
          {@const av = calcularAvanceTemporal(proy.fecha_inicio, proy.fecha_fin_planificada || proy.fecha_fin_real, proy.estado)}
          
          <!-- BANNER AVANCE -->
          <div class="avance-box">
            <div class="ab-head">
              <span class="ab-title"><i class="bi bi-speedometer2"></i> Cronograma de Ejecución</span>
              <span class="badge badge-{av.variant}">{av.label}</span>
            </div>
            <ProgressBar
              value={av.pct}
              max={100}
              label={av.sub}
              sublabel="{formatFechaLocal(proy.fecha_inicio)} → {formatFechaLocal(proy.fecha_fin_planificada)}"
              showPercentage={true}
              variant={av.variant}
              size="md"
            />
          </div>

          <div class="grid-details">
            <!-- Información General -->
            <div class="card-detail">
              <h4 class="card-detail-title"><i class="bi bi-info-circle-fill"></i> Información General</h4>
              <div class="info-grid">
                <div class="info-item"><span class="il">Facultad</span><span class="iv">{proy.facultad}</span></div>
                <div class="info-item"><span class="il">Carrera</span><span class="iv">{proy.carrera}</span></div>
                <div class="info-item"><span class="il">Período Inicio</span><span class="iv">{proy.periodo}</span></div>
                {#if proy.linea_vinculacion}
                  <div class="info-item"><span class="il">Línea Vinculación</span><span class="iv">{proy.linea_vinculacion}</span></div>
                {/if}
                {#if proy.ods}
                  <div class="info-item"><span class="il">ODS</span><span class="iv">{proy.ods}</span></div>
                {/if}
                {#if proy.presupuesto_planificado}
                  <div class="info-item"><span class="il">Presupuesto</span><span class="iv text-green font-bold">$ {proy.presupuesto_planificado}</span></div>
                {/if}
                {#if proy.provincia}
                  <div class="info-item full"><span class="il">Ubicación</span><span class="iv"><i class="bi bi-geo-alt-fill text-green"></i> {proy.canton}, {proy.parroquia ? proy.parroquia + ', ' : ''}{proy.provincia}</span></div>
                {/if}
              </div>
              {#if proy.descripcion}
                <div class="sec-text-block">
                  <span class="il">Descripción</span>
                  <p class="desc-p">{proy.descripcion}</p>
                </div>
              {/if}
              {#if proy.objetivo_general}
                <div class="sec-text-block">
                  <span class="il">Objetivo General</span>
                  <p class="desc-p">{proy.objetivo_general}</p>
                </div>
              {/if}
            </div>

            <!-- Convenios Vinculados -->
            <div class="card-detail">
              <h4 class="card-detail-title"><i class="bi bi-file-earmark-text-fill"></i> Convenios Asociados ({proy.convenios?.length || 0})</h4>
              {#if proy.convenios && proy.convenios.length > 0}
                <div class="conv-stack">
                  {#each proy.convenios as conv}
                    <div class="conv-mini-card">
                      <div class="cm-head">
                        <span class="cm-entidad"><i class="bi bi-building"></i> {conv.entidad_nombre}</span>
                        <span class="badge {conv.estado?.toLowerCase()}">{conv.estado}</span>
                      </div>
                      {#if conv.numero_memorando}
                        <div class="cm-memo">Memo: {conv.numero_memorando}</div>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="empty-docs">No hay convenios registrados para este proyecto.</p>
              {/if}
            </div>

            <!-- Fotos -->
            {#if proy.fotos?.length}
              <div class="card-detail full-col">
                <h4 class="card-detail-title"><i class="bi bi-images"></i> Evidencia Fotográfica ({proy.fotos.length})</h4>
                <div class="fotos-gallery">
                  {#each proy.fotos as foto}
                    <button class="foto-btn" onclick={() => fotoActiva = foto}>
                      <img src={API_BASE + foto.url} alt={foto.titulo || 'Evidencia'} />
                    </button>
                  {/each}
                </div>
              </div>
            {/if}

            <!-- Documentos del Portafolio -->
            <div class="card-detail full-col">
              <h4 class="card-detail-title"><i class="bi bi-folder-fill"></i> Documentos del Portafolio ({documentos.length})</h4>
              
              <!-- Subida -->
              <div class="doc-upload-row">
                <select bind:value={codigoTipoSubir} class="doc-select">
                  <option value="">— Tipo de documento —</option>
                  {#each tiposDoc as t}<option value={t.codigo}>{t.numero_carpeta}. {t.nombre}</option>{/each}
                </select>
                <input type="file" accept="application/pdf,image/*" onchange={(e) => archivoSubir = e.target.files[0] || null} />
                <button class="btn-subir-doc" onclick={subirDocumento} disabled={subiendoDoc}>
                  {#if subiendoDoc}<i class="bi bi-arrow-repeat spin"></i>{:else}<i class="bi bi-cloud-arrow-up"></i> Subir{/if}
                </button>
              </div>

              {#if documentos.length}
                <div class="docs-stack">
                  {#each documentos as d}
                    <div class="doc-item">
                      <i class="bi bi-file-earmark-pdf-fill doc-ic"></i>
                      <div class="doc-txt">
                        <a href={API_BASE + d.url} target="_blank" class="doc-link">{d.tipo}</a>
                        <span class="doc-sub">{d.codigo_tipo} — {d.nombre} · {d.tamanio_kb} KB</span>
                      </div>
                      <button class="btn-doc-del" onclick={() => eliminarDocumento(d)} title="Eliminar documento">
                        <i class="bi bi-trash"></i>
                      </button>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="empty-docs">Aún no se han subido documentos al portafolio.</p>
              {/if}
            </div>
          </div>

          <!-- FIRMAS OFICIALES UTEQ (SOLO EN IMPRESIÓN) -->
          <div class="print-official-firmas">
            <div class="pof-col">
              <div class="pof-line"></div>
              <span>DIRECTOR(A) DE VINCULACIÓN</span>
              <small>Universidad Técnica Estatal de Quevedo</small>
            </div>
            <div class="pof-col">
              <div class="pof-line"></div>
              <span>DIRECTOR / RESPONSABLE DEL PROYECTO</span>
              <small>{proy.director_proyecto || 'Docente Responsable'}</small>
            </div>
          </div>
        {/if}
      </div>

      <!-- FOOTER -->
      <div class="modal-footer">
        <button type="button" class="btn-modal-print" onclick={imprimirFicha}>
          <i class="bi bi-printer-fill"></i> Imprimir Ficha PDF
        </button>
        <button type="button" class="btn-modal-close" onclick={() => onClose?.()}>
          Cerrar
        </button>
        {#if proy}
          <a href="/proyectos/{proy.id_proyecto}/editar" class="btn-modal-edit">
            <i class="bi bi-pencil-square"></i> Editar Proyecto
          </a>
        {/if}
      </div>

    </div>
  </div>
{/if}

<!-- LIGHTBOX PARA FOTOS -->
{#if fotoActiva}
  <div class="lightbox" onclick={() => fotoActiva = null}>
    <button class="lb-close" onclick={() => fotoActiva = null}><i class="bi bi-x-lg"></i></button>
    <img src={API_BASE + fotoActiva.url} alt={fotoActiva.titulo || 'Evidencia'} onclick={(e) => e.stopPropagation()} />
    {#if fotoActiva.titulo}<p class="lb-caption">{fotoActiva.titulo}</p>{/if}
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    animation: fadeIn .18s ease-out;
  }

  .modal-card {
    background: #ffffff;
    border-radius: 16px;
    max-width: 900px;
    width: 100%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
    border: 1px solid #e2e8f0;
    animation: popIn .22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 20px 24px 16px;
    border-bottom: 1px solid #e2e8f0;
    gap: 12px;
  }

  .mh-code { font-size: .72rem; font-weight: 800; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 2px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px; margin-bottom: 4px; }
  .mh-title { font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0; }
  .mh-sub { font-size: .84rem; color: #64748b; margin: 2px 0 0 0; }

  .mh-right { display: flex; align-items: center; gap: 12px; }
  .btn-close-x {
    width: 32px; height: 32px; border-radius: 8px; border: none; background: #f1f5f9; color: #64748b;
    display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all .15s;
  }
  .btn-close-x:hover { background: #fee2e2; color: #dc2626; }

  .modal-body {
    padding: 20px 24px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .loading-box { text-align: center; padding: 40px; color: #64748b; font-weight: 600; }

  .avance-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .ab-head { display: flex; justify-content: space-between; align-items: center; }
  .ab-title { font-size: .86rem; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 6px; }

  .grid-details { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; }
  .card-detail { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 18px; }
  .full-col { grid-column: span 2; }
  .card-detail-title { font-size: .9rem; font-weight: 800; color: #1e293b; margin: 0 0 12px 0; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; }

  .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; }
  .info-item { display: flex; flex-direction: column; gap: 2px; }
  .info-item.full { grid-column: span 2; }
  .il { font-size: .7rem; font-weight: 700; text-transform: uppercase; color: #94a3b8; }
  .iv { font-size: .84rem; color: #1e293b; font-weight: 600; word-break: break-word; }
  .font-bold { font-weight: 700; }
  .text-green { color: #15803d; }

  .sec-text-block { margin-top: 10px; padding-top: 8px; border-top: 1px dashed #e2e8f0; display: flex; flex-direction: column; gap: 3px; }
  .desc-p { font-size: .82rem; color: #475569; margin: 0; line-height: 1.45; }

  .conv-stack { display: flex; flex-direction: column; gap: 8px; }
  .conv-mini-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; gap: 4px; }
  .cm-head { display: flex; justify-content: space-between; align-items: center; font-size: .82rem; font-weight: 700; }
  .cm-entidad { color: #1e293b; }
  .cm-memo { font-size: .74rem; color: #64748b; }

  .fotos-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
  .foto-btn { border: none; background: none; padding: 0; border-radius: 8px; overflow: hidden; height: 75px; cursor: pointer; }
  .foto-btn img { width: 100%; height: 100%; object-fit: cover; transition: transform .2s; }
  .foto-btn:hover img { transform: scale(1.05); }

  .doc-upload-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px dashed #cbd5e1; }
  .doc-select { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; font-size: .8rem; }
  .btn-subir-doc { background: #1b7505; color: #fff; border: none; border-radius: 6px; padding: 6px 14px; font-size: .8rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 5px; }
  .btn-subir-doc:hover { background: #145c04; }

  .docs-stack { display: flex; flex-direction: column; gap: 6px; }
  .doc-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
  .doc-ic { font-size: 1.15rem; color: #dc2626; }
  .doc-txt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
  .doc-link { font-size: .82rem; font-weight: 700; color: #0284c7; text-decoration: none; }
  .doc-sub { font-size: .72rem; color: #64748b; }
  .btn-doc-del { width: 28px; height: 28px; border-radius: 6px; border: none; background: #fee2e2; color: #dc2626; display: flex; align-items: center; justify-content: center; cursor: pointer; }
  .empty-docs { font-size: .82rem; color: #94a3b8; font-style: italic; margin: 4px 0 0; }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 14px 24px;
    border-top: 1px solid #e2e8f0;
    background: #f8fafc;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
  }
  .btn-modal-print {
    background: #ffffff; border: 1.5px solid var(--verde, #1b7505); color: var(--verde, #1b7505);
    padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: .84rem; cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px; transition: all .15s ease;
  }
  .btn-modal-print:hover { background: var(--verde-claro, #e8f5e0); }
  .btn-modal-close { background: #ffffff; border: 1px solid #cbd5e1; color: #475569; padding: 8px 18px; border-radius: 8px; font-weight: 600; font-size: .84rem; cursor: pointer; }
  .btn-modal-close:hover { background: #f1f5f9; }
  .btn-modal-edit { background: var(--verde, #1b7505); color: #ffffff; border: none; padding: 8px 18px; border-radius: 8px; font-weight: 700; font-size: .84rem; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
  .btn-modal-edit:hover { background: #145c04; }

  .print-official-header { display: none; }
  .print-official-firmas { display: none; }

  .lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 10000; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }
  .lightbox img { max-width: 90vw; max-height: 80vh; border-radius: 8px; object-fit: contain; }
  .lb-close { position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2); border: none; color: #fff; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; }
  .lb-caption { color: #fff; margin-top: 10px; font-size: 0.9rem; }

  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes popIn { from { opacity: 0; transform: scale(.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }

  @media (max-width: 640px) {
    .grid-details { grid-template-columns: 1fr; }
    .full-col { grid-column: span 1; }
    .info-grid { grid-template-columns: 1fr; }
    .info-item.full { grid-column: span 1; }
  }

  @media print {
    .modal-backdrop { position: static !important; background: none !important; padding: 0 !important; }
    .modal-card { max-width: 100% !important; max-height: none !important; box-shadow: none !important; border: none !important; }
    .modal-header, .modal-footer, .doc-upload-row, .btn-doc-del { display: none !important; }
    .print-official-header {
      display: flex !important; align-items: center; gap: 16px;
      border-bottom: 2.5px solid #0f172a; padding-bottom: 14px; margin-bottom: 20px;
    }
    .poh-logo { width: 65px; height: auto; object-fit: contain; }
    .poh-title-box h3 { font-size: 1.15rem; font-weight: 900; color: #0f172a; margin: 0; }
    .poh-title-box h4 { font-size: .9rem; font-weight: 800; color: #1b7505; margin: 2px 0; }
    .poh-title-box p { font-size: .8rem; font-weight: 800; color: #475569; margin: 2px 0; }

    .print-official-firmas {
      display: flex !important; justify-content: space-around;
      margin-top: 50px; padding-top: 20px; break-inside: avoid;
    }
    .pof-col { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; }
    .pof-line { width: 220px; border-top: 1.5px solid #334155; margin-bottom: 6px; }
    .pof-col span { font-size: .78rem; font-weight: 800; color: #0f172a; }
    .pof-col small { font-size: .7rem; color: #64748b; }

    .card-detail { break-inside: avoid; border: 1px solid #ddd !important; }
  }
</style>
