<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import Pagination from '$lib/Pagination.svelte';
  import InstitutionalLoader from '$lib/InstitutionalLoader.svelte';

  let facultades = $state([]);
  let carreras   = $state([]);
  let loading    = $state(true);
  let tab        = $state('facultades');
  let q          = $state('');

  // Paginación por tab
  let pageFac = $state(1);
  let pageSizeFac = $state(10);
  let pageCar = $state(1);
  let pageSizeCar = $state(10);

  onMount(async () => {
    try {
      [facultades, carreras] = await Promise.all([
        fetchAPI('/api/facultades/'),
        fetchAPI('/api/carreras/'),
      ]);
    } finally { loading = false; }
  });

  let filtFacs = $derived(facultades.filter(f =>
    !q || f.nombre.toLowerCase().includes(q.toLowerCase()) || (f.codigo || '').toLowerCase().includes(q.toLowerCase())
  ));

  let filtCarr = $derived(carreras.filter(c =>
    !q || c.nombre.toLowerCase().includes(q.toLowerCase()) || (c.codigo || '').toLowerCase().includes(q.toLowerCase())
  ));

  let paginatedFacs = $derived(filtFacs.slice((pageFac - 1) * pageSizeFac, pageFac * pageSizeFac));
  let paginatedCarr = $derived(filtCarr.slice((pageCar - 1) * pageSizeCar, pageCar * pageSizeCar));

  async function toggleFac(id, activo) {
    try {
      await fetch(`/api/facultades/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({activo: !activo}),
      });
      facultades = facultades.map(f => f.id_facultad === id ? {...f, activo: !activo} : f);
      toast.success(activo ? 'Facultad desactivada' : 'Facultad activada');
    } catch {
      toast.error('Error al actualizar estado de la facultad');
    }
  }

  async function toggleCarr(id, activo) {
    try {
      await fetch(`/api/carreras/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({activo: !activo}),
      });
      carreras = carreras.map(c => c.id_carrera === id ? {...c, activo: !activo} : c);
      toast.success(activo ? 'Carrera desactivada' : 'Carrera activada');
    } catch {
      toast.error('Error al actualizar estado de la carrera');
    }
  }
</script>

<svelte:head><title>Facultades y Carreras — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Estructura académica</span>
  </nav>
  {#if tab === 'carreras'}
    <a href="/carreras/nueva" class="btn-nuevo"><i class="bi bi-plus-lg"></i> Nueva carrera</a>
  {/if}
</div>

<div class="page-wrap">
  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-diagram-3"></i> Estructura Académica</h2>
      <p class="page-sub">Gestión de facultades y carreras de la universidad</p>
    </div>
    <div class="search-wrap">
      <i class="bi bi-search"></i>
      <input bind:value={q} placeholder="Buscar por nombre o código..." oninput={() => { pageFac = 1; pageCar = 1; }} />
    </div>
  </div>

  <div class="tabs">
    <button class="tab" class:active={tab === 'facultades'} onclick={() => { tab='facultades'; q=''; pageFac = 1; }}>
      <i class="bi bi-bank"></i> Facultades ({facultades.length})
    </button>
    <button class="tab" class:active={tab === 'carreras'} onclick={() => { tab='carreras'; q=''; pageCar = 1; }}>
      <i class="bi bi-book"></i> Carreras ({carreras.length})
    </button>
  </div>

  {#if loading}
    <InstitutionalLoader fullscreen={true} texto="CARGANDO FACULTADES" subtexto="Consultando facultades y carreras UTEQ..." />
  {:else if tab === 'facultades'}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre de la Facultad</th>
            <th>Nombre corto</th>
            <th>Campus</th>
            <th>Estado</th>
            <th style="text-align: center;">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedFacs as f}
            <tr>
              <td><span class="code">{f.codigo}</span></td>
              <td class="nombre-p">{f.nombre}</td>
              <td class="txt-sm">{f.nombre_corto || '—'}</td>
              <td class="txt-sm">{f.campus || '—'}</td>
              <td>
                <span class="badge" class:activo={f.activo} class:inactivo={!f.activo}>
                  {f.activo ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td>
                <div class="acciones center">
                  <a href="/facultades/{f.id_facultad}" class="btn-accion editar" title="Editar facultad">
                    <i class="bi bi-pencil"></i>
                  </a>
                  <button class="btn-accion {f.activo ? 'danger':'success'}"
                    onclick={() => toggleFac(f.id_facultad, f.activo)}
                    title={f.activo ? 'Desactivar' : 'Activar'}>
                    <i class="bi bi-{f.activo ? 'toggle-on':'toggle-off'}"></i>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
          {#if filtFacs.length === 0}
            <tr><td colspan="6" class="empty">No se encontraron facultades</td></tr>
          {/if}
        </tbody>
      </table>

      {#if filtFacs.length > 0}
        <Pagination totalItems={filtFacs.length} bind:page={pageFac} bind:pageSize={pageSizeFac} itemLabel="facultades" />
      {/if}
    </div>

  {:else}
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre de la Carrera</th>
            <th>Facultad</th>
            <th style="text-align: center;">Horas Vinc.</th>
            <th>Estado</th>
            <th style="text-align: center;">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedCarr as c}
            <tr>
              <td><span class="code">{c.codigo || '—'}</span></td>
              <td class="nombre-p">{c.nombre}</td>
              <td><span class="fac-b">{c.facultad_nombre || '—'}</span></td>
              <td class="txt-sm center font-bold">{c.horas_vinculacion || '—'}h</td>
              <td>
                <span class="badge" class:activo={c.activo} class:inactivo={!c.activo}>
                  {c.activo ? 'Activa' : 'Inactiva'}
                </span>
              </td>
              <td>
                <div class="acciones center">
                  <a href="/carreras/{c.id_carrera}" class="btn-accion editar" title="Editar carrera">
                    <i class="bi bi-pencil"></i>
                  </a>
                  <button class="btn-accion {c.activo ? 'danger':'success'}"
                    onclick={() => toggleCarr(c.id_carrera, c.activo)}
                    title={c.activo ? 'Desactivar' : 'Activar'}>
                    <i class="bi bi-{c.activo ? 'toggle-on':'toggle-off'}"></i>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
          {#if filtCarr.length === 0}
            <tr><td colspan="6" class="empty">No se encontraron carreras</td></tr>
          {/if}
        </tbody>
      </table>

      {#if filtCarr.length > 0}
        <Pagination totalItems={filtCarr.length} bind:page={pageCar} bind:pageSize={pageSizeCar} itemLabel="carreras" />
      {/if}
    </div>
  {/if}
</div>

<style>
.subbar { display:flex;align-items:center;justify-content:space-between;padding:10px 24px;background:#fff;border-bottom:1px solid #e2e8f0; }
.btn-nuevo { display:inline-flex;align-items:center;gap:6px;background:#1b7505;color:#fff;padding:8px 16px;border-radius:9px;font-weight:700;font-size:.85rem;text-decoration:none;transition:background .15s ease; }
.btn-nuevo:hover { background:#145c04; }

.tabs { display:flex;gap:4px;margin-bottom:16px;border-bottom:2px solid #e2e8f0;padding-bottom:0; }
.tab { display:flex;align-items:center;gap:8px;padding:10px 18px;border:none;background:transparent;font-size:.88rem;font-weight:600;color:#64748b;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s; }
.tab:hover { color:#1e293b; }
.tab.active { color:#1b7505;border-bottom-color:#1b7505;font-weight:700; }

.nombre-p { font-weight:700; color:#1e293b; }
.fac-b { font-size:.72rem;font-weight:700;color:#15803d;background:#f0fdf4;border:1px solid #bbf7d0;padding:2px 8px;border-radius:6px; }
.txt-sm { font-size:.78rem; color:#475569; }
.font-bold { font-weight:700; }
.center { text-align:center; justify-content:center; }
.acciones { display:flex;gap:6px;align-items:center; }
</style>
