<script>
  /**
   * Componente de Barra de Progreso institucional.
   * Soporta variantes de color, cálculo de porcentaje, etiquetas y animaciones.
   */
  let {
    value = 0,
    max = 100,
    label = '',
    sublabel = '',
    variant = 'uteq', // 'uteq' | 'auto' | 'auto-reverse' | 'success' | 'warning' | 'danger' | 'info'
    size = 'md', // 'sm' | 'md' | 'lg'
    showPercentage = false,
    animated = false,
    striped = false,
    height = null,
  } = $props();

  // Calcular porcentaje normalizado (0 a 100)
  const pct = $derived(
    max > 0 ? Math.min(100, Math.max(0, Math.round((value / max) * 100))) : 0
  );

  // Determinar color de barra
  const color = $derived.by(() => {
    if (variant === 'auto') {
      // Directo: alto es bueno (verde), medio (amarillo), bajo (rojo)
      if (pct >= 70) return '#1b7505'; // Verde SGA
      if (pct >= 35) return '#d97706'; // Ámbar
      return '#dc3545'; // Rojo
    }
    if (variant === 'auto-reverse') {
      // Inverso: bajo es bueno (verde), alto es crítico (rojo)
      if (pct <= 35) return '#1b7505';
      if (pct <= 70) return '#d97706';
      return '#dc3545';
    }
    if (variant === 'success') return '#1b7505';
    if (variant === 'warning') return '#d97706';
    if (variant === 'danger') return '#dc3545';
    if (variant === 'info') return '#0284c7';
    return '#1b7505'; // Default UTEQ green
  });

  const barHeight = $derived(
    height || (size === 'sm' ? '6px' : size === 'lg' ? '14px' : '9px')
  );
</script>

<div class="progress-container">
  {#if label || sublabel || showPercentage}
    <div class="progress-labels">
      {#if label}
        <span class="p-label">{label}</span>
      {/if}
      <div class="p-meta">
        {#if sublabel}
          <span class="p-sublabel">{sublabel}</span>
        {/if}
        {#if showPercentage}
          <span class="p-pct" style="color: {color};">{pct}%</span>
        {/if}
      </div>
    </div>
  {/if}

  <div class="progress-track" style="height: {barHeight};">
    <div
      class="progress-fill {animated ? 'animated' : ''} {striped ? 'striped' : ''}"
      style="width: {pct}%; background-color: {color};"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin="0"
      aria-valuemax={max}
    ></div>
  </div>
</div>

<style>
  .progress-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .progress-labels {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78rem;
    line-height: 1.2;
  }

  .p-label {
    font-weight: 600;
    color: #475569;
  }

  .p-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: auto;
  }

  .p-sublabel {
    color: #64748b;
    font-size: 0.75rem;
  }

  .p-pct {
    font-weight: 700;
    font-size: 0.78rem;
  }

  .progress-track {
    width: 100%;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
    position: relative;
  }

  .progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.3s ease;
  }

  .striped {
    background-image: linear-gradient(
      45deg,
      rgba(255, 255, 255, 0.18) 25%,
      transparent 25%,
      transparent 50%,
      rgba(255, 255, 255, 0.18) 50%,
      rgba(255, 255, 255, 0.18) 75%,
      transparent 75%,
      transparent
    );
    background-size: 1rem 1rem;
  }

  .animated {
    animation: progress-stripes 1s linear infinite;
  }

  @keyframes progress-stripes {
    0% { background-position: 1rem 0; }
    100% { background-position: 0 0; }
  }
</style>
