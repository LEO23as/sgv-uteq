<script>
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>Error {$page.status} — SGV UTEQ</title>
</svelte:head>

<div class="sgv-error-container">
  <div class="sgv-error-card">
    
    <!-- Insignia Institucional -->
    <div class="error-badge">
      <div class="badge-ring"></div>
      <i class="bi {$page.status === 404 ? 'bi-geo-alt-fill' : 'bi-exclamation-octagon-fill'}"></i>
    </div>

    <div class="error-code">{$page.status}</div>
    
    <h1 class="error-title">
      {$page.status === 404 ? 'Ruta o Recurso No Encontrado' : 'Incidencia en el Servidor'}
    </h1>

    <p class="error-desc">
      {#if $page.status === 404}
        La página o el punto georreferenciado que intentas consultar no existe, fue archivado o se encuentra temporalmente fuera de servicio.
      {:else}
        {$page.error?.message || 'Ocurrió una incidencia inesperada al procesar la solicitud. Nuestro equipo de soporte ha registrado el evento en la bitácora de auditoría.'}
      {/if}
    </p>

    <!-- Botones de Acción Directa -->
    <div class="error-actions">
      <a href="/dashboard" class="btn-primary">
        <i class="bi bi-speedometer2"></i> Panel Principal
      </a>
      <a href="/mapa" class="btn-secondary">
        <i class="bi bi-map-fill"></i> Ver Mapa de Vinculación
      </a>
    </div>

    <!-- Pie Institucional -->
    <div class="error-footer">
      <span>Universidad Técnica Estatal de Quevedo</span>
      <span class="dot">•</span>
      <span>Dirección de Vinculación con la Sociedad</span>
    </div>

  </div>
</div>

<style>
  .sgv-error-container {
    min-height: 85vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 30px 20px;
    background: radial-gradient(circle at 50% 30%, rgba(34, 197, 94, 0.05) 0%, transparent 70%);
  }

  .sgv-error-card {
    background: #ffffff;
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 20px;
    box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.08);
    max-width: 520px;
    width: 100%;
    padding: 42px 36px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    animation: fadeIn .3s ease-out;
  }

  .error-badge {
    position: relative;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(22, 163, 74, 0.12), rgba(245, 158, 11, 0.12));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    color: #16a34a;
    margin-bottom: 16px;
  }

  .badge-ring {
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 2px dashed #f59e0b;
    opacity: 0.6;
    animation: spinSlow 14s linear infinite;
  }

  .error-code {
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 3.6rem;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #16a34a 0%, #0f766e 50%, #ca8a04 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }

  .error-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 12px 0;
    letter-spacing: -0.01em;
  }

  .error-desc {
    font-size: 0.92rem;
    line-height: 1.6;
    color: #64748b;
    margin: 0 0 28px 0;
  }

  .error-actions {
    display: flex;
    gap: 12px;
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 24px;
  }

  .btn-primary, .btn-secondary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 11px 20px;
    border-radius: 10px;
    font-size: 0.88rem;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.2s ease;
  }

  .btn-primary {
    background: #16a34a;
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.25);
  }
  .btn-primary:hover {
    background: #15803d;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(22, 163, 74, 0.35);
  }

  .btn-secondary {
    background: #f8fafc;
    color: #334155;
    border: 1px solid #cbd5e1;
  }
  .btn-secondary:hover {
    background: #f1f5f9;
    color: #0f172a;
    border-color: #94a3b8;
  }

  .error-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.74rem;
    color: #94a3b8;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-top: 1px solid #f1f5f9;
    padding-top: 18px;
    width: 100%;
    justify-content: center;
  }

  .dot {
    color: #cbd5e1;
  }

  @keyframes spinSlow {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
</style>
