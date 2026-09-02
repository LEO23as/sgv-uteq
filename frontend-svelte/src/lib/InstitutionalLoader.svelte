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
    background: rgba(15, 23, 42, 0.48);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    animation: fadeIn .25s ease-out forwards;
  }

  .sgv-loader-backdrop:not(.fullscreen) {
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    border-radius: inherit;
  }

  .sgv-loader-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 18px;
    animation: floatCard 3s ease-in-out infinite alternate;
  }

  /* ── ÓRBITAS GIRATORIAS ── */
  .sgv-orbit-wrap {
    position: relative;
    width: 130px;
    height: 130px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .orbit-ring {
    position: absolute;
    border-radius: 50%;
    box-sizing: border-box;
  }

  /* Anillo exterior Dorado UTEQ */
  .ring-outer-gold {
    width: 124px;
    height: 124px;
    border: 3.5px solid transparent;
    border-top-color: #f59e0b;
    border-bottom-color: #eab308;
    filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.45));
    animation: spinClockwise 2.4s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite;
  }

  /* Anillo interior Verde UTEQ */
  .ring-inner-green {
    width: 96px;
    height: 96px;
    border: 3px solid transparent;
    border-left-color: #10b981;
    border-right-color: #059669;
    filter: drop-shadow(0 0 6px rgba(16, 185, 129, 0.45));
    animation: spinCounter 1.8s linear infinite;
  }

  /* ── SIGLAS CENTRALES FLOTANTES CON DEGRADADO METÁLICO ── */
  .sgv-siglas-box {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulseSiglas 2s ease-in-out infinite alternate;
  }

  .sgv-siglas {
    font-family: 'Montserrat', 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 2.25rem;
    font-weight: 900;
    letter-spacing: 0.12em;
    background: linear-gradient(135deg, #fffbeb 0%, #fef08a 25%, #f59e0b 60%, #b45309 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.35));
    padding-left: 0.12em; /* Compensa el letter-spacing */
  }

  /* ── CAPTION "CARGANDO" ── */
  .sgv-loader-caption {
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Montserrat', 'Inter', system-ui, sans-serif;
    font-size: 0.88rem;
    font-weight: 800;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #ffffff;
    text-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
  }

  .animated-dots {
    display: inline-flex;
    margin-left: 2px;
  }

  .dot {
    opacity: 0;
    animation: dotPulse 1.4s infinite;
  }
  .dot.d1 { animation-delay: 0.0s; }
  .dot.d2 { animation-delay: 0.2s; }
  .dot.d3 { animation-delay: 0.4s; }

  .sgv-loader-sub {
    font-size: 0.78rem;
    color: rgba(255, 255, 255, 0.85);
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    font-weight: 500;
    margin-top: -8px;
  }

  /* ── KEYFRAME ANIMATIONS ── */
  @keyframes spinClockwise {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes spinCounter {
    0%   { transform: rotate(360deg); }
    100% { transform: rotate(0deg); }
  }

  @keyframes floatCard {
    0%   { transform: translateY(-5px); }
    100% { transform: translateY(5px); }
  }

  @keyframes pulseSiglas {
    0%   { transform: scale(0.96); filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }
    100% { transform: scale(1.04); filter: drop-shadow(0 4px 10px rgba(245, 158, 11, 0.5)); }
  }

  @keyframes dotPulse {
    0%, 20% { opacity: 0; transform: translateY(0); }
    50%     { opacity: 1; transform: translateY(-2px); }
    80%, 100% { opacity: 0; transform: translateY(0); }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
</style>
