<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';
  import ProgressBar from '$lib/ProgressBar.svelte';

  let items = $state([]);
  let periodos = $state([]);
  let loading = $state(true);
  let q = $state('');
  let filtEst = $state('');
  let filtPer = $state('');

  const ESTADOS = {
    VIGENTE:   { label:'Vigente',   cls:'vigente'  },
    VENCIDO:   { label:'Vencido',   cls:'vencido'  },
    RENOVADO:  { label:'Renovado',  cls:'renovado' },
    CANCELADO: { label:'Cancelado', cls:'cancelado'},
  };

  function calcularVigencia(fechaInicio, fechaFin) {
    if (!fechaFin) return { pct: 100, label: 'Sin fecha fin', variant: 'info' };
    const fin = new Date(fechaFin);
    const ini = fechaInicio ? new Date(fechaInicio) : new Date(fin.getFullYear() - 1, fin.getMonth(), fin.getDate());
    const hoy = new Date();
    
    const total = fin.getTime() - ini.getTime();
    if (total <= 0) return { pct: 100, label: 'Vencido', variant: 'danger' };
    
    const rest = Math.ceil((fin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
    const transcurrido = hoy.getTime() - ini.getTime();
    const pct = Math.min(100, Math.max(0, Math.round((transcurrido / total) * 100)));
    
    if (rest <= 0) {
      return { pct: 100, label: 'Vencido', variant: 'danger' };
    } else if (rest <= 90) {
      return { pct, label: `${rest}d restantes`, variant: 'warning' };
    } else {
      return { pct, label: `${rest}d restantes`, variant: 'success' };
    }
  }

  async function cargar() {
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
      <p class="page-sub">Acuerdos con entidades cooperantes y seguimiento de vigencia</p>
    </div>
  </div>

  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar entidad, proyecto o memorando..." onkeydown={(e) => e.key === 'Enter' && cargar()} />
    </div>
    <select bind:value={filtEst}>
      <option value="">Todos los estados</option>
      {#each Object.entries(ESTADOS) as [val, info]}
        <option value={val}>{info.label}</option>
      {/each}
    </select>
    <select bind:value={filtPer}>
      <option value="">Todos los períodos</option>
      {#each periodos as p}
        <option value={p.id_periodo}>{p.nombre}</option>
      {/each}
    </select>
    <button class="btn-filtrar" onclick={cargar}>Filtrar</button>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando convenios...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>N° Memorando</th>
            <th>Entidad</th>
            <th>Proyecto</th>
            <th>Período</th>
            <th style="min-width: 140px;">Vigencia / Avance</th>
            <th>Estudiantes</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each items as c}
            {@const vig = calcularVigencia(c.fecha_inicio || c.fecha_firma, c.fecha_fin)}
            <tr>
              <td><strong class="code">{c.numero_memorando || 'Sin Nro.'}</strong></td>
              <td class="td-truncate" title={c.entidad_nombre}>{c.entidad_nombre}</td>
              <td class="td-truncate" title={c.proyecto_nombre || '—'}>{c.proyecto_nombre || '—'}</td>
              <td class="txt-sm">{c.periodo_nombre}</td>
              <td>
                <div class="vigencia-col">
                  <ProgressBar
                    value={vig.pct}
                    max={100}
                    sublabel={vig.label}
                    variant={vig.variant}
                    size="sm"
                  />
                </div>
              </td>
              <td class="txt-sm center">{c.estudiantes_asignados || 0}</td>
              <td>
                <span class="badge {ESTADOS[c.estado]?.cls || 'cancelado'}">
                  {ESTADOS[c.estado]?.label || c.estado}
                </span>
              </td>
              <td class="acciones">
                <a href="/convenios/{c.id_convenio}" class="btn-accion" title="Ver detalle">
                  <i class="bi bi-eye"></i>
                </a>
                <a href="/convenios/{c.id_convenio}/editar" class="btn-accion" title="Editar">
                  <i class="bi bi-pencil"></i>
                </a>
                <button class="btn-accion danger" onclick={() => eliminar(c)} title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          {/each}
          {#if items.length === 0}
            <tr><td colspan="8" class="empty">No se encontraron convenios</td></tr>
          {/if}
        </tbody>
      </table>
    </div>
    <div class="total">{items.length} convenio(s) encontrado(s)</div>
  {/if}
</div>

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:8px 24px;background:#fff;border-bottom:1px solid var(--borde); }
.td-truncate { max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.txt-sm { font-size:.78rem; }
.center { text-align:center; }
.acciones { display:flex;gap:6px; }
.vigencia-col { width: 100%; min-width: 120px; }
</style>
