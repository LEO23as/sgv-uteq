<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';

  const API = 'http://127.0.0.1:8000';
  const id = $derived($page.params.id);
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

  function calcularVigencia(fechaInicio, fechaFin) {
    if (!fechaFin) return { pct: 100, label: 'Sin fecha de fin definida', variant: 'info', rest: null };
    const fin = new Date(fechaFin);
    const ini = fechaInicio ? new Date(fechaInicio) : new Date(fin.getFullYear() - 1, fin.getMonth(), fin.getDate());
    const hoy = new Date();
    
    const total = fin.getTime() - ini.getTime();
    if (total <= 0) return { pct: 100, label: 'Plazo culminado (Vencido)', variant: 'danger', rest: 0 };
    
    const rest = Math.ceil((fin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    const transcurrido = hoy.getTime() - ini.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurrido / total) * 100)));
    
    if (rest <= 0) {
      return { pct: 100, label: 'Convenio Vencido', variant: 'danger', rest };
    } else if (rest <= 90) {
      return { pct, label: `${rest} días restantes para vencer`, variant: 'warning', rest };
    } else {
      return { pct, label: `${rest} días de vigencia restantes`, variant: 'success', rest };
    }
  }

  onMount(async () => {
    try {
      const res = await fetch(`/api/convenios/${id}/`, { credentials:'include' });
      if (res.ok) {
        c = await res.json();
      } else {
        toast.error('No se encontró el convenio especificado');
      }
    } catch {
      toast.error('Error al cargar datos del convenio');
    } finally { loading = false; }
  });

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
    if (!archivoAnexo) return;
    subiendoAnexo = true;
    const fd = new FormData();
    fd.append('archivo', archivoAnexo);
    if (tipoDoc) fd.append('tipo_documento', tipoDoc);
    if (descDoc) fd.append('descripcion', descDoc);
    try {
      const res = await fetch(`/api/convenios/${id}/anexos/`, {
        method:'POST', credentials:'include', body:fd,
      });
      const data = await res.json();
      if (res.ok) {
        c.anexos = [...(c.anexos || []), data];
        archivoAnexo = null; tipoDoc = ''; descDoc = '';
        toast.success('Anexo institucional subido con éxito');
      } else {
        toast.error(data.error || 'Error al subir el anexo');
      }
    } catch {
      toast.error('Error de conexión al subir anexo');
    } finally { subiendoAnexo = false; }
  }

  async function eliminarAnexo(a) {
    const ok = await confirmDialog({
      title: '¿Eliminar documento anexo?',
      message: `Se eliminará el archivo "${a.nombre_archivo}". Esta acción no se puede revertir.`,
      confirmText: 'Sí, eliminar archivo',
      type: 'danger'
    });
    if (!ok) return;

    try {
      const res = await fetch(`/api/anexos/${a.id_anexo}/`, { method:'DELETE', credentials:'include' });
      if (res.ok) {
        c.anexos = c.anexos.filter(x => x.id_anexo !== a.id_anexo);
        toast.success('Anexo eliminado del convenio');
      } else {
        toast.error('No se pudo eliminar el anexo');
      }
    } catch {
      toast.error('Error de conexión al eliminar anexo');
    }
  }
</script>

<svelte:head><title>Detalle Convenio — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/convenios">Convenios</a>
    <span class="sep">/</span>
    <span class="current">Detalle</span>
  </nav>
  {#if c}
    <a href="/convenios/{id}/editar" class="btn-editar"><i class="bi bi-pencil"></i> Editar convenio</a>
  {/if}
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando información del convenio...</div>
{:else if c}
{@const vig = calcularVigencia(c.fecha_inicio || c.fecha_firma, c.fecha_fin)}
<div class="detalle-wrap">

  <!-- HEADER -->
  <div class="header-card">
    <div>
      <div class="hc-meta-tag"><i class="bi bi-shield-check"></i> Registro Oficial de Convenio</div>
      <h1 class="hc-title">{c.numero_memorando || 'Sin número de memorando'}</h1>
      <p class="hc-sub">{c.entidad_nombre} · {c.periodo_nombre}</p>
    </div>
    <div class="header-badge-wrap">
      <span class="badge {ESTADOS[c.estado]?.cls || 'cancelado'}">
        {ESTADOS[c.estado]?.label || c.estado}
      </span>
    </div>
  </div>

  <!-- BANNER DE PROGRESO DE VIGENCIA -->
  <div class="vigencia-card">
    <div class="vigencia-header">
      <div class="vh-title">
        <i class="bi bi-clock-history"></i>
        <span>Vigencia del Acuerdo Interinstitucional</span>
      </div>
      <span class="vh-badge badge-{vig.variant}">{vig.label}</span>
    </div>
    <ProgressBar
      value={vig.pct}
      max={100}
      label="Tiempo transcurrido del periodo del convenio"
      sublabel="{c.fecha_inicio || c.fecha_firma || 'Inicio'} → {c.fecha_fin || 'Vigencia actual'}"
      showPercentage={true}
      variant={vig.variant}
      size="md"
      animated={c.estado === 'VIGENTE'}
    />
  </div>

  <div class="detalle-grid">
    <!-- Datos del convenio -->
    <div class="sec-card">
      <h3 class="sec-title"><i class="bi bi-file-text-fill"></i> Datos del convenio</h3>
      <div class="info-grid">
        {#if c.numero_memorando}<div class="info-item"><span class="il">N° Memorando</span><span class="iv">{c.numero_memorando}</span></div>{/if}
        {#if c.fecha_firma}<div class="info-item"><span class="il">Fecha de firma</span><span class="iv">{c.fecha_firma}</span></div>{/if}
        {#if c.fecha_inicio}<div class="info-item"><span class="il">Fecha inicio</span><span class="iv">{c.fecha_inicio}</span></div>{/if}
        {#if c.fecha_fin}<div class="info-item"><span class="il">Fecha fin</span><span class="iv">{c.fecha_fin}</span></div>{/if}
        <div class="info-item"><span class="il">Duración</span><span class="iv">{c.duracion_anios || 1} año(s)</span></div>
        <div class="info-item"><span class="il">Estudiantes asignados</span><span class="iv">{c.estudiantes_asignados || 0}</span></div>
        {#if c.proyecto_nombre}
          <div class="info-item full"><span class="il">Proyecto Vinculado</span><span class="iv">{c.proyecto_nombre}</span></div>
        {/if}
        {#if c.observaciones}
          <div class="info-item full"><span class="il">Observaciones</span><span class="iv">{c.observaciones}</span></div>
        {/if}
      </div>
    </div>

    <!-- Entidad cooperante -->
    <div class="sec-card">
      <h3 class="sec-title"><i class="bi bi-building-fill"></i> Entidad cooperante</h3>
      <div class="info-grid">
        <div class="info-item full"><span class="il">Nombre Institucional</span><span class="iv">{c.entidad_nombre}</span></div>
        {#if c.entidad_siglas}<div class="info-item"><span class="il">Siglas</span><span class="iv">{c.entidad_siglas}</span></div>{/if}
        {#if c.entidad_representante}<div class="info-item"><span class="il">Representante Legal</span><span class="iv">{c.entidad_representante}</span></div>{/if}
        {#if c.entidad_cargo}<div class="info-item"><span class="il">Cargo</span><span class="iv">{c.entidad_cargo}</span></div>{/if}
        {#if c.entidad_provincia}<div class="info-item"><span class="il">Provincia</span><span class="iv">{c.entidad_provincia}</span></div>{/if}
        {#if c.entidad_canton}<div class="info-item"><span class="il">Cantón</span><span class="iv">{c.entidad_canton}</span></div>{/if}
        {#if c.entidad_telefono}<div class="info-item"><span class="il">Teléfono</span><span class="iv">{c.entidad_telefono}</span></div>{/if}
        {#if c.entidad_correo}<div class="info-item"><span class="il">Correo</span><span class="iv">{c.entidad_correo}</span></div>{/if}
      </div>
    </div>

    <!-- Anexos -->
    <div class="sec-card full-col">
      <h3 class="sec-title"><i class="bi bi-paperclip"></i> Anexos y Documentos de Respaldo</h3>

      <!-- Subir -->
      <div class="anexo-form">
        <label class="anexo-file" class:selected={!!archivoAnexo}>
          <input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png" onchange={subirAnexo} />
          <i class="bi bi-{archivoAnexo ? 'check-circle-fill' : 'cloud-arrow-up'}"></i>
          <span>{archivoAnexo ? archivoAnexo.name : 'Seleccionar documento o resolución escaneada'}</span>
        </label>
        {#if archivoAnexo}
          <input class="anexo-input" bind:value={tipoDoc} placeholder="Tipo de documento (ej: Convenio firmado, Adenda...)" />
          <input class="anexo-input" bind:value={descDoc} placeholder="Descripción breve del documento..." />
          <button class="btn-subir" onclick={confirmarAnexo} disabled={subiendoAnexo}>
            {#if subiendoAnexo}<i class="bi bi-arrow-repeat spin"></i> Subiendo...{:else}<i class="bi bi-upload"></i> Subir Anexo{/if}
          </button>
        {/if}
      </div>

      {#if subiendoAnexo}
        <div style="margin-top: 10px;">
          <ProgressBar value={100} animated={true} striped={true} label="Subiendo y procesando archivo en el servidor..." size="sm" />
        </div>
      {/if}

      <!-- Lista de anexos -->
      {#if c.anexos?.length}
        <div class="anexos-list">
          {#each c.anexos as a}
            <div class="anexo-item">
              <i class="bi {iconAnexo(a.nombre_archivo)} anexo-icon"></i>
              <div class="anexo-info">
                <span class="anexo-nombre">{a.nombre_archivo}</span>
                <span class="anexo-meta">
                  {a.tipo_documento || 'Documento'} · {a.tamanio_kb || 0} KB
                  {#if a.descripcion} · {a.descripcion}{/if}
                </span>
              </div>
              <a href={API + a.url} target="_blank" class="btn-dl" title="Descargar anexo">
                <i class="bi bi-download"></i>
              </a>
              <button class="btn-del" onclick={() => eliminarAnexo(a)} title="Eliminar anexo">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          {/each}
        </div>
      {:else}
        <p class="empty-side">Sin anexos o documentos registrados para este convenio.</p>
      {/if}
    </div>
  </div>
</div>
{:else}
  <div class="loading-wrap">Convenio no encontrado</div>
{/if}

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }
.btn-editar { display:flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:6px 14px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.85rem; }
.btn-editar:hover { background:#145c04; }

.loading-wrap { text-align:center;padding:60px 20px;color:#64748b;font-weight:600; }
.detalle-wrap { max-width:1100px;margin:24px auto;padding:0 20px;display:flex;flex-direction:column;gap:18px; }

.header-card { background:#fff;border-radius:14px;padding:22px 26px;border:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,.04); }
.hc-meta-tag { font-size:.72rem;font-weight:800;text-transform:uppercase;color:#1b7505;letter-spacing:.5px;margin-bottom:4px;display:flex;align-items:center;gap:5px; }
.hc-title { font-size:1.4rem;font-weight:800;color:#0f172a;margin:0 0 4px 0; }
.hc-sub { font-size:.9rem;color:#64748b;margin:0;font-weight:500; }

.vigencia-card { background:#fff;border-radius:14px;padding:18px 24px;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,.04);display:flex;flex-direction:column;gap:10px; }
.vigencia-header { display:flex;justify-content:space-between;align-items:center; }
.vh-title { display:flex;align-items:center;gap:8px;font-weight:700;color:#1e293b;font-size:.92rem; }
.vh-badge { font-size:.75rem;font-weight:700;padding:3px 10px;border-radius:20px; }
.badge-success { background:#e8f8e8;color:#1b7505; }
.badge-warning { background:#fef3c7;color:#b45309; }
.badge-danger { background:#fee2e2;color:#dc2626; }
.badge-info { background:#e0f2fe;color:#0369a1; }

.detalle-grid { display:grid;grid-template-columns:1fr 1fr;gap:18px; }
.sec-card { background:#fff;border-radius:14px;padding:20px 24px;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,.04); }
.full-col { grid-column:span 2; }
.sec-title { font-size:1rem;font-weight:800;color:#1e293b;margin:0 0 16px 0;display:flex;align-items:center;gap:8px;border-bottom:1px solid #f1f5f9;padding-bottom:10px; }

.info-grid { display:grid;grid-template-columns:1fr 1fr;gap:12px 18px; }
.info-item { display:flex;flex-direction:column;gap:2px; }
.info-item.full { grid-column:span 2; }
.il { font-size:.72rem;font-weight:700;text-transform:uppercase;color:#94a3b8;letter-spacing:.3px; }
.iv { font-size:.88rem;color:#1e293b;font-weight:600;word-break:break-word; }

.anexo-form { display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px;background:#f8fafc;padding:12px;border-radius:10px;border:1px dashed #cbd5e1; }
.anexo-file { display:flex;align-items:center;gap:8px;background:#fff;border:1px solid #cbd5e1;padding:8px 14px;border-radius:8px;font-size:.82rem;font-weight:600;color:#475569;cursor:pointer; }
.anexo-file input { display:none; }
.anexo-file.selected { background:#e8f8e8;border-color:#86efac;color:#1b7505; }
.anexo-input { flex:1;min-width:180px;border:1px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:.82rem; }
.btn-subir { background:#1b7505;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:.82rem;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px; }
.btn-subir:hover { background:#145c04; }

.anexos-list { display:flex;flex-direction:column;gap:8px; }
.anexo-item { display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0; }
.anexo-icon { font-size:1.3rem;color:#1b7505; }
.anexo-info { flex:1;min-width:0;display:flex;flex-direction:column;gap:2px; }
.anexo-nombre { font-size:.85rem;font-weight:700;color:#1e293b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.anexo-meta { font-size:.75rem;color:#64748b; }
.btn-dl, .btn-del { width:30px;height:30px;border-radius:6px;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;text-decoration:none;font-size:.85rem; }
.btn-dl { background:#e0f2fe;color:#0369a1; }
.btn-del { background:#fee2e2;color:#dc2626; }
.btn-dl:hover { background:#bae6fd; }
.btn-del:hover { background:#fecaca; }
.empty-side { font-size:.85rem;color:#94a3b8;font-style:italic;margin:6px 0 0 0; }

@media (max-width:768px) {
  .detalle-grid { grid-template-columns:1fr; }
  .full-col { grid-column:span 1; }
  .info-grid { grid-template-columns:1fr; }
  .info-item.full { grid-column:span 1; }
}
</style>
