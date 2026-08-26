<script>
  import { goto } from '$app/navigation';
  import { login, user } from '$lib/stores';
  import { onMount } from 'svelte';

  let username = $state('');
  let password = $state('');
  let showPassword = $state(false);
  let error = $state('');
  let loading = $state(false);

  onMount(() => {
    if ($user) goto('/dashboard');
  });

  async function handleLogin() {
    error = '';
    loading = true;
    try {
      await login(username, password);
      goto('/dashboard');
    } catch (e) {
      error = e?.error || 'Error al iniciar sesión. Verifique sus credenciales.';
    } finally {
      loading = false;
    }
  }

  function togglePassword() {
    showPassword = !showPassword;
  }
</script>

<svelte:head>
  <title>SGV | Sistema de Georreferenciación de Vinculación — UTEQ</title>
</svelte:head>

<div class="sga-wrapper">
  <!-- Header Bar -->
  <header class="sga-header">
    <div class="sga-header-title">
      <strong>SGV</strong> | Sistema de Georreferenciación de Vinculación
    </div>
  </header>

  <!-- Body Section with Campus Background -->
  <div class="sga-body">
    <div class="sga-right-panel">
      <!-- Login Card -->
      <div class="sga-card">
        <h2 class="sga-card-heading">Entrada al SGV</h2>

        <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }} class="sga-form">
          {#if error}
            <div class="sga-alert-danger">
              <i class="bi bi-exclamation-triangle-fill"></i> {error}
            </div>
          {/if}

          <div class="sga-input-group">
            <label for="username">Usuario</label>
            <input 
              id="username" 
              type="text" 
              bind:value={username} 
              placeholder="Ingrese su usuario"
              required 
            />
          </div>

          <div class="sga-input-group">
            <label for="password">Contraseña</label>
            <div class="sga-pwd-container">
              <input 
                id="password" 
                type={showPassword ? 'text' : 'password'} 
                bind:value={password} 
                placeholder="••••••••••••"
                required 
              />
              <button 
                type="button" 
                class="sga-pwd-toggle" 
                onclick={togglePassword}
                tabindex="-1"
                aria-label="Mostrar u ocultar contraseña"
              >
                <i class="bi {showPassword ? 'bi-eye-slash' : 'bi-eye'}"></i>
              </button>
            </div>
          </div>

          <button type="submit" class="sga-btn-submit" disabled={loading}>
            {#if loading}
              <i class="bi bi-arrow-repeat spin"></i> Entrando...
            {:else}
              <i class="bi bi-arrow-right-short"></i> Entrar
            {/if}
          </button>
        </form>

        <div class="sga-card-footer">
          <p class="sga-support">
            En caso de problemas, contactar a <a href="mailto:soportevinculacion@uteq.edu.ec">soportevinculacion@uteq.edu.ec</a>
          </p>
          <a href="#forgot" onclick={(e) => { e.preventDefault(); alert('Por favor contacte a la Unidad de Vinculación.'); }} class="sga-forgot">
            ¿Has olvidado los datos de la cuenta? Clic aquí!
          </a>
        </div>
      </div>

      <!-- Downloads / Quick Access Card -->
      <div class="sga-card sga-downloads">
        <h3 class="sga-downloads-heading">DESCARGAS</h3>
        <div class="sga-downloads-grid">
          <a href="/dashboard" class="sga-download-box">
            <div class="sga-icon-bg bg-blue">
              <i class="bi bi-journal-text"></i>
            </div>
            <span>Manual de acceso al SGV y Gestión</span>
          </a>
          <a href="/dashboard" class="sga-download-box">
            <div class="sga-icon-bg bg-orange">
              <i class="bi bi-laptop"></i>
            </div>
            <span>Procedimiento de Vinculación</span>
          </a>
          <a href="/dashboard" class="sga-download-box">
            <div class="sga-icon-bg bg-green">
              <i class="bi bi-file-earmark-check"></i>
            </div>
            <span>Solicitud de Proyectos</span>
          </a>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #e9ecef;
  }

  .sga-wrapper {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Header Bar */
  .sga-header {
    background-color: #1b7a2b;
    color: #ffffff;
    padding: 10px 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    z-index: 100;
  }

  .sga-header-title {
    font-size: 1.1rem;
    font-weight: 400;
  }

  .sga-header-title strong {
    font-weight: 700;
  }

  /* Main Body with UTEQ Campus Photo */
  .sga-body {
    flex: 1;
    background: url('https://sga.uteq.edu.ec/static/images/loginsga.jpg') no-repeat center center / cover;
    background-color: #1b7a2b;
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    padding: 30px 40px;
    box-sizing: border-box;
    min-height: calc(100vh - 44px);
  }

  .sga-right-panel {
    width: 100%;
    max-width: 410px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* SGA White Card Container */
  .sga-card {
    background: #ffffff;
    border-radius: 4px;
    padding: 24px 26px 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
  }

  .sga-card-heading {
    margin: 0 0 18px 0;
    font-size: 1.3rem;
    font-weight: 600;
    color: #333333;
  }

  .sga-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .sga-alert-danger {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .sga-input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .sga-input-group label {
    font-size: 0.82rem;
    color: #495057;
    font-weight: 600;
  }

  .sga-input-group input {
    width: 100%;
    padding: 9px 12px;
    font-size: 0.92rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background-color: #e8f0fe;
    color: #212529;
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.15s ease-in-out, background-color 0.15s;
  }

  .sga-input-group input:focus {
    border-color: #1b7a2b;
    background-color: #ffffff;
  }

  /* Password Toggle Container */
  .sga-pwd-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .sga-pwd-container input {
    padding-right: 36px;
  }

  .sga-pwd-toggle {
    position: absolute;
    right: 8px;
    background: transparent;
    border: none;
    color: #6c757d;
    cursor: pointer;
    font-size: 1rem;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sga-pwd-toggle:hover {
    color: #1b7a2b;
  }

  /* Green Submit Button */
  .sga-btn-submit {
    background-color: #5cb85c;
    color: #ffffff;
    border: 1px solid #4cae4c;
    border-radius: 4px;
    padding: 7px 16px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    align-self: flex-start;
    margin-top: 4px;
    transition: background-color 0.15s ease-in-out;
  }

  .sga-btn-submit:hover:not(:disabled) {
    background-color: #4cae4c;
  }

  .sga-btn-submit:disabled {
    opacity: 0.65;
    cursor: not-allowed;
  }

  /* Card Footer Links */
  .sga-card-footer {
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid #e9ecef;
    font-size: 0.8rem;
    color: #6c757d;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .sga-support {
    margin: 0;
  }

  .sga-support a {
    color: #0056b3;
    text-decoration: none;
  }

  .sga-support a:hover {
    text-decoration: underline;
  }

  .sga-forgot {
    color: #0056b3;
    font-weight: 700;
    text-decoration: none;
    font-size: 0.82rem;
  }

  .sga-forgot:hover {
    text-decoration: underline;
  }

  /* Downloads Panel */
  .sga-downloads-heading {
    margin: 0 0 14px 0;
    font-size: 0.9rem;
    font-weight: 700;
    color: #495057;
    text-align: center;
    letter-spacing: 0.5px;
  }

  .sga-downloads-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }

  .sga-download-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 6px;
    text-decoration: none;
    color: #212529;
    padding: 8px 4px;
    border-radius: 4px;
    transition: background-color 0.15s;
  }

  .sga-download-box:hover {
    background-color: #f8f9fa;
  }

  .sga-icon-bg {
    width: 42px;
    height: 42px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    color: #ffffff;
  }

  .bg-blue { background-color: #0056b3; }
  .bg-orange { background-color: #fd7e14; }
  .bg-green { background-color: #28a745; }

  .sga-download-box span {
    font-size: 0.7rem;
    font-weight: 600;
    line-height: 1.2;
    color: #0056b3;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin .7s linear infinite; }

  @media (max-width: 768px) {
    .sga-body {
      justify-content: center;
      padding: 16px;
    }
  }
</style>
