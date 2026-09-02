<script>
  /**
   * Componente Oficial de Carga Institucional SGV-UTEQ
   * Replica exacta del loader institucional del SGA-UTEQ adaptado a SGV
   */
  let { 
    fullscreen = true, 
    texto = 'CARGANDO', 
    subtexto = '',
    siglas = 'SGV' 
  } = $props();
</script>

<div class="sgv-loader-backdrop" class:fullscreen>
  <div class="sgv-loader-card">
    
    <!-- Anillos Orbitales Giratorios -->
    <div class="sgv-orbit-wrap">
      <div class="orbit-ring ring-outer-gold"></div>
      <div class="orbit-ring ring-inner-green"></div>
      
      <!-- Siglas Centrales Flotantes -->
      <div class="sgv-siglas-box">
        <span class="sgv-siglas">{siglas}</span>
      </div>
    </div>

    <!-- Texto Inferior con puntos animados -->
    <div class="sgv-loader-caption">
      <span class="caption-text">{texto}</span>
      <span class="animated-dots">
        <span class="dot d1">.</span><span class="dot d2">.</span><span class="dot d3">.</span>
      </span>
    </div>

    {#if subtexto}
      <div class="sgv-loader-sub">{subtexto}</div>
    {/if}

  </div>
</div>

<style>
  .sgv-loader-backdrop {
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 99999;
    pointer-events: all;
    user-select: none;
  }

  .sgv-loader-backdrop.fullscreen {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    animation: fadeIn .2s ease-out forwards;
  }

  .sgv-loader-backdrop:not(.fullscreen) {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-radius: 12px;
    min-height: 260px;
    animation: fadeIn .2s ease-out forwards;
  }

  /* ── MOVIMIENTO DE ARRIBA PARA ABAJO (BOBBING) ── */
  .sgv-loader-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    animation: floatUpDown 2.4s ease-in-out infinite alternate;
  }

  /* ── ÓRBITAS GIRATORIAS FINAS Y ELEGANTES ── */
  .sgv-orbit-wrap {
    position: relative;
    width: 120px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .orbit-ring {
    position: absolute;
    border-radius: 50%;
    box-sizing: border-box;
  }

  /* Pista circular sutil de fondo */
  .sgv-orbit-wrap::before {
    content: '';
    position: absolute;
    width: 114px;
    height: 114px;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.18);
  }

  /* Arco exterior Dorado UTEQ */
  .ring-outer-gold {
    width: 114px;
    height: 114px;
    border: 2.5px solid transparent;
    border-top-color: #f59e0b;
    border-left-color: #f59e0b;
    border-radius: 50%;
    filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.5));
    animation: spinClockwise 2.2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  }

  /* Arco interior Verde UTEQ */
  .ring-inner-green {
    width: 88px;
    height: 88px;
    border: 2.5px solid transparent;
    border-bottom-color: #22c55e;
    border-right-color: #16a34a;
    border-radius: 50%;
    filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.45));
    animation: spinCounter 1.7s linear infinite;
  }

  /* ── TIPOGRAFÍA EXACTA SGA/SGV UTEQ (DORADO SUAVE GEOMÉTRICO) ── */
  .sgv-siglas-box {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sgv-siglas {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    color: #f2c94c;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
    padding-left: 0.16em; /* Equilibrio visual del letter-spacing */
  }

  /* ── CAPTION "C A R G A N D O" ── */
  .sgv-loader-caption {
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: #e2e8f0;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.7);
    padding-left: 0.32em;
  }

  .animated-dots {
    display: inline-flex;
    margin-left: 2px;
  }

  .dot {
    opacity: 0;
    color: #f59e0b;
    animation: dotPulse 1.4s infinite;
  }
  .dot.d1 { animation-delay: 0.0s; }
  .dot.d2 { animation-delay: 0.25s; }
  .dot.d3 { animation-delay: 0.5s; }

  .sgv-loader-sub {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.82);
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
    font-weight: 500;
    margin-top: -6px;
    letter-spacing: 0.06em;
  }

  /* ── ANIMACIONES CSS PURAS A 60 FPS ── */
  @keyframes spinClockwise {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes spinCounter {
    0%   { transform: rotate(360deg); }
    100% { transform: rotate(0deg); }
  }

  @keyframes floatUpDown {
    0%   { transform: translateY(-7px); }
    100% { transform: translateY(7px); }
  }

  @keyframes dotPulse {
    0%, 20% { opacity: 0; transform: translateY(0); }
    50%     { opacity: 1; transform: translateY(-3px); }
    80%, 100% { opacity: 0; transform: translateY(0); }
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: scale(0.98); }
    to   { opacity: 1; transform: scale(1); }
  }
</style>
