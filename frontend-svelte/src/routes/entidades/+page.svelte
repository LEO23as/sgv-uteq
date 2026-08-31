<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import Pagination from '$lib/Pagination.svelte';

  let items = $state([]);
  let tipos = $state([]);
  let loading = $state(true);
  let q = $state('');
  let filtTipo = $state('');
  let filtEstado = $state('');

  // Paginación
  let page = $state(1);
  let pageSize = $state(10);

  onMount(async () => {
    try {
      const [ents, tipoData] = await Promise.all([
        fetchAPI('/api/entidades/'),
        fetch('/api/entidades/create/', { credentials:'include' }).then(r => r.json()),
      ]);
      items = ents;
      tipos = tipoData.tipos || [];
    } finally { loading = false; }
  });

  let filtered = $derived(items.filter(e => {
    const matchQ = !q ||
      e.nombre.toLowerCase().includes(q.toLowerCase()) ||
      (e.ruc || '').includes(q);
    const matchT = !filtTipo || String(e.id_tipo) === filtTipo;
    const matchE = !filtEstado ||
      (filtEstado === 'activa' && e.activo) ||
      (filtEstado === 'inactiva' && !e.activo);
    return matchQ && matchT && matchE;
  }));

  const paginatedEntidades = $derived(
    filtered.slice((page - 1) * pageSize, page * pageSize)
  );

  function limpiar() { q = ''; filtTipo = ''; filtEstado = ''; page = 1; }

  async function toggle(id, activo) {
    try {
      await fetch(`/api/entidades/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({activo: !activo}),
      });
      items = items.map(e => e.id_entidad === id ? {...e, activo: !activo} : e);
      toast.success(activo ? 'Entidad desactivada' : 'Entidad activada');
    } catch {
      toast.error('Error al cambiar estado de la entidad');
    }
  }
</script>

<svelte:head><title>Entidades — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Entidades cooperantes</span>
  </nav>
  <a href="/entidades/nueva" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nueva entidad</a>
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-building"></i> Entidades Cooperantes</h2>
      <p class="page-sub">GADs, hospitales, escuelas, empresas y organizaciones aliadas</p>
    </div>
  </div>

  <div class="filtros-row">
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar por nombre o RUC..." oninput={() => page = 1} />
    </div>
    <select bind:value={filtTipo} onchange={() => page = 1}>
      <option value="">Todos los tipos</option>
      {#each tipos as t}
        <option value={String(t.id_tipo)}>{t.nombre}</option>
      {/each}
    </select>
    <select bind:value={filtEstado} onchange={() => page = 1}>
      <option value="">Todos los estados</option>
      <option value="activa">Activas</option>
      <option value="inactiva">Inactivas</option>
    </select>
    <button class="btn-limpiar" onclick={limpiar}>Limpiar</button>
  </div>

  {#if loading}
    <div class="loading"><i class="bi bi-arrow-repeat spin"></i> Cargando entidades...</div>
  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Nombre de la Entidad</th>
            <th>Tipo</th>
            <th>Representante</th>
            <th>Ubicación</th>
            <th>RUC</th>
            <th>Estado</th>
            <th style="text-align: center;">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedEntidades as e}
            <tr>
              <td>
                <span class="nombre-p">{e.nombre}</span>
                {#if e.nombre_corto}<span class="nombre-s">{e.nombre_corto}</span>{/if}
              </td>
              <td><span class="tipo-badge">{e.tipo_nombre}</span></td>
              <td>
                {e.representante_legal || '—'}
                {#if e.cargo_representante}<span class="sec-txt">{e.cargo_representante}</span>{/if}
              </td>
              <td class="txt-sm">{e.canton || '—'}{e.provincia ? ', ' + e.provincia : ''}</td>
              <td class="txt-sm font-semibold">{e.ruc || '—'}</td>
              <td>
                <span class="badge" class:activo={e.activo} class:inactivo={!e.activo}>
                  {e.activo ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td>
                <div class="acciones center">
                  <a href="/entidades/{e.id_entidad}" class="btn-accion editar" title="Editar entidad">
                    <i class="bi bi-pencil"></i>
                  </a>
                  <button class="btn-accion {e.activo ? 'danger' : 'success'}"
                    onclick={() => toggle(e.id_entidad, e.activo)}
                    title={e.activo ? 'Desactivar' : 'Activar'}>
                    <i class="bi bi-{e.activo ? 'toggle-on' : 'toggle-off'}"></i>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
          {#if filtered.length === 0}
            <tr><td colspan="7" class="empty">No se encontraron entidades</td></tr>
          {/if}
        </tbody>
      </table>

      {#if filtered.length > 0}
        <Pagination totalItems={filtered.length} bind:page bind:pageSize itemLabel="entidades" />
      {/if}
    </div>
  {/if}
</div>

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:10px 24px;background:#fff;border-bottom:1px solid #e2e8f0; }
.btn-nuevo { display:inline-flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:8px 16px;border-radius:9px;font-weight:700;font-size:.85rem;text-decoration:none;transition:background .15s ease; }
.btn-nuevo:hover { background:#145c04; }

.nombre-p { font-weight:700; color:#1e293b; }
.nombre-s { display:block;font-size:.72rem;color:#64748b;margin-top:2px; }
.tipo-badge { font-size:.72rem;font-weight:700;color:#15803d;background:#f0fdf4;border:1px solid #bbf7d0;padding:2px 8px;border-radius:6px; }
.sec-txt { display:block;font-size:.72rem;color:#64748b;margin-top:2px; }
.txt-sm { font-size:.78rem; color:#475569; }
.font-semibold { font-weight:600; }
.center { text-align:center; justify-content:center; }
.acciones { display:flex;gap:6px;align-items:center; }

.filtros-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
.filtros-row select { border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 8px 12px; font-size: .84rem; background: #fff; color: #334155; }
.btn-limpiar { background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; border-radius: 9px; padding: 8px 16px; font-weight: 600; font-size: .84rem; cursor: pointer; }
.btn-limpiar:hover { background: #e2e8f0; }
</style>
