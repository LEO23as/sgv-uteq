<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';
  import Pagination from '$lib/Pagination.svelte';
  import ProyectoDetalleModal from '$lib/ProyectoDetalleModal.svelte';

  let items     = $state([]);
  let facultades = $state([]);
  let loading   = $state(true);

  let q         = $state('');
  let filtEst   = $state('');
  let filtFac   = $state('');

  // Modal de Detalle
  let modalProyectoId = $state(null);
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
      [items, facultades] = await Promise.all([
        fetchAPI('/api/proyectos/'),
        fetchAPI('/api/facultades/'),
      ]);
    } finally { loading = false; }
  });

  let filtered = $derived(items.filter(p => {
    const matchQ = !q ||
      p.nombre.toLowerCase().includes(q.toLowerCase()) ||
      p.codigo.toLowerCase().includes(q.toLowerCase());
    const matchE = !filtEst || p.estado === filtEst;
    const matchF = !filtFac || String(p.facultad_nombre) === String(
      facultades.find(f => String(f.id_facultad) === filtFac)?.nombre || filtFac
    );
    return matchQ && matchE && matchF;
  }));

  const paginatedProjects = $derived(
    filtered.slice((page - 1) * pageSize, page * pageSize)
  );

  function limpiar() { q = ''; filtEst = ''; filtFac = ''; page = 1; }

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

<svelte:head><title>Proyectos — SGV</title></svelte:head>

<!-- SUBBAR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Proyectos</span>
  </nav>
  <a href="/proyectos/nuevo" class="btn-nuevo">
    <i class="bi bi-plus-lg"></i> Nuevo proyecto
  </a>
</div>

<div class="page-wrap">
  <!-- CABECERA -->
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-folder2-open"></i> Proyectos de Vinculación</h2>
      <p class="page-sub">Registro, seguimiento y avance cronológico de proyectos con la sociedad</p>
    </div>
  </div>

  <!-- FILTROS -->
  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar por nombre o código…" oninput={() => page = 1} />
    </div>
    <select bind:value={filtFac} onchange={() => page = 1}>
      <option value="">Todas las facultades</option>
      {#each facultades as f}
        <option value={f.id_facultad}>{f.nombre_corto || f.nombre}</option>
      {/each}
    </select>
    <select bind:value={filtEst} onchange={() => page = 1}>
      <option value="">Todos los estados</option>
      {#each Object.entries(ESTADOS) as [val, info]}
        <option value={val}>{info.label}</option>
      {/each}
    </select>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando proyectos...</div>
  {:else}
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
                  <a href="/proyectos/{p.id_proyecto}/editar" class="btn-accion editar" title="Editar">
                    <i class="bi bi-pencil"></i>
                  </a>
                  <button class="btn-accion eliminar" title="Eliminar" onclick={() => eliminarProyecto(p)}>
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
          {#if filtered.length === 0}
            <tr><td colspan="7" class="empty">No se encontraron proyectos</td></tr>
          {/if}
        </tbody>
      </table>

      {#if filtered.length > 0}
        <Pagination totalItems={filtered.length} bind:page bind:pageSize itemLabel="proyectos" />
      {/if}
    </div>
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
.btn-nuevo { display:inline-flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:8px 16px;border-radius:9px;font-weight:700;font-size:.85rem;text-decoration:none;transition:background .15s ease; }
.btn-nuevo:hover { background:#145c04; }

.nombre-cell { max-width: 260px; }
.nombre-principal { display:block;font-weight:700;color:#1e293b; }
.nombre-sec { display:block;font-size:.72rem;color:#64748b;margin-top:2px; }
.fac-badge { display:inline-block;background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:6px;width:fit-content; }
.carrera-sec { display:block;font-size:.72rem;color:#64748b;margin-top:3px; }
.txt-small { font-size:.78rem; color:#475569; }
.center { text-align:center; justify-content:center; }
.acciones { display:flex;gap:6px;align-items:center; }
.avance-col { width: 100%; min-width: 150px; }

.filtros-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
.filtros-row select { border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 8px 12px; font-size: .84rem; background: #fff; color: #334155; }
.btn-limpiar { background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; border-radius: 9px; padding: 8px 16px; font-weight: 600; font-size: .84rem; cursor: pointer; }
.btn-limpiar:hover { background: #e2e8f0; }
</style>
