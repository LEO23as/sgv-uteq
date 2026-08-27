<script>
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores';
  import { onMount } from 'svelte';

  let username = $state('');
  let password = $state('');
  let showPassword = $state(false);
  let error = $state('');
  let loading = $state(false);

  // Flujo de Primer Acceso (Cambio de Clave Obligatorio)
  let modoCambioClave = $state(false);
  let claveNueva = $state('');
  let claveConfirmar = $state('');
  let showNewPassword = $state(false);
  let guardandoClave = $state(false);

  onMount(() => {
    if ($user) goto('/dashboard');
  });

  async function handleLogin() {
    error = '';
    loading = true;
    try {
      const res = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Usuario o contraseña incorrectos');

      // Si debe cambiar clave obligatoriamente en su primer acceso
      if (data.debe_cambiar_clave) {
        modoCambioClave = true;
        claveNueva = '';
        claveConfirmar = '';
        return;
      }

      // Si no, entrar al dashboard
      window.location.href = '/dashboard';
    } catch (e) {
      error = e.message || 'Error al iniciar sesión. Verifique sus credenciales.';
    } finally {
      loading = false;
    }
  }

  async function handleCambiarClave() {
    error = '';
    if (!claveNueva || !claveConfirmar) {
      error = 'Debes ingresar y confirmar tu nueva contraseña.';
      return;
    }
    if (claveNueva.length < 6) {
      error = 'La nueva contraseña debe tener al menos 6 caracteres.';
      return;
    }
    if (claveNueva !== claveConfirmar) {
      error = 'Las contraseñas no coinciden.';
      return;
    }

    guardandoClave = true;
    try {
      const res = await fetch('/api/auth/cambiar-clave-primer-acceso/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          clave_actual: password,
          clave_nueva: claveNueva.trim(),
        }),
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al actualizar contraseña');

      // Entrar al sistema con la sesión activa
      window.location.href = '/dashboard';
    } catch (e) {
      error = e.message || 'Error al actualizar la contraseña.';
    } finally {
      guardandoClave = false;
    }
  }

  function togglePassword() {
    showPassword = !showPassword;
  }

  function cancelarCambio() {
    modoCambioClave = false;
    password = '';
    claveNueva = '';
    claveConfirmar = '';
    error = '';
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

  <!-- Main Body with banner.png Background -->
  <div class="sga-body">
    <div class="sga-right-panel">
      <!-- Login Card -->
      <div class="sga-card">
        <div class="sga-card-header">
          <img src="/logo-uteq.png" alt="UTEQ Mascot" class="sga-mascot-logo" />
          <h2 class="sga-card-heading">
            {modoCambioClave ? 'Cambiar Contraseña' : 'Entrada al SGV'}
          </h2>
        </div>

        {#if !modoCambioClave}
          <!-- FORMULARIO LOGIN ORIGINAL -->
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

        {:else}
          <!-- FORMULARIO CAMBIO DE CLAVE CON EL MISMO DISEÑO -->
          <form onsubmit={(e) => { e.preventDefault(); handleCambiarClave(); }} class="sga-form">
            {#if error}
              <div class="sga-alert-danger">
                <i class="bi bi-exclamation-triangle-fill"></i> {error}
              </div>
            {/if}

            <div class="sga-input-group">
              <label for="claveNueva">Nueva Contraseña</label>
              <div class="sga-pwd-container">
                <input 
                  id="claveNueva" 
                  type={showNewPassword ? 'text' : 'password'} 
                  bind:value={claveNueva} 
                  placeholder="Ingrese nueva contraseña"
                  required 
                />
                <button 
                  type="button" 
                  class="sga-pwd-toggle" 
                  onclick={() => { showNewPassword = !showNewPassword; }}
                  tabindex="-1"
                >
                  <i class="bi {showNewPassword ? 'bi-eye-slash' : 'bi-eye'}"></i>
                </button>
              </div>
            </div>

            <div class="sga-input-group">
              <label for="claveConfirmar">Confirmar Contraseña</label>
              <input 
                id="claveConfirmar" 
                type={showNewPassword ? 'text' : 'password'} 
                bind:value={claveConfirmar} 
                placeholder="Repita nueva contraseña"
                required 
              />
            </div>

            <div style="display: flex; gap: 8px; align-items: center; margin-top: 4px;">
              <button type="submit" class="sga-btn-submit" disabled={guardandoClave}>
                {#if guardandoClave}
                  <i class="bi bi-arrow-repeat spin"></i> Guardando...
                {:else}
                  <i class="bi bi-arrow-right-short"></i> Guardar y Entrar
                {/if}
              </button>
              <button type="button" class="btn-cancelar-clean" onclick={cancelarCambio}>
                Regresar
              </button>
            </div>
          </form>

          <div class="sga-card-footer">
            <p class="sga-support">
              Primer acceso al sistema: defina su clave personal para continuar.
            </p>
          </div>
        {/if}

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

  /* Main Body with banner.png Background */
  .sga-body {
    flex: 1;
    background: url('/banner.webp') no-repeat center center / cover,
                url('/banner.jpg') no-repeat center center / cover,
                url('/banner.png') no-repeat center center / cover;
    background-color: #1b7a2b;
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    padding: 40px 50px;
    box-sizing: border-box;
    min-height: calc(100vh - 44px);
  }

  .sga-right-panel {
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* SGA White Card Container */
  .sga-card {
    background: #ffffff;
    border-radius: 6px;
    padding: 26px 28px 22px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  }

  .sga-card-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 20px;
    gap: 10px;
  }

  .sga-mascot-logo {
    height: 75px;
    width: auto;
    object-fit: contain;
  }

  .sga-card-heading {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    color: #222222;
    text-align: center;
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
    padding: 8px 18px;
    font-size: 0.92rem;
    font-weight: 700;
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

  .btn-cancelar-clean {
    background: none;
    border: none;
    color: #6c757d;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    padding: 8px 12px;
  }

  .btn-cancelar-clean:hover {
    text-decoration: underline;
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

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin .7s linear infinite; }

  @media (max-width: 768px) {
    .sga-body {
      justify-content: center;
      padding: 16px;
    }
  }
</style>
