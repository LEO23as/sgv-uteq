<script>
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';

  let { idConvenio = null, isOpen = false, onClose } = $props();

  const API = 'http://127.0.0.1:8000';
  let c = $state(null);
  let loading = $state(true);
  let subiendoAnexo = $state(false);
  let archivoAnexo = $state(null);
  let tipoDoc = $state('');
  let descDoc = $state('');

  const ESTADOS = {
    VIGENTE:   { label:'Vigente',   cls:'vigente'  },
    VENCIDO:   { label:'Vencido',   cls:'vencido'  },
    RENOVADO:  { label:'Renovado',  cls:'renovado' },
    CANCELADO: { label:'Cancelado', cls:'cancelado'},
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

  function calcularVigencia(fechaInicio, fechaFin, duracionAnios = 1) {
    let fin = parsearFecha(fechaFin);
    let ini = parsearFecha(fechaInicio);

    if (!fin && ini && duracionAnios) {
      fin = new Date(ini);
      fin.setFullYear(fin.getFullYear() + Number(duracionAnios));
    }

    if (!fin) {
      return { pct: 100, label: 'Indefinido', sub: 'Sin fecha fin', variant: 'info', dias: null };
    }

    if (!ini) {
      ini = new Date(fin);
      ini.setFullYear(ini.getFullYear() - (duracionAnios || 1));
    }

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const finN = new Date(fin); finN.setHours(0, 0, 0, 0);
    const iniN = new Date(ini); iniN.setHours(0, 0, 0, 0);

    const totalMs = finN.getTime() - iniN.getTime();
    const restMs = finN.getTime() - hoy.getTime();
    const restDias = Math.ceil(restMs / (1000 * 60 * 60 * 24));

    if (totalMs <= 0 || restDias <= 0) {
      return { pct: 100, label: 'Convenio Vencido', sub: `Finalizó ${formatFechaLocal(fin)}`, variant: 'danger', dias: restDias };
    }

    const transcurridoMs = hoy.getTime() - iniN.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurridoMs / totalMs) * 100)));

    if (restDias <= 60) {
      return { pct, label: `${restDias}d restantes`, sub: `Vence ${formatFechaLocal(fin)}`, variant: 'warning', dias: restDias };
    }

    return { pct, label: `${restDias}d restantes`, sub: `Hasta ${formatFechaLocal(fin)}`, variant: 'success', dias: restDias };
  }

  $effect(() => {
    if (isOpen && idConvenio) {
      cargarConvenio(idConvenio);
    } else {
      c = null;
    }
  });

  async function cargarConvenio(id) {
    loading = true;
    try {
      const res = await fetch(`/api/convenios/${id}/`, { credentials:'include' });
      if (res.ok) {
        c = await res.json();
      } else {
        toast.error('No se pudo cargar el convenio');
      }
    } catch {
      toast.error('Error de conexión al cargar datos');
    } finally {
      loading = false;
    }
  }

  function iconAnexo(nombre) {
    const ext = nombre.split('.').pop().toLowerCase();
    if (ext === 'pdf') return 'bi-file-pdf';
    if (['doc','docx'].includes(ext)) return 'bi-file-word';
    if (['xls','xlsx'].includes(ext)) return 'bi-file-excel';
    return 'bi-file-earmark';
  }

  async function subirAnexo(e) {
    const file = e.target.files[0];
    if (!file) return;
    archivoAnexo = file;
  }

  async function confirmarAnexo() {
    if (!archivoAnexo || !idConvenio) return;
    subiendoAnexo = true;
    const fd = new FormData();
    fd.append('archivo', archivoAnexo);
    if (tipoDoc) fd.append('tipo_documento', tipoDoc);
    if (descDoc) fd.append('descripcion', descDoc);
    try {
      const res = await fetch(`/api/convenios/${idConvenio}/anexos/`, {
        method:'POST', credentials:'include', body:fd,
      });
      const data = await res.json();
      if (res.ok) {
        c.anexos = [...(c.anexos || []), data];
        archivoAnexo = null; tipoDoc = ''; descDoc = '';
        toast.success('Anexo institucional subido con éxito');
      } else {
        toast.error(data.error || 'Error al subir anexo');
      }
    } catch {
      toast.error('Error de conexión al subir anexo');
    } finally { subiendoAnexo = false; }
  }

  async function eliminarAnexo(a) {
    const ok = await confirmDialog({
      title: '¿Eliminar anexo?',
      message: `Se eliminará "${a.nombre_archivo}". Esta acción no se puede revertir.`,
      confirmText: 'Sí, eliminar',
      type: 'danger'
    });
    if (!ok) return;

    try {
      const res = await fetch(`/api/anexos/${a.id_anexo}/`, { method:'DELETE', credentials:'include' });
      if (res.ok) {
        c.anexos = c.anexos.filter(x => x.id_anexo !== a.id_anexo);
        toast.success('Anexo eliminado');
      } else {
        toast.error('No se pudo eliminar el anexo');
      }
    } catch {
      toast.error('Error de conexión');
    }
  }

  function onKeydown(e) {
    if (e.key === 'Escape' && isOpen) {
      onClose?.();
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if isOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="modal-backdrop" onclick={() => onClose?.()}>
    <div class="modal-card" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      
      <!-- CABECERA DEL MODAL -->
      <div class="modal-header">
        <div class="mh-left">
          <div class="mh-meta"><i class="bi bi-shield-check"></i> Convenio Institucional</div>
          <h2 class="mh-title">{c?.numero_memorando || (loading ? 'Cargando...' : 'Sin número de memorando')}</h2>
          {#if c}
            <p class="mh-sub">{c.entidad_nombre} · {c.periodo_nombre || 'Período actual'}</p>
          {/if}
        </div>
        <div class="mh-right">
          {#if c}
            <span class="badge {ESTADOS[c.estado]?.cls || 'cancelado'}">
              {ESTADOS[c.estado]?.label || c.estado}
            </span>
          {/if}
          <button class="btn-close-x" onclick={() => onClose?.()} title="Cerrar modal">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>

      <!-- CUERPO DEL MODAL -->
      <div class="modal-body">
        {#if loading}
          <div class="loading-box"><i class="bi bi-arrow-repeat spin"></i> Cargando información del convenio...</div>
        {:else if c}
          {@const vig = calcularVigencia(c.fecha_inicio || c.fecha_firma, c.fecha_fin, c.duracion_anios)}
          
          <!-- BANNER DE PROGRESO DE VIGENCIA -->
          <div class="vigencia-box">
            <div class="vb-head">
              <span class="vb-title"><i class="bi bi-clock-history"></i> Vigencia del Acuerdo</span>
              <span class="badge badge-{vig.variant}">{vig.label}</span>
            </div>
            <ProgressBar
              value={vig.pct}
              max={100}
              label={vig.sub}
              sublabel="{formatFechaLocal(c.fecha_inicio || c.fecha_firma)} → {formatFechaLocal(c.fecha_fin)}"
              showPercentage={true}
              variant={vig.variant}
              size="md"
            />
          </div>

          <div class="grid-details">
            <!-- Datos del convenio -->
            <div class="card-detail">
              <h4 class="card-detail-title"><i class="bi bi-file-text-fill"></i> Datos del Convenio</h4>
              <div class="info-grid">
                <div class="info-item"><span class="il">N° Memorando</span><span class="iv">{c.numero_memorando || '—'}</span></div>
                <div class="info-item"><span class="il">Fecha Firma</span><span class="iv">{formatFechaLocal(c.fecha_firma)}</span></div>
                <div class="info-item"><span class="il">Fecha Inicio</span><span class="iv">{formatFechaLocal(c.fecha_inicio)}</span></div>
                <div class="info-item"><span class="il">Fecha Fin</span><span class="iv">{formatFechaLocal(c.fecha_fin)}</span></div>
                <div class="info-item"><span class="il">Duración</span><span class="iv">{c.duracion_anios || 1} año(s)</span></div>
                <div class="info-item"><span class="il">Estudiantes Asignados</span><span class="iv font-bold">{c.estudiantes_asignados || 0}</span></div>
                {#if c.proyecto_nombre}
                  <div class="info-item full"><span class="il">Proyecto Vinculado</span><span class="iv text-green">{c.proyecto_nombre}</span></div>
                {/if}
                {#if c.observaciones}
                  <div class="info-item full"><span class="il">Observaciones</span><span class="iv">{c.observaciones}</span></div>
                {/if}
              </div>
            </div>

            <!-- Entidad cooperante -->
            <div class="card-detail">
              <h4 class="card-detail-title"><i class="bi bi-building-fill"></i> Entidad Cooperante</h4>
              <div class="info-grid">
                <div class="info-item full"><span class="il">Nombre Institucional</span><span class="iv font-bold">{c.entidad_nombre}</span></div>
                {#if c.entidad_representante}<div class="info-item"><span class="il">Representante</span><span class="iv">{c.entidad_representante}</span></div>{/if}
                {#if c.entidad_cargo}<div class="info-item"><span class="il">Cargo</span><span class="iv">{c.entidad_cargo}</span></div>{/if}
                {#if c.entidad_canton}<div class="info-item"><span class="il">Cantón / Provincia</span><span class="iv">{c.entidad_canton}{c.entidad_provincia ? `, ${c.entidad_provincia}` : ''}</span></div>{/if}
                {#if c.entidad_telefono}<div class="info-item"><span class="il">Teléfono</span><span class="iv">{c.entidad_telefono}</span></div>{/if}
                {#if c.entidad_correo}<div class="info-item full"><span class="il">Correo</span><span class="iv">{c.entidad_correo}</span></div>{/if}
              </div>
            </div>

            <!-- Anexos y Documentos -->
            <div class="card-detail full-col">
              <h4 class="card-detail-title"><i class="bi bi-paperclip"></i> Anexos y Documentos de Respaldo ({c.anexos?.length || 0})</h4>

              <!-- Subida -->
              <div class="anexo-upload-row">
                <label class="anexo-file-btn" class:selected={!!archivoAnexo}>
                  <input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png" onchange={subirAnexo} />
                  <i class="bi bi-{archivoAnexo ? 'check-circle-fill' : 'cloud-arrow-up'}"></i>
                  <span>{archivoAnexo ? archivoAnexo.name : 'Adjuntar documento...'}</span>
                </label>
                {#if archivoAnexo}
                  <input class="anexo-input" bind:value={tipoDoc} placeholder="Tipo (ej: Convenio firmado)" />
                  <input class="anexo-input" bind:value={descDoc} placeholder="Descripción breve..." />
                  <button class="btn-subir-anexo" onclick={confirmarAnexo} disabled={subiendoAnexo}>
                    {#if subiendoAnexo}<i class="bi bi-arrow-repeat spin"></i>{:else}<i class="bi bi-upload"></i> Subir{/if}
                  </button>
                {/if}
              </div>

              {#if c.anexos?.length}
                <div class="anexos-list">
                  {#each c.anexos as a}
                    <div class="anexo-item">
                      <i class="bi {iconAnexo(a.nombre_archivo)} anexo-ic"></i>
                      <div class="anexo-txt">
                        <span class="anexo-name">{a.nombre_archivo}</span>
                        <span class="anexo-sub">{a.tipo_documento || 'Documento'} · {a.tamanio_kb || 0} KB</span>
                      </div>
                      <a href={API + a.url} target="_blank" class="btn-anexo dl" title="Descargar anexo">
                        <i class="bi bi-download"></i>
                      </a>
                      <button class="btn-anexo del" onclick={() => eliminarAnexo(a)} title="Eliminar anexo">
                        <i class="bi bi-trash"></i>
                      </button>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="empty-docs">No hay anexos ni documentos de respaldo registrados para este convenio.</p>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <!-- FOOTER DEL MODAL -->
      <div class="modal-footer">
        <button type="button" class="btn-modal-close" onclick={() => onClose?.()}>
          Cerrar
        </button>
        {#if c}
          <a href="/convenios/{c.id_convenio}/editar" class="btn-modal-edit">
            <i class="bi bi-pencil-square"></i> Editar Convenio
          </a>
        {/if}
      </div>

    </div>
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
    max-width: 860px;
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

  .mh-meta { font-size: .72rem; font-weight: 800; color: #1b7505; text-transform: uppercase; letter-spacing: .4px; display: flex; align-items: center; gap: 5px; margin-bottom: 2px; }
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

  .vigencia-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .vb-head { display: flex; justify-content: space-between; align-items: center; }
  .vb-title { font-size: .86rem; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 6px; }

  .grid-details { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
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

  .anexo-upload-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px dashed #cbd5e1; }
  .anexo-file-btn { display: inline-flex; align-items: center; gap: 6px; background: #fff; border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 6px; font-size: .8rem; font-weight: 600; color: #475569; cursor: pointer; }
  .anexo-file-btn input { display: none; }
  .anexo-file-btn.selected { background: #dcfce7; border-color: #86efac; color: #15803d; }
  .anexo-input { flex: 1; min-width: 140px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: .8rem; }
  .btn-subir-anexo { background: #1b7505; color: #fff; border: none; border-radius: 6px; padding: 6px 14px; font-size: .8rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 5px; }
  .btn-subir-anexo:hover { background: #145c04; }

  .anexos-list { display: flex; flex-direction: column; gap: 6px; }
  .anexo-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
  .anexo-ic { font-size: 1.15rem; color: #1b7505; }
  .anexo-txt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
  .anexo-name { font-size: .82rem; font-weight: 700; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .anexo-sub { font-size: .72rem; color: #64748b; }
  .btn-anexo { width: 28px; height: 28px; border-radius: 6px; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; text-decoration: none; font-size: .8rem; }
  .btn-anexo.dl { background: #e0f2fe; color: #0284c7; }
  .btn-anexo.del { background: #fee2e2; color: #dc2626; }
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
  .btn-modal-close { background: #ffffff; border: 1px solid #cbd5e1; color: #475569; padding: 8px 18px; border-radius: 8px; font-weight: 600; font-size: .84rem; cursor: pointer; }
  .btn-modal-close:hover { background: #f1f5f9; }
  .btn-modal-edit { background: #1b7505; color: #ffffff; border: none; padding: 8px 18px; border-radius: 8px; font-weight: 700; font-size: .84rem; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
  .btn-modal-edit:hover { background: #145c04; }

  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes popIn { from { opacity: 0; transform: scale(.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }

  @media (max-width: 640px) {
    .grid-details { grid-template-columns: 1fr; }
    .full-col { grid-column: span 1; }
    .info-grid { grid-template-columns: 1fr; }
    .info-item.full { grid-column: span 1; }
  }
</style>
