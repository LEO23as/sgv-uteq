<script>
  import { goto } from '$app/navigation';
  import { login, user } from '$lib/stores';
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
  let datosUsuario = $state(null);

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

      // Verificar si el usuario debe cambiar su clave obligatoriamente
      if (data.debe_cambiar_clave) {
        datosUsuario = data;
        modoCambioClave = true;
        claveNueva = '';
        claveConfirmar = '';
        return;
      }

      // Si no debe cambiar clave, ingresar directamente
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

      // Sesión iniciada con éxito
      window.location.href = '/dashboard';
    } catch (e) {
      error = e.message || 'Error al actualizar la contraseña.';
    } finally {
      guardandoClave = false;
    }
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

  <!-- Main Body with Optimized Background -->
  <div class="sga-body">
    <div class="sga-right-panel">
      
      <!-- Card Container -->
      <div class="sga-card">
        <div class="sga-card-header">
          <img src="/logo-uteq.png" alt="UTEQ Logo" class="sga-mascot-logo" />
          <h2 class="sga-card-heading">
            {modoCambioClave ? 'Cambio de Clave Obligatorio' : 'Entrada al SGV'}
          </h2>
        </div>

        {#if !modoCambioClave}
          <!-- FORMULARIO LOGIN NORMAL -->
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
                placeholder="Ingrese su usuario (ej: pecastrol)"
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
                  onclick={() => { showPassword = !showPassword; }}
                  tabindex="-1"
                  aria-label="Mostrar u ocultar contraseña"
                >
                  <i class="bi {showPassword ? 'bi-eye-slash' : 'bi-eye'}"></i>
                </button>
              </div>
            </div>

            <button type="submit" class="sga-btn-submit" disabled={loading}>
              {#if loading}
                <i class="bi bi-arrow-repeat spin"></i> Verificando...
              {:else}
                <i class="bi bi-arrow-right-short"></i> Entrar
              {/if}
            </button>
          </form>

          <div class="sga-card-footer">
            <p>En caso de problemas, contactar a</p>
            <a href="mailto:soporte.vinculacion@uteq.edu.ec" class="sga-footer-link">soporte.vinculacion@uteq.edu.ec</a>
            <div class="sga-help-row">
              <span class="sga-help-text">¿Has olvidado los datos de la cuenta? Contacta a la Dirección.</span>
            </div>
          </div>

        {:else}
          <!-- FORMULARIO OBLIGATORIO DE PRIMER ACCESO -->
          <div class="primer-acceso-banner">
            <i class="bi bi-shield-lock-fill"></i>
            <div>
              <strong>Primer inicio de sesión</strong>
              <p>Hola <b>{datosUsuario?.nombre || username}</b>, por seguridad debes definir tu contraseña personal para acceder al SGV.</p>
            </div>
          </div>

          <form onsubmit={(e) => { e.preventDefault(); handleCambiarClave(); }} class="sga-form">
            {#if error}
              <div class="sga-alert-danger">
                <i class="bi bi-exclamation-triangle-fill"></i> {error}
              </div>
            {/if}

            <div class="sga-input-group">
              <label for="claveNueva">Nueva Contraseña *</label>
              <div class="sga-pwd-container">
                <input 
                  id="claveNueva" 
                  type={showNewPassword ? 'text' : 'password'} 
                  bind:value={claveNueva} 
                  placeholder="Mínimo 6 caracteres"
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
              <label for="claveConfirmar">Confirmar Nueva Contraseña *</label>
              <input 
                id="claveConfirmar" 
                type={showNewPassword ? 'text' : 'password'} 
                bind:value={claveConfirmar} 
                placeholder="Repite la nueva contraseña"
                required 
              />
            </div>

            <div class="btn-group-cambio">
              <button type="button" class="btn-cancelar-login" onclick={cancelarCambio}>
                Regresar
              </button>
              <button type="submit" class="sga-btn-submit flex-1" disabled={guardandoClave}>
                {#if guardandoClave}
                  <i class="bi bi-arrow-repeat spin"></i> Guardando...
                {:else}
                  <i class="bi bi-check2-circle"></i> Guardar y Entrar
                {/if}
              </button>
            </div>
          </form>
        {/if}

      </div>
    </div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: 'Nunito', sans-serif;
    background-color: #1b7a2b;
    overflow-x: hidden;
  }

  .sga-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
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

  /* Main Body with Instant Loading Background */
  .sga-body {
    flex: 1;
    background: url('/banner.webp') no-repeat center center / cover,
                url('/banner.jpg') no-repeat center center / cover,
                #1b7a2b;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 20px 60px;
    box-sizing: border-box;
    min-height: calc(100vh - 44px);
  }

  @media (max-width: 768px) {
    .sga-body {
      justify-content: center;
      padding: 16px;
    }
  }

  .sga-right-panel {
    width: 100%;
    max-width: 420px;
    display: flex;
    flex-direction: column;
  }

  /* SGA White Card */
  .sga-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 28px 30px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.8);
    animation: fadeIn 0.25s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .sga-card-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 20px;
    gap: 8px;
  }

  .sga-mascot-logo {
    height: 70px;
    width: auto;
    object-fit: contain;
  }

  .sga-card-heading {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 800;
    color: #1e293b;
    text-align: center;
  }

  .sga-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .sga-alert-danger {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 0.82rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .primer-acceso-banner {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e40af;
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 0.8rem;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 16px;
  }

  .primer-acceso-banner i {
    font-size: 1.2rem;
    color: #2563eb;
    flex-shrink: 0;
  }

  .primer-acceso-banner p {
    margin: 3px 0 0;
    font-size: 0.76rem;
    color: #3b82f6;
    line-height: 1.3;
  }

  .sga-input-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .sga-input-group label {
    font-size: 0.76rem;
    font-weight: 800;
    color: #475569;
    letter-spacing: 0.04em;
  }

  .sga-input-group input {
    padding: 10px 12px;
    font-size: 0.9rem;
    font-family: inherit;
    font-weight: 600;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    background-color: #f8fafc;
    color: #1e293b;
    outline: none;
    transition: all 0.18s ease;
  }

  .sga-input-group input:focus {
    border-color: #1b7a2b;
    background-color: #ffffff;
    box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.12);
  }

  .sga-pwd-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .sga-pwd-container input {
    width: 100%;
    padding-right: 38px;
    box-sizing: border-box;
  }

  .sga-pwd-toggle {
    position: absolute;
    right: 10px;
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1.1rem;
    padding: 4px;
    display: flex;
    align-items: center;
  }

  .sga-pwd-toggle:hover {
    color: #1b7a2b;
  }

  .sga-btn-submit {
    margin-top: 6px;
    background-color: #1b7a2b;
    color: #ffffff;
    border: none;
    border-radius: 20px;
    padding: 10px;
    font-size: 0.92rem;
    font-weight: 800;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    box-shadow: 0 4px 12px rgba(27, 122, 43, 0.25);
    transition: all 0.2s ease;
  }

  .sga-btn-submit:hover:not(:disabled) {
    background-color: #155e04;
    transform: translateY(-1px);
  }

  .sga-btn-submit:disabled {
    opacity: 0.65;
    cursor: not-allowed;
  }

  .btn-group-cambio {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
  }

  .flex-1 {
    flex: 1;
  }

  .btn-cancelar-login {
    background: #f1f5f9;
    color: #475569;
    border: 1.5px solid #cbd5e1;
    border-radius: 20px;
    padding: 9px 18px;
    font-size: 0.84rem;
    font-weight: 700;
    cursor: pointer;
  }

  .sga-card-footer {
    margin-top: 20px;
    padding-top: 14px;
    border-top: 1px solid #f1f5f9;
    text-align: center;
    font-size: 0.76rem;
    color: #64748b;
  }

  .sga-card-footer p {
    margin: 0 0 2px;
  }

  .sga-footer-link {
    color: #0284c7;
    text-decoration: none;
    font-weight: 700;
  }

  .sga-footer-link:hover {
    text-decoration: underline;
  }

  .sga-help-row {
    margin-top: 8px;
  }

  .sga-help-text {
    font-size: 0.72rem;
    color: #94a3b8;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 0.7s linear infinite; }
</style>
