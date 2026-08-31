<script>
  /**
   * Componente institucional de Paginación para tablas.
   */
  let {
    totalItems = 0,
    page = $bindable(1),
    pageSize = $bindable(10),
    pageSizeOptions = [5, 10, 20, 50],
    itemLabel = 'registros'
  } = $props();

  const totalPages = $derived(Math.max(1, Math.ceil(totalItems / pageSize)));
  
  // Rango actual mostrado
  const startItem = $derived(totalItems === 0 ? 0 : (page - 1) * pageSize + 1);
  const endItem = $derived(Math.min(page * pageSize, totalItems));

  // Generación de botones de páginas visibles
  const visiblePages = $derived.by(() => {
    const pages = [];
    const maxButtons = 5;
    
    if (totalPages <= maxButtons) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      let start = Math.max(1, page - 2);
      let end = Math.min(totalPages, page + 2);

      if (page <= 3) {
        start = 1;
        end = maxButtons;
      } else if (page >= totalPages - 2) {
        start = totalPages - maxButtons + 1;
        end = totalPages;
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
    }
    return pages;
  });

  function goToPage(p) {
    if (p >= 1 && p <= totalPages) {
      page = p;
    }
  }
</script>

<div class="pagination-bar">
  <div class="pag-info">
    {#if totalItems > 0}
      Mostrando <span class="pag-bold">{startItem} - {endItem}</span> de <span class="pag-bold">{totalItems}</span> {itemLabel}
    {:else}
      No hay {itemLabel} para mostrar
    {/if}
  </div>

  {#if totalPages > 1 || totalItems > pageSizeOptions[0]}
    <div class="pag-controls">
      <!-- Selector de cantidad por página -->
      <div class="pag-size-wrap">
        <label for="pag-size" class="pag-size-label">Mostrar:</label>
        <select
          id="pag-size"
          class="pag-select"
          bind:value={pageSize}
          onchange={() => { page = 1; }}
        >
          {#each pageSizeOptions as opt}
            <option value={opt}>{opt} / pág</option>
          {/each}
        </select>
      </div>

      <!-- Botones de navegación -->
      {#if totalPages > 1}
        <div class="pag-nav">
          <button
            type="button"
            class="pag-btn"
            disabled={page === 1}
            onclick={() => goToPage(page - 1)}
            title="Página anterior"
          >
            <i class="bi bi-chevron-left"></i>
          </button>

          {#each visiblePages as p}
            <button
              type="button"
              class="pag-btn num-btn"
              class:active={p === page}
              onclick={() => goToPage(p)}
            >
              {p}
            </button>
          {/each}

          <button
            type="button"
            class="pag-btn"
            disabled={page === totalPages}
            onclick={() => goToPage(page + 1)}
            title="Página siguiente"
          >
            <i class="bi bi-chevron-right"></i>
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .pagination-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px 16px;
    background: #ffffff;
    border-top: 1px solid #e2e8f0;
    border-bottom-left-radius: 14px;
    border-bottom-right-radius: 14px;
    font-size: 0.82rem;
    color: #64748b;
  }

  .pag-info {
    font-weight: 500;
  }

  .pag-bold {
    font-weight: 700;
    color: #1e293b;
  }

  .pag-controls {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .pag-size-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .pag-size-label {
    font-size: 0.78rem;
    color: #64748b;
  }

  .pag-select {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #334155;
    background: #f8fafc;
    cursor: pointer;
    outline: none;
  }

  .pag-select:focus {
    border-color: #1b7505;
  }

  .pag-nav {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .pag-btn {
    width: 30px;
    height: 30px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
    background: #ffffff;
    color: #475569;
    font-size: 0.82rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .pag-btn:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #cbd5e1;
    color: #1e293b;
  }

  .pag-btn.active {
    background: #1b7505;
    border-color: #1b7505;
    color: #ffffff;
    font-weight: 700;
  }

  .pag-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  @media (max-width: 640px) {
    .pagination-bar {
      flex-direction: column;
      align-items: flex-start;
    }
    .pag-controls {
      width: 100%;
      justify-content: space-between;
    }
  }
</style>
