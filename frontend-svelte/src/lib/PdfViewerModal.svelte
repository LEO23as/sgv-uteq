<script lang="ts">
  interface Props {
    show: boolean;
    docUrl: string;
    docTitle?: string;
    docCategory?: string;
    onClose: () => void;
  }

  let {
    show = $bindable(false),
    docUrl = '',
    docTitle = 'Documento Oficial',
    docCategory = 'CACES - Vinculación',
    onClose
  }: Props = $props();

  let loading = $state(true);
  let isFullscreen = $state(false);
  let loadError = $state(false);

  $effect(() => {
    if (show && docUrl) {
      loading = true;
      loadError = false;
    }
  });

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && show) {
      cerrar();
    }
  }

  function cerrar() {
    show = false;
    isFullscreen = false;
    loading = false;
    if (onClose) onClose();
  }

  function toggleFullscreen() {
    isFullscreen = !isFullscreen;
  }

  function handleIframeLoad() {
    loading = false;
  }

  function handleIframeError() {
    loading = false;
    loadError = true;
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if show}
  <div class="pdf-backdrop" role="dialog" aria-modal="true" onclick={cerrar}>
    <div
      class="pdf-modal-container"
      class:fullscreen={isFullscreen}
      onclick={(e) => e.stopPropagation()}
      role="document"
    >
      <!-- HEADER -->
      <div class="pdf-header">
        <div class="pdf-meta">
          <div class="pdf-badges">
            <span class="badge-inst"><i class="bi bi-shield-check"></i> UTEQ CACES</span>
            {#if docCategory}
              <span class="badge-cat">{docCategory}</span>
            {/if}
          </div>
          <h3 class="pdf-title" title={docTitle}>
            <i class="bi bi-file-earmark-pdf-fill text-danger"></i>
            {docTitle}
          </h3>
        </div>

        <div class="pdf-actions">
          <button
            type="button"
            class="btn-action"
            title="Pantalla completa"
            onclick={toggleFullscreen}
          >
            <i class="bi {isFullscreen ? 'bi-fullscreen-exit' : 'bi-arrows-fullscreen'}"></i>
            <span class="btn-txt">{isFullscreen ? 'Normal' : 'Expandir'}</span>
          </button>

          <a
            href={docUrl}
            target="_blank"
            rel="noopener noreferrer"
            class="btn-action"
            title="Abrir en pestaña nueva"
          >
            <i class="bi bi-box-arrow-up-right"></i>
            <span class="btn-txt">Pestaña</span>
          </a>

          <a
            href={docUrl}
            download
            class="btn-action btn-primary-uteq"
            title="Descargar PDF oficial"
          >
            <i class="bi bi-download"></i>
            <span class="btn-txt">Descargar</span>
          </a>

          <button
            type="button"
            class="btn-close-modal"
            title="Cerrar visor (ESC)"
            onclick={cerrar}
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>

      <!-- BODY DEL VISOR -->
      <div class="pdf-body">
        {#if loading}
          <div class="pdf-loader">
            <div class="spinner-uteq"></div>
            <p>Cargando documento oficial de vinculación...</p>
          </div>
        {/if}

        {#if loadError}
          <div class="pdf-error">
            <i class="bi bi-exclamation-triangle-fill text-warning"></i>
            <h4>No se pudo cargar la vista previa directa</h4>
            <p>El documento está disponible para descarga segura o apertura externa.</p>
            <div class="error-actions">
              <a href={docUrl} target="_blank" class="btn-action"><i class="bi bi-box-arrow-up-right"></i> Abrir en pestaña</a>
              <a href={docUrl} download class="btn-action btn-primary-uteq"><i class="bi bi-download"></i> Descargar archivo</a>
            </div>
          </div>
        {:else if docUrl}
          <iframe
            src="{docUrl}#toolbar=1&navpanes=0&view=FitH"
            title={docTitle}
            class="pdf-iframe"
            onload={handleIframeLoad}
            onerror={handleIframeError}
          ></iframe>
        {/if}
      </div>

      <!-- FOOTER / STATUS BAR -->
      <div class="pdf-footer">
        <span class="pdf-footer-note"><i class="bi bi-lock-fill"></i> Documento normativo digitalizado - Sistema de Gestión de Vinculación UTEQ</span>
        <span class="pdf-esc-hint">Presiona <strong>ESC</strong> para cerrar</span>
      </div>
    </div>
  </div>
{/if}

<style>
  .pdf-backdrop {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    animation: fadeIn 0.18s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .pdf-modal-container {
    width: 92vw;
    max-width: 1200px;
    height: 90vh;
    background: #ffffff;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
    transition: all 0.25s ease-in-out;
  }

  .pdf-modal-container.fullscreen {
    width: 100vw;
    max-width: 100vw;
    height: 100vh;
    border-radius: 0;
    padding: 0;
  }

  /* HEADER */
  .pdf-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    gap: 16px;
    flex-shrink: 0;
  }

  .pdf-meta {
    min-width: 0;
    flex: 1;
  }

  .pdf-badges {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .badge-inst {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    background: #e8f5e0;
    color: #1b7505;
    padding: 2px 8px;
    border-radius: 6px;
    letter-spacing: 0.03em;
  }

  .badge-cat {
    font-size: 0.72rem;
    font-weight: 600;
    background: #e2e8f0;
    color: #334155;
    padding: 2px 8px;
    border-radius: 6px;
  }

  .pdf-title {
    margin: 0;
    font-size: 0.98rem;
    font-weight: 600;
    color: #0f172a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .text-danger { color: #dc2626; }
  .text-warning { color: #d97706; }

  /* ACTIONS */
  .pdf-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .btn-action {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    background: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s;
  }

  .btn-action:hover {
    background: #f1f5f9;
    color: #0f172a;
    border-color: #94a3b8;
  }

  .btn-primary-uteq {
    background: #1b7505;
    color: #ffffff !important;
    border-color: #1b7505;
  }

  .btn-primary-uteq:hover {
    background: #155d04;
    border-color: #155d04;
  }

  .btn-close-modal {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-close-modal:hover {
    background: #fee2e2;
    color: #ef4444;
  }

  /* BODY */
  .pdf-body {
    flex: 1;
    position: relative;
    background: #334155;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pdf-iframe {
    width: 100%;
    height: 100%;
    border: none;
    display: block;
    background: #ffffff;
  }

  .pdf-loader {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    color: #f8fafc;
    font-size: 0.9rem;
  }

  .spinner-uteq {
    width: 42px;
    height: 42px;
    border: 4px solid rgba(255, 255, 255, 0.2);
    border-top-color: #22c55e;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .pdf-error {
    text-align: center;
    color: #f8fafc;
    padding: 30px;
  }

  .pdf-error i {
    font-size: 2.5rem;
  }

  .pdf-error h4 {
    margin: 12px 0 6px 0;
    font-size: 1.1rem;
  }

  .pdf-error p {
    color: #94a3b8;
    font-size: 0.88rem;
    margin-bottom: 20px;
  }

  .error-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
  }

  /* FOOTER */
  .pdf-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 20px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 0.76rem;
    color: #64748b;
  }

  .pdf-footer-note i {
    color: #1b7505;
  }

  .pdf-esc-hint strong {
    background: #e2e8f0;
    padding: 2px 6px;
    border-radius: 4px;
    color: #1e293b;
  }

  @media (max-width: 640px) {
    .btn-txt { display: none; }
    .pdf-header { padding: 10px 14px; }
    .pdf-modal-container { width: 98vw; height: 95vh; }
    .pdf-esc-hint { display: none; }
  }
</style>
