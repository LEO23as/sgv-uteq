<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import Pagination from '$lib/Pagination.svelte';

  let periodos = $state([]);
  let loading = $state(true);
  let q = $state('');

  // Paginación
  let page = $state(1);
  let pageSize = $state(10);

  onMount(async () => {
    try { periodos = await fetchAPI('/api/periodos/'); }
    catch { toast.error('Error al cargar períodos académicos'); }
    finally { loading = false; }
  });

  let filtered = $derived(periodos.filter(p =>
    p.nombre.toLowerCase().includes(q.toLowerCase()) ||
    p.codigo.toLowerCase().includes(q.toLowerCase())
  ));

  const paginatedPeriodos = $derived(
    filtered.slice((page - 1) * pageSize, page * pageSize)
  );

  async function toggle(id, activo) {
    try {
      await fetch(`/api/periodos/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({activo: !activo}),
      });
      periodos = periodos.map(p => p.id_periodo === id ? {...p, activo: !activo} : p);
      toast.success(activo ? 'Período desactivado' : 'Período activado');
    } catch {
      toast.error('Error al actualizar estado del período');
    }
  }
</script>

<svelte:head><title>Períodos — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Períodos Académicos</span>
  </nav>
  <a href="/periodos/nuevo" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nuevo período</a>
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-calendar3"></i> Períodos Académicos</h2>
      <p class="page-sub">Gestión de ciclos académicos ordinarios y extraordinarios (SPA / PPA)</p>
    </div>
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar período..." oninput={() => page = 1} />
    </div>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando períodos...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre del Período</th>
            <th>Tipo</th>
            <th>Fecha Inicio</th>
            <th>Fecha Fin</th>
            <th>Estado</th>
            <th style="text-align: center;">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedPeriodos as p}
            <tr>
              <td><span class="code">{p.codigo}</span></td>
              <td class="font-semibold">{p.nombre}</td>
              <td>
                <span class="badge {p.tipo === 'SPA' ? 'renovado' : 'propuesto'}">{p.tipo}</span>
              </td>
              <td class="txt-sm">{p.fecha_inicio || '—'}</td>
              <td class="txt-sm">{p.fecha_fin || '—'}</td>
              <td>
                <span class="badge" class:activo={p.activo} class:inactivo={!p.activo}>
                  {p.activo ? 'Activo' : 'Inactivo'}
                </span>
              </td>
              <td>
                <div class="acciones center">
                  <a href="/periodos/{p.id_periodo}" class="btn-accion editar" title="Editar período">
                    <i class="bi bi-pencil"></i>
                  </a>
                  <button class="btn-accion {p.activo ? 'danger' : 'success'}"
                    onclick={() => toggle(p.id_periodo, p.activo)}
                    title={p.activo ? 'Desactivar' : 'Activar'}>
                    <i class="bi bi-{p.activo ? 'toggle-on' : 'toggle-off'}"></i>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
          {#if filtered.length === 0}
            <tr><td colspan="7" class="empty">No se encontraron períodos</td></tr>
          {/if}
        </tbody>
      </table>

      {#if filtered.length > 0}
        <Pagination totalItems={filtered.length} bind:page bind:pageSize itemLabel="períodos" />
      {/if}
    </div>
  {/if}
</div>

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:10px 24px;background:#fff;border-bottom:1px solid #e2e8f0; }
.btn-nuevo { display:inline-flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:8px 16px;border-radius:9px;font-weight:700;font-size:.85rem;text-decoration:none;transition:background .15s ease; }
.btn-nuevo:hover { background:#145c04; }

.font-semibold { font-weight:600; color:#1e293b; }
.txt-sm { font-size:.78rem; color:#475569; }
.center { text-align:center; justify-content:center; }
.acciones { display:flex;gap:6px;align-items:center; }
</style>
