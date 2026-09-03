<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { goto } from '$app/navigation';

  interface Props {
    isOpen?: boolean;
    onSelectProject?: (id: number) => void;
  }

  let { isOpen = $bindable(false), onSelectProject }: Props = $props();

  let query = $state('');
  let loading = $state(false);
  let resultados = $state<{
    proyectos: any[];
    docentes: any[];
    convenios: any[];
    territorios: any[];
  }>({
    proyectos: [],
    docentes: [],
    convenios: [],
    territorios: []
  });
  let totalResultados = $state(0);
  let esSugerencia = $state(true);
  let selectedIndex = $state(0);
  let inputEl: HTMLInputElement | null = $state(null);
  let debounceTimer: any = null;
  let recentSearches = $state<string[]>([]);

  // Lista plana de todos los elementos para navegación por teclado
  let flatItems = $derived([
    ...resultados.proyectos.map((p) => ({ ...p, _kind: 'proyecto' })),
    ...resultados.docentes.map((d) => ({ ...d, _kind: 'docente' })),
    ...resultados.convenios.map((c) => ({ ...c, _kind: 'convenio' })),
    ...resultados.territorios.map((t) => ({ ...t, _kind: 'territorio' }))
  ]);

  onMount(() => {
    try {
      const saved = localStorage.getItem('sgv_recent_searches');
      if (saved) recentSearches = JSON.parse(saved);
    } catch {}
  });

  $effect(() => {
    if (isOpen) {
      tick().then(() => {
        if (inputEl) inputEl.focus();
      });
      cargarSugerencias();
    } else {
      query = '';
      selectedIndex = 0;
    }
  });

  $effect(() => {
    if (isOpen && selectedIndex >= 0) {
      tick().then(() => {
        const el = document.querySelector('.result-row.active');
        if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      });
    }
  });

  function guardarBusquedaReciente(texto: string) {
    if (!texto || texto.trim().length < 2) return;
    const t = texto.trim();
    const nueva = [t, ...recentSearches.filter((x) => x.toLowerCase() !== t.toLowerCase())].slice(0, 5);
    recentSearches = nueva;
    try {
      localStorage.setItem('sgv_recent_searches', JSON.stringify(nueva));
    } catch {}
  }

  function limpiarHistorial() {
    recentSearches = [];
    try {
      localStorage.removeItem('sgv_recent_searches');
    } catch {}
  }

  function usarBusquedaReciente(texto: string) {
    query = texto;
    buscar(texto);
  }

  function handleGlobalKeydown(e: KeyboardEvent) {
    // Atajo Ctrl+K o Cmd+K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      isOpen = !isOpen;
      return;
    }

    if (!isOpen) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      isOpen = false;
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (flatItems.length > 0) {
        selectedIndex = (selectedIndex + 1) % flatItems.length;
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (flatItems.length > 0) {
        selectedIndex = (selectedIndex - 1 + flatItems.length) % flatItems.length;
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (flatItems[selectedIndex]) {
        ejecutarAccion(flatItems[selectedIndex]);
      }
    }
  }

  function onInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    query = val;
    selectedIndex = 0;

    clearTimeout(debounceTimer);
    if (!val || val.trim().length < 2) {
      cargarSugerencias();
      return;
    }

    loading = true;
    debounceTimer = setTimeout(() => {
      buscar(val.trim());
    }, 220);
  }

  async function buscar(q: string) {
    try {
      const res = await fetch(`/api/busqueda-global/?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        resultados = data.categorias || { proyectos: [], docentes: [], convenios: [], territorios: [] };
        totalResultados = data.total_resultados || 0;
        esSugerencia = !!data.es_sugerencia;
      }
    } catch (err) {
      console.error('Error en búsqueda global:', err);
    } finally {
      loading = false;
    }
  }

  async function cargarSugerencias() {
    try {
      loading = true;
      const res = await fetch('/api/busqueda-global/');
      if (res.ok) {
        const data = await res.json();
        resultados = data.categorias || { proyectos: [], docentes: [], convenios: [], territorios: [] };
        totalResultados = data.total_resultados || 0;
        esSugerencia = true;
      }
    } catch (err) {
      console.error('Error cargando sugerencias:', err);
    } finally {
      loading = false;
    }
  }

  function ejecutarAccion(item: any) {
    isOpen = false;
    if (!item) return;

    guardarBusquedaReciente(query || item.codigo || item.nombre || item.canton || item.entidad);

    if (item._kind === 'proyecto') {
      if (onSelectProject) {
        onSelectProject(item.id || item.id_proyecto);
      } else {
        goto(`/proyectos?id=${item.id || item.id_proyecto}`);
      }
    } else if (item._kind === 'docente') {
      if (onSelectProject && item.proyecto_id) {
        onSelectProject(item.proyecto_id);
      } else if (item.proyecto_id) {
        goto(`/proyectos?id=${item.proyecto_id}`);
      }
    } else if (item._kind === 'convenio') {
      goto(`/convenios/${item.id}`);
    } else if (item._kind === 'territorio') {
      goto(`/mapa?buscar=${encodeURIComponent(item.canton)}`);
    }
  }
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

{#if isOpen}
  <div class="search-backdrop" role="dialog" aria-modal="true" onclick={() => isOpen = false}>
    <div
      class="search-modal"
      onclick={(e) => e.stopPropagation()}
      role="document"
    >
      <!-- BARRA DE ENTRADA -->
      <div class="search-input-header">
        <i class="bi bi-search search-main-icon"></i>
        <input
          bind:this={inputEl}
          type="text"
          class="search-main-input"
          placeholder="Buscar proyectos, docentes, cantones, convenios... (ej: 'Quevedo', 'cacao', 'FCI')"
          value={query}
          oninput={onInput}
        />
        {#if loading}
          <div class="search-spinner"></div>
        {:else if query}
          <button type="button" class="btn-clear-search" onclick={() => { query = ''; cargarSugerencias(); }}>
            <i class="bi bi-x-circle-fill"></i>
          </button>
        {/if}
        <span class="kbd-badge">ESC</span>
      </div>

      <!-- HISTORIAL DE BÚSQUEDAS RECIENTES -->
      {#if !query && recentSearches.length > 0}
        <div class="recent-searches-bar">
          <span class="rs-label"><i class="bi bi-clock-history"></i> Recientes:</span>
          <div class="rs-chips">
            {#each recentSearches as rs}
              <button type="button" class="rs-chip" onclick={() => usarBusquedaReciente(rs)}>
                {rs}
              </button>
            {/each}
            <button type="button" class="btn-clear-history" onclick={limpiarHistorial} title="Limpiar historial">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      {/if}

      <!-- LISTA DE RESULTADOS -->
      <div class="search-results-box">
        {#if esSugerencia && !query}
          <div class="results-header-note">
            <i class="bi bi-lightning-charge-fill text-warning"></i> Proyectos destacados recientes
          </div>
        {/if}

        {#if !loading && totalResultados === 0 && query}
          <div class="no-results-state">
            <i class="bi bi-search-heart"></i>
            <h4>Sin coincidencias para "{query}"</h4>
            <p>Intenta con el código de proyecto (ej: PVSUTEQ), nombre de un cantón o apellido de docente.</p>
          </div>
        {/if}

        <!-- 1. PROYECTOS -->
        {#if resultados.proyectos?.length}
          <div class="search-group">
            <div class="group-title">
              <i class="bi bi-folder2-open text-verde"></i> Proyectos de Vinculación ({resultados.proyectos.length})
            </div>
            {#each resultados.proyectos as p}
              {@const isSel = flatItems[selectedIndex] === p}
              <div
                class="result-row"
                class:active={isSel}
                onclick={() => ejecutarAccion({ ...p, _kind: 'proyecto' })}
                role="button"
                tabindex="0"
                onmouseenter={() => selectedIndex = flatItems.indexOf(p)}
              >
                <div class="rr-icon verde"><i class="bi bi-folder-fill"></i></div>
                <div class="rr-body">
                  <div class="rr-line1">
                    <span class="rr-code">{p.codigo}</span>
                    <span class="rr-title">{p.nombre_corto || p.nombre}</span>
                  </div>
                  <div class="rr-line2">
                    <span class="rr-fac">{p.facultad || p.id_facultad__nombre_corto || 'UTEQ'}</span>
                    {#if p.carrera}<span class="rr-car">· {p.carrera}</span>{/if}
                    {#if p.canton}<span class="rr-geo">· <i class="bi bi-geo-alt"></i> {p.canton}</span>{/if}
                  </div>
                </div>
                <div class="rr-badge-estado {p.estado?.toLowerCase()}">
                  {p.estado || 'ACTIVO'}
                </div>
                {#if isSel}
                  <span class="rr-enter-hint"><kbd>↵</kbd></span>
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        <!-- 2. DOCENTES DIRECTORES -->
        {#if resultados.docentes?.length}
          <div class="search-group">
            <div class="group-title">
              <i class="bi bi-person-badge-fill text-blue"></i> Docentes y Directores ({resultados.docentes.length})
            </div>
            {#each resultados.docentes as d}
              {@const isSel = flatItems[selectedIndex] === d}
              <div
                class="result-row"
                class:active={isSel}
                onclick={() => ejecutarAccion({ ...d, _kind: 'docente' })}
                role="button"
                tabindex="0"
                onmouseenter={() => selectedIndex = flatItems.indexOf(d)}
              >
                <div class="rr-icon blue"><i class="bi bi-person-fill"></i></div>
                <div class="rr-body">
                  <div class="rr-line1">
                    <span class="rr-title bold">{d.nombre}</span>
                    {#if d.correo}<span class="rr-email">&lt;{d.correo}&gt;</span>{/if}
                  </div>
                  <div class="rr-line2">
                    <span class="rr-sub">Director de: <strong>{d.proyecto_codigo}</strong> - {d.proyecto_nombre}</span>
                  </div>
                </div>
                <span class="rr-tag">Docente UTEQ</span>
                {#if isSel}
                  <span class="rr-enter-hint"><kbd>↵</kbd></span>
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        <!-- 3. CONVENIOS -->
        {#if resultados.convenios?.length}
          <div class="search-group">
            <div class="group-title">
              <i class="bi bi-file-earmark-check-fill text-dorado"></i> Convenios y Cooperantes ({resultados.convenios.length})
            </div>
            {#each resultados.convenios as c}
              {@const isSel = flatItems[selectedIndex] === c}
              <div
                class="result-row"
                class:active={isSel}
                onclick={() => ejecutarAccion({ ...c, _kind: 'convenio' })}
                role="button"
                tabindex="0"
                onmouseenter={() => selectedIndex = flatItems.indexOf(c)}
              >
                <div class="rr-icon dorado"><i class="bi bi-building"></i></div>
                <div class="rr-body">
                  <div class="rr-line1">
                    <span class="rr-title bold">{c.entidad}</span>
                    <span class="rr-code">{c.memorando}</span>
                  </div>
                  <div class="rr-line2">
                    <span class="rr-sub">Convenio interinstitucional vigente</span>
                  </div>
                </div>
                <span class="rr-badge-estado vigente">{c.estado || 'VIGENTE'}</span>
                {#if isSel}
                  <span class="rr-enter-hint"><kbd>↵</kbd></span>
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        <!-- 4. TERRITORIOS / CANTONES -->
        {#if resultados.territorios?.length}
          <div class="search-group">
            <div class="group-title">
              <i class="bi bi-geo-alt-fill text-verde"></i> Cobertura Territorial ({resultados.territorios.length})
            </div>
            {#each resultados.territorios as t}
              {@const isSel = flatItems[selectedIndex] === t}
              <div
                class="result-row"
                class:active={isSel}
                onclick={() => ejecutarAccion({ ...t, _kind: 'territorio' })}
                role="button"
                tabindex="0"
                onmouseenter={() => selectedIndex = flatItems.indexOf(t)}
              >
                <div class="rr-icon verde"><i class="bi bi-pin-map-fill"></i></div>
                <div class="rr-body">
                  <div class="rr-line1">
                    <span class="rr-title bold">Cantón {t.canton}</span>
                    <span class="rr-sub">Provincia de {t.provincia}</span>
                  </div>
                  <div class="rr-line2">
                    <span class="rr-sub">Explorar cobertura de impacto territorial en mapa</span>
                  </div>
                </div>
                <span class="rr-tag">{t.total_proyectos} {t.total_proyectos === 1 ? 'proyecto' : 'proyectos'}</span>
                {#if isSel}
                  <span class="rr-enter-hint"><kbd>↵</kbd></span>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- FOOTER DE NAVEGACIÓN -->
      <div class="search-footer">
        <div class="footer-hints">
          <span class="hint-item"><kbd>↑</kbd><kbd>↓</kbd> Navegar</span>
          <span class="hint-item"><kbd>ENTER</kbd> Abrir</span>
          <span class="hint-item"><kbd>ESC</kbd> Cerrar</span>
        </div>
        <span class="footer-brand"><i class="bi bi-shield-check text-verde"></i> UTEQ Vinculación Global</span>
      </div>
    </div>
  </div>
{/if}

<style>
  .search-backdrop {
    position: fixed;
    inset: 0;
    z-index: 999999;
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(5px);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 60px 16px 20px;
    animation: fadeIn 0.16s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .search-modal {
    width: 100%;
    max-width: 760px;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(226, 232, 240, 0.9);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    max-height: 82vh;
    animation: slideDown 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes slideDown {
    from { transform: scale(0.97) translateY(-10px); opacity: 0; }
    to { transform: scale(1) translateY(0); opacity: 1; }
  }

  /* INPUT HEADER */
  .search-input-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    border-bottom: 1px solid #e2e8f0;
    background: #ffffff;
  }

  .search-main-icon {
    font-size: 1.3rem;
    color: #1b7505;
    flex-shrink: 0;
  }

  .search-main-input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 1.05rem;
    font-weight: 500;
    color: #0f172a;
    background: transparent;
  }

  .search-main-input::placeholder {
    color: #94a3b8;
    font-size: 0.95rem;
  }

  .search-spinner {
    width: 20px;
    height: 20px;
    border: 2.5px solid #e2e8f0;
    border-top-color: #1b7505;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .btn-clear-search {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1rem;
    padding: 2px;
    display: flex;
  }

  .btn-clear-search:hover {
    color: #64748b;
  }

  .kbd-badge {
    font-size: 0.7rem;
    font-weight: 700;
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 2px 6px;
    letter-spacing: 0.04em;
  }

  /* RECENT SEARCHES BAR */
  .recent-searches-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    background: #f8fafc;
    border-bottom: 1px solid #f1f5f9;
    overflow-x: auto;
  }

  .rs-label {
    font-size: 0.74rem;
    font-weight: 700;
    color: #64748b;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .rs-chips {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .rs-chip {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #334155;
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 0.74rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.14s;
  }

  .rs-chip:hover {
    background: #e8f5e0;
    color: #1b7505;
    border-color: #a7f3d0;
  }

  .btn-clear-history {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.75rem;
    padding: 2px;
  }

  .btn-clear-history:hover {
    color: #ef4444;
  }

  /* RESULTS BOX */
  .search-results-box {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .results-header-note {
    font-size: 0.76rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    padding: 4px 10px;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .search-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .group-title {
    font-size: 0.74rem;
    font-weight: 800;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 6px 10px 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .result-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.12s, transform 0.12s;
    user-select: none;
    position: relative;
  }

  .result-row:hover, .result-row.active {
    background: #f1f5f9;
  }

  .result-row.active {
    border-left: 3px solid #1b7505;
    background: #f0fdf4;
  }

  .rr-enter-hint {
    margin-left: 6px;
  }

  .rr-enter-hint kbd {
    background: #ffffff;
    border: 1px solid #a7f3d0;
    color: #1b7505;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    box-shadow: 0 1px 2px rgba(27, 117, 5, 0.15);
  }

  .rr-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
  }

  .rr-icon.verde { background: #e8f5e0; color: #1b7505; }
  .rr-icon.blue { background: #e0f2fe; color: #0284c7; }
  .rr-icon.dorado { background: #fef3c7; color: #d97706; }

  .rr-body {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .rr-line1 {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .rr-code {
    font-size: 0.72rem;
    font-weight: 800;
    background: #e2e8f0;
    color: #334155;
    padding: 1px 6px;
    border-radius: 4px;
    white-space: nowrap;
  }

  .rr-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: #0f172a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .rr-title.bold {
    font-weight: 700;
  }

  .rr-email {
    font-size: 0.74rem;
    color: #64748b;
    font-family: monospace;
  }

  .rr-line2 {
    font-size: 0.76rem;
    color: #64748b;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .rr-fac { font-weight: 700; color: #1b7505; }

  .rr-badge-estado {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 6px;
    letter-spacing: 0.04em;
    flex-shrink: 0;
  }

  .rr-badge-estado.en_ejecucion, .rr-badge-estado.vigente {
    background: #e8f5e0; color: #1b7505;
  }

  .rr-badge-estado.finalizado {
    background: #f1f5f9; color: #475569;
  }

  .rr-tag {
    font-size: 0.72rem;
    font-weight: 700;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    color: #475569;
    padding: 2px 8px;
    border-radius: 12px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .no-results-state {
    text-align: center;
    padding: 40px 20px;
    color: #64748b;
  }

  .no-results-state i {
    font-size: 2.4rem;
    color: #cbd5e1;
    margin-bottom: 8px;
    display: block;
  }

  .no-results-state h4 {
    margin: 0 0 6px 0;
    font-size: 1rem;
    color: #1e293b;
  }

  .no-results-state p {
    margin: 0;
    font-size: 0.82rem;
    color: #94a3b8;
  }

  /* FOOTER */
  .search-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 18px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 0.74rem;
    color: #64748b;
  }

  .footer-hints {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .hint-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .hint-item kbd {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.08);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 0.68rem;
    font-weight: 700;
    color: #334155;
  }

  .text-verde { color: #1b7505; }
  .text-blue { color: #0284c7; }
  .text-dorado { color: #d97706; }
  .text-warning { color: #eab308; }

  @media (max-width: 640px) {
    .search-backdrop { padding-top: 20px; }
    .footer-hints { display: none; }
    .recent-searches-bar { display: none; }
  }
</style>
