<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';
  import Pagination from '$lib/Pagination.svelte';
  import ConvenioDetalleModal from '$lib/ConvenioDetalleModal.svelte';
  import InstitutionalLoader from '$lib/InstitutionalLoader.svelte';

  let items = $state([]);
  let periodos = $state([]);
  let loading = $state(true);
  let q = $state('');
  let filtEst = $state('');
  let filtPer = $state('');

  // Modal de Detalle
  let modalDetalleId = $state(null);
  let modalDetalleOpen = $state(false);

  // Paginación
  let page = $state(1);
  let pageSize = $state(10);

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
      return { pct: 100, label: 'Vencido', sub: `Finalizó ${formatFechaLocal(fin)}`, variant: 'danger', dias: restDias };
    }

    const transcurridoMs = hoy.getTime() - iniN.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurridoMs / totalMs) * 100)));

    if (restDias <= 60) {
      return { pct, label: `${restDias}d rest.`, sub: `Vence ${formatFechaLocal(fin)}`, variant: 'warning', dias: restDias };
    }

    return { pct, label: `${restDias}d rest.`, sub: `Hasta ${formatFechaLocal(fin)}`, variant: 'success', dias: restDias };
  }

  async function cargar() {
    page = 1;
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (filtEst) params.set('estado', filtEst);
    if (filtPer) params.set('periodo', filtPer);
    try {
      const data = await fetch('/api/convenios/list/?' + params, { credentials:'include' }).then(r => r.json());
      items = data.results || [];
    } catch {
      toast.error('Error al cargar convenios');
    }
  }

  onMount(async () => {
    try {
      [periodos] = await Promise.all([
        fetchAPI('/api/periodos/'),
      ]);
      await cargar();
    } finally { loading = false; }
  });

  function limpiar() { q = ''; filtEst = ''; filtPer = ''; cargar(); }

  let filtroAlerta = $state(''); // '' | 'vigentes' | 'por_vencer' | 'vencidos'

  let statsConvenios = $derived.by(() => {
    let vigentes = 0;
    let porVencer = 0;
    let vencidos = 0;
    for (const c of items) {
      const vig = calcularVigencia(c.fecha_inicio || c.fecha_firma, c.fecha_fin, c.duracion_anios);
      if (c.estado === 'VENCIDO' || (vig.dias !== null && vig.dias <= 0)) {
        vencidos++;
      } else if (vig.dias !== null && vig.dias <= 60) {
        porVencer++;
      } else {
        vigentes++;
      }
    }
    return { vigentes, porVencer, vencidos, total: items.length };
  });

  let conveniosFiltrados = $derived.by(() => {
    if (!filtroAlerta) return items;
    return items.filter(c => {
      const vig = calcularVigencia(c.fecha_inicio || c.fecha_firma, c.fecha_fin, c.duracion_anios);
      if (filtroAlerta === 'vencidos') {
        return c.estado === 'VENCIDO' || (vig.dias !== null && vig.dias <= 0);
      }
      if (filtroAlerta === 'por_vencer') {
        return c.estado !== 'VENCIDO' && vig.dias !== null && vig.dias > 0 && vig.dias <= 60;
      }
      if (filtroAlerta === 'vigentes') {
        return c.estado === 'VIGENTE' && (vig.dias === null || vig.dias > 60);
      }
      return true;
    });
  });

  function abrirDetalle(id) {
    modalDetalleId = id;
    modalDetalleOpen = true;
  }

  // Elementos paginados
  const paginatedItems = $derived(
    conveniosFiltrados.slice((page - 1) * pageSize, page * pageSize)
  );

  async function eliminar(c) {
    const confirmed = await confirmDialog({
      title: '¿Eliminar convenio?',
      message: `Se eliminará el convenio "${c.numero_memorando || 'sin número'}" con ${c.entidad_nombre}. Esta acción no se puede deshacer.`,
      confirmText: 'Sí, eliminar',
      type: 'danger'
    });

    if (!confirmed) return;

    try {
      const res = await fetch(`/api/convenios/${c.id_convenio}/`, { method:'DELETE', credentials:'include' });
      if (res.ok) {
        items = items.filter(x => x.id_convenio !== c.id_convenio);
        toast.success(`Convenio "${c.numero_memorando || 'seleccionado'}" eliminado correctamente`);
      } else {
        toast.error('No se pudo eliminar el convenio');
      }
    } catch {
      toast.error('Error de conexión al eliminar');
    }
  }
</script>

<svelte:head><title>Convenios — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Convenios</span>
  </nav>
  <a href="/convenios/nuevo" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nuevo convenio</a>
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-file-earmark-text"></i> Gestión de Convenios</h2>
      <p class="page-sub">Acuerdos interinstitucionales y monitoreo de plazos de vigencia</p>
    </div>
  </div>

  <!-- KPI CARDS INSTITUCIONALES DE ALERTA DE CONVENIOS -->
  <div class="kpis-banner">
    <button
      type="button"
      class="kpi-mini-card"
      class:active={filtroAlerta === ''}
      onclick={() => { filtroAlerta = ''; page = 1; }}
    >
      <div class="kmc-icon azul"><i class="bi bi-file-earmark-text"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{statsConvenios.total}</span>
        <span class="kmc-label">Total Convenios</span>
      </div>
    </button>

    <button
      type="button"
      class="kpi-mini-card"
      class:active={filtroAlerta === 'vigentes'}
      onclick={() => { filtroAlerta = filtroAlerta === 'vigentes' ? '' : 'vigentes'; page = 1; }}
    >
      <div class="kmc-icon verde"><i class="bi bi-check-circle-fill"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{statsConvenios.vigentes}</span>
        <span class="kmc-label">Vigentes al Día</span>
      </div>
    </button>

    <button
      type="button"
      class="kpi-mini-card"
      class:active={filtroAlerta === 'por_vencer'}
      onclick={() => { filtroAlerta = filtroAlerta === 'por_vencer' ? '' : 'por_vencer'; page = 1; }}
    >
      <div class="kmc-icon amarillo"><i class="bi bi-exclamation-triangle-fill"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{statsConvenios.porVencer}</span>
        <span class="kmc-label">Por Vencer (&le; 60 días)</span>
      </div>
    </button>

    <button
      type="button"
      class="kpi-mini-card"
      class:active={filtroAlerta === 'vencidos'}
      onclick={() => { filtroAlerta = filtroAlerta === 'vencidos' ? '' : 'vencidos'; page = 1; }}
    >
      <div class="kmc-icon rojo"><i class="bi bi-x-circle-fill"></i></div>
      <div class="kmc-info">
        <span class="kmc-num">{statsConvenios.vencidos}</span>
        <span class="kmc-label">Vencidos / Por Renovar</span>
      </div>
    </button>
  </div>

  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar entidad, proyecto o memorando..." onkeydown={(e) => e.key === 'Enter' && cargar()} />
    </div>
    <select bind:value={filtEst} onchange={cargar}>
      <option value="">Todos los estados</option>
      {#each Object.entries(ESTADOS) as [val, info]}
        <option value={val}>{info.label}</option>
      {/each}
    </select>
    <select bind:value={filtPer} onchange={cargar}>
      <option value="">Todos los períodos</option>
      {#each periodos as p}
        <option value={p.id_periodo}>{p.nombre}</option>
      {/each}
    </select>
    <button class="btn-filtrar" onclick={cargar}>Filtrar</button>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <InstitutionalLoader fullscreen={true} texto="CARGANDO CONVENIOS" subtexto="Consultando convenios interinstitucionales..." />
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>N° Memorando</th>
            <th>Entidad Cooperante</th>
            <th>Proyecto</th>
            <th>Período</th>
            <th style="min-width: 170px;">Vigencia / Plazo</th>
            <th style="text-align: center;">Estudiantes</th>
            <th>Estado</th>
            <th style="text-align: center;">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedItems as c}
            {@const vig = calcularVigencia(c.fecha_inicio || c.fecha_firma, c.fecha_fin, c.duracion_anios)}
            <tr>
              <td>
                <span class="code">{c.numero_memorando || 'Sin Nro.'}</span>
              </td>
              <td class="td-truncate font-semibold" title={c.entidad_nombre}>
                {c.entidad_nombre}
              </td>
              <td class="td-truncate text-muted" title={c.proyecto_nombre || '—'}>
                {c.proyecto_nombre || '—'}
              </td>
              <td class="txt-sm">{c.periodo_nombre || '—'}</td>
              <td>
                <div class="vigencia-col">
                  <ProgressBar
                    value={vig.pct}
                    max={100}
                    label={vig.label}
                    sublabel={vig.sub}
                    variant={vig.variant}
                    size="sm"
                  />
                </div>
              </td>
              <td class="txt-sm center font-bold">{c.estudiantes_asignados || 0}</td>
              <td>
                <span class="badge {ESTADOS[c.estado]?.cls || 'cancelado'}">
                  {ESTADOS[c.estado]?.label || c.estado}
                </span>
              </td>
              <td>
                <div class="acciones center">
                  <button type="button" class="btn-accion" title="Ver detalle del convenio" onclick={() => abrirDetalle(c.id_convenio)}>
                    <i class="bi bi-eye"></i>
                  </button>
                  <a href="/convenios/{c.id_convenio}/editar" class="btn-accion editar" title="Editar convenio">
                    <i class="bi bi-pencil"></i>
                  </a>
                  <button class="btn-accion eliminar" onclick={() => eliminar(c)} title="Eliminar convenio">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
          {#if conveniosFiltrados.length === 0}
            <tr><td colspan="8" class="empty">No se encontraron convenios con el filtro seleccionado</td></tr>
          {/if}
        </tbody>
      </table>

      {#if conveniosFiltrados.length > 0}
        <Pagination totalItems={conveniosFiltrados.length} bind:page bind:pageSize itemLabel="convenios" />
      {/if}
    </div>
  {/if}
</div>

<!-- MODAL DE DETALLE DEL CONVENIO -->
<ConvenioDetalleModal
  idConvenio={modalDetalleId}
  isOpen={modalDetalleOpen}
  onClose={() => { modalDetalleOpen = false; cargar(); }}
/>

<style>
.kpis-banner {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.kpi-mini-card {
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: all .15s ease;
  box-shadow: 0 1px 4px rgba(0,0,0,0.02);
}
.kpi-mini-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  border-color: #cbd5e1;
}
.kpi-mini-card.active {
  border-color: var(--verde, #1b7505);
  background: #fdfefe;
  box-shadow: 0 0 0 2px rgba(27, 117, 5, 0.15);
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
.kmc-label { font-size: .72rem; font-weight: 800; color: #64748b; text-transform: uppercase; }

.subbar { display:flex;align-items:center;justify-content:space-between;padding:10px 24px;background:#fff;border-bottom:1px solid #e2e8f0; }
.btn-nuevo { display:inline-flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:8px 16px;border-radius:9px;font-weight:700;font-size:.85rem;text-decoration:none;transition:background .15s ease; }
.btn-nuevo:hover { background:#145c04; }

.td-truncate { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.font-semibold { font-weight: 600; color: #1e293b; }
.font-bold { font-weight: 700; }
.text-muted { color: #64748b; font-size: .82rem; }
.txt-sm { font-size: .78rem; color: #475569; }
.center { text-align: center; justify-content: center; }
.acciones { display: flex; gap: 6px; align-items: center; }
.vigencia-col { width: 100%; min-width: 150px; }

.filtros-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
.filtros-row select { border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 8px 12px; font-size: .84rem; background: #fff; color: #334155; }
.btn-filtrar { background: #1b7505; color: #fff; border: none; border-radius: 9px; padding: 8px 18px; font-weight: 700; font-size: .84rem; cursor: pointer; }
.btn-filtrar:hover { background: #145c04; }
.btn-limpiar { background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; border-radius: 9px; padding: 8px 16px; font-weight: 600; font-size: .84rem; cursor: pointer; }
.btn-limpiar:hover { background: #e2e8f0; }
</style>
