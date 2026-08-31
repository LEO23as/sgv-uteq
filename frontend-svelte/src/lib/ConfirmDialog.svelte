<script>
  import { confirmState, closeConfirm } from '$lib/confirm';

  function onKeydown(e) {
    if (!$confirmState.isOpen) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      closeConfirm(false);
    }
  }

  const THEMES = {
    danger: {
      color: '#dc3545',
      bgLight: '#fee2e2',
      btnClass: 'btn-confirm-danger',
      defaultIcon: 'bi-exclamation-octagon-fill'
    },
    warning: {
      color: '#d97706',
      bgLight: '#fef3c7',
      btnClass: 'btn-confirm-warning',
      defaultIcon: 'bi-exclamation-triangle-fill'
    },
    info: {
      color: '#0284c7',
      bgLight: '#e0f2fe',
      btnClass: 'btn-confirm-info',
      defaultIcon: 'bi-info-circle-fill'
    },
    primary: {
      color: '#1b7505',
      bgLight: '#dcfce7',
      btnClass: 'btn-confirm-primary',
      defaultIcon: 'bi-check-circle-fill'
    }
  };
</script>

<svelte:window onkeydown={onKeydown} />

{#if $confirmState.isOpen}
  {@const theme = THEMES[$confirmState.type] || THEMES.danger}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="confirm-backdrop" onclick={() => closeConfirm(false)}>
    <div class="confirm-card" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <div class="confirm-header">
        <div class="confirm-icon-wrapper" style="--theme-c:{theme.color}; --theme-bg:{theme.bgLight}">
          <i class="bi {$confirmState.icon || theme.defaultIcon}"></i>
        </div>
        <div class="confirm-text">
          <h3 class="confirm-title">{$confirmState.title}</h3>
          <p class="confirm-msg">{$confirmState.message}</p>
        </div>
      </div>

      <div class="confirm-actions">
        <button
          type="button"
          class="btn-cancel"
          onclick={() => closeConfirm(false)}
        >
          {$confirmState.cancelText}
        </button>
        <button
          type="button"
          class="btn-confirm {theme.btnClass}"
          onclick={() => closeConfirm(true)}
        >
          {$confirmState.confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .confirm-backdrop {
    position: fixed;
    inset: 0;
    z-index: 10000;
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    animation: fadeIn 0.18s ease-out;
  }

  .confirm-card {
    background: #ffffff;
    border-radius: 16px;
    max-width: 440px;
    width: 100%;
    padding: 24px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.22), 0 4px 12px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0;
    animation: popIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .confirm-header {
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }

  .confirm-icon-wrapper {
    width: 46px;
    height: 46px;
    border-radius: 12px;
    background: var(--theme-bg);
    color: var(--theme-c);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.45rem;
    flex-shrink: 0;
  }

  .confirm-text {
    flex: 1;
    min-width: 0;
  }

  .confirm-title {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.35;
  }

  .confirm-msg {
    margin: 6px 0 0 0;
    font-size: 0.88rem;
    color: #64748b;
    line-height: 1.45;
    word-break: break-word;
  }

  .confirm-actions {
    margin-top: 22px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .btn-cancel,
  .btn-confirm {
    padding: 8px 18px;
    border-radius: 9px;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-cancel {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    color: #475569;
  }

  .btn-cancel:hover {
    background: #e2e8f0;
    color: #1e293b;
  }

  .btn-confirm {
    border: none;
    color: #ffffff;
  }

  .btn-confirm-danger {
    background: #dc3545;
  }
  .btn-confirm-danger:hover {
    background: #b02a37;
  }

  .btn-confirm-warning {
    background: #d97706;
  }
  .btn-confirm-warning:hover {
    background: #b45309;
  }

  .btn-confirm-info {
    background: #0284c7;
  }
  .btn-confirm-info:hover {
    background: #0369a1;
  }

  .btn-confirm-primary {
    background: #1b7505;
  }
  .btn-confirm-primary:hover {
    background: #155d04;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes popIn {
    from {
      opacity: 0;
      transform: scale(0.94) translateY(8px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }
</style>
