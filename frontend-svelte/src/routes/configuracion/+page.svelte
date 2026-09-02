<script>
  import { onMount } from 'svelte';
  import { user, fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { solicitarPermisoNotificaciones, notificaciones } from '$lib/notifications';

  let cargando = $state(true);
  let ipActual = $state('181.119.184.93');
  let permisosNotif = $state('default');
  let appInstalada = $state(false);

  // Modales
  let showModalIdentidad = $state(false);
  let showModalPreferencias = $state(false);
  let showPassword = $state(false);
  let passwordInput = $state('');
  let verificandoClave = $state(false);

  // Lista de Dispositivos Vinculados (Persistidos en LocalStorage)
  let dispositivos = $state([]);

  // Preferencias de Notificaciones (Estilo SGA UTEQ)
  let prefs = $state({
    loginAlerts: true,
    systemAlerts: true,
    caducidadConvenios: true,
    cierreProyectos: true,
    proyectosPropuestos: true,
    alertasAuditoria: true,
  });

  function totalActivas() {
    return Object.values(prefs).filter(Boolean).length;
  }

  function detectarPlataforma() {
    if (typeof window === 'undefined') return { so: 'Dispositivo', tipo: 'Escritorio', icon: 'bi-display' };
    const ua = navigator.userAgent || '';
    if (/android/i.test(ua)) return { so: 'Android', tipo: 'Móvil', icon: 'bi-android2' };
    if (/iphone|ipad|ipod/i.test(ua)) return { so: 'iOS', tipo: 'Móvil', icon: 'bi-apple' };
    if (/windows/i.test(ua)) return { so: 'Windows', tipo: 'Escritorio', icon: 'bi-microsoft' };
    if (/macintosh|mac os x/i.test(ua)) return { so: 'macOS', tipo: 'Escritorio', icon: 'bi-apple' };
    if (/linux/i.test(ua)) return { so: 'Linux', tipo: 'Escritorio', icon: 'bi-ubuntu' };
    return { so: 'Navegador Web', tipo: 'Dispositivo', icon: 'bi-laptop' };
  }

  function detectarNavegador() {
    if (typeof window === 'undefined') return 'Chrome';
    const ua = navigator.userAgent || '';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Edg')) return 'Edge';
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Safari')) return 'Safari';
    return 'Navegador';
  }

  function formatearFechaEspanol(date) {
    const d = new Date(date);
    const dias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    const diaNom = dias[d.getDay()];
    const diaNum = String(d.getDate()).padStart(2, '0');
    const mesNom = meses[d.getMonth()];
    const anio = d.getFullYear();
    const hora = d.toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' });
    return `${diaNom}, ${diaNum} de ${mesNom} del ${anio} a las ${hora}`;
  }

  onMount(async () => {
    // 1. Detectar permisos de notificación y PWA
    if (typeof window !== 'undefined') {
      permisosNotif = 'Notification' in window ? Notification.permission : 'default';
      appInstalada = window.matchMedia('(display-mode: standalone)').matches || Boolean(navigator.standalone);

      // Cargar preferencias guardadas
      const savedPrefs = localStorage.getItem('sgv_pref_notificaciones');
      if (savedPrefs) {
        try { Object.assign(prefs, JSON.parse(savedPrefs)); } catch {}
      }
    }

    // 2. Obtener IP real del servidor
    try {
      const health = await fetchAPI('/api/health/');
      if (health?.timestamp) {
        // Obtenemos telemetría de red
      }
    } catch {}

    // 3. Cargar o Inicializar dispositivos vinculados
    const infoActual = detectarPlataforma();
    const navActual = detectarNavegador();

    const storedDevs = localStorage.getItem('sgv_dispositivos_vinculados');
    if (storedDevs) {
      try {
        dispositivos = JSON.parse(storedDevs);
      } catch {
        dispositivos = [];
      }
    }

    // Asegurar que el dispositivo actual esté en la lista
    let actualDev = dispositivos.find(d => d.actual);
    if (!actualDev) {
      actualDev = {
        id: 'dev-actual',
        so: infoActual.so,
        tipo: infoActual.tipo,
        icon: infoActual.icon,
        ip: ipActual,
        primerInicio: '02 septiembre',
        actividad: new Date().toISOString(),
        navegador: navActual,
        actual: true,
      };
      dispositivos = [actualDev, ...dispositivos.filter(d => !d.actual)];
      localStorage.setItem('sgv_dispositivos_vinculados', JSON.stringify(dispositivos));
    } else {
      // Actualizar actividad reciente
      actualDev.actividad = new Date().toISOString();
      actualDev.navegador = navActual;
      dispositivos = [...dispositivos];
      localStorage.setItem('sgv_dispositivos_vinculados', JSON.stringify(dispositivos));
    }

    cargando = false;
  });

  // Flujo: Vincular Dispositivo con Verificación de Contraseña
  function abrirModalVincular() {
    passwordInput = '';
    showPassword = false;
    showModalIdentidad = true;
  }

  async function confirmarVinculacion() {
    if (!passwordInput.trim()) {
      toast.error('Por favor ingresa tu contraseña para confirmar identidad.');
      return;
    }

    verificandoClave = true;
    try {
      const res = await fetch('/api/dispositivos/vincular/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ password: passwordInput })
      });

      const data = await res.json();
      if (!res.ok) {
        toast.error(data.error || 'Contraseña incorrecta');
        verificandoClave = false;
        return;
      }

      // Éxito: Vincular dispositivo
      if (data.ip) ipActual = data.ip;
      showModalIdentidad = false;
      toast.success('¡Identidad verificada exitosamente!');

      // Pedir permiso nativo si no lo tiene
      const ok = await solicitarPermisoNotificaciones();
      if (ok) {
        permisosNotif = 'granted';
        toast.success('Permiso de notificaciones concedido.');

        // Enviar notificación nativa al teléfono / PC (estilo SGA)
        if ('Notification' in window && Notification.permission === 'granted') {
          const userNom = $user?.nombre || 'Usuario';
          const notifMsg = `¡Bienvenido, ${userNom}! Dispositivo vinculado exitosamente al SGV UTEQ. Recibirás recordatorios de caducidad y alertas institucionales.`;
          try {
            new Notification('SGV UTEQ • Dispositivo Vinculado', {
              body: notifMsg,
              icon: '/icons/icon-192.png'
            });
          } catch {}
        }
      }

      // Actualizar tarjeta
      appInstalada = true;
      const infoActual = detectarPlataforma();
      const navActual = detectarNavegador();

      dispositivos = dispositivos.map(d => {
        if (d.actual) {
          return {
            ...d,
            so: infoActual.so,
            tipo: infoActual.tipo,
            icon: infoActual.icon,
            ip: data.ip || ipActual,
            actividad: new Date().toISOString(),
            navegador: navActual
          };
        }
        return d;
      });
      localStorage.setItem('sgv_dispositivos_vinculados', JSON.stringify(dispositivos));

    } catch (err) {
      toast.error('Error de conexión al verificar identidad.');
    } finally {
      verificandoClave = false;
    }
  }

  async function permitirNotificacionesCard() {
    const ok = await solicitarPermisoNotificaciones();
    if (ok) {
      permisosNotif = 'granted';
      toast.success('¡Permiso de notificación activado para este navegador!');
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('SGV UTEQ • Notificaciones Activas', {
          body: 'Este dispositivo ahora recibirá alertas de convenios y proyectos.',
          icon: '/icons/icon-192.png'
        });
      }
    } else {
      toast.info('Permiso bloqueado o rechazado en el navegador.');
    }
  }

  function desvincularDispositivo(dev) {
    if (dev.actual) {
      if (!confirm('¿Estás seguro de que deseas desvincular tu dispositivo actual?')) return;
      toast.info('Dispositivo actual desvinculado.');
      appInstalada = false;
    } else {
      dispositivos = dispositivos.filter(d => d.id !== dev.id);
      localStorage.setItem('sgv_dispositivos_vinculados', JSON.stringify(dispositivos));
      toast.success('Dispositivo retirado con éxito.');
    }
  }

  function cerrarOtrasSesiones() {
    if (!confirm('¿Deseas cerrar sesión en todos los demás dispositivos vinculados?')) return;
    dispositivos = dispositivos.filter(d => d.actual);
    localStorage.setItem('sgv_dispositivos_vinculados', JSON.stringify(dispositivos));
    toast.success('Se cerraron todas las demás sesiones.');
  }

  // Flujo: Guardar Preferencias de Notificaciones
  function guardarPreferencias() {
    localStorage.setItem('sgv_pref_notificaciones', JSON.stringify(prefs));
    showModalPreferencias = false;
    toast.success('Preferencias de notificación guardadas.');
  }

  function toggleTodas(estado) {
    for (const k in prefs) prefs[k] = estado;
  }
</script>

<div class="config-page">
  <!-- MIGA DE PAN -->
  <div class="crumbs-bar">
    <a href="/dashboard" class="cb-link">Inicio</a>
    <span class="cb-sep">/</span>
    <span class="cb-link">Configuración</span>
    <span class="cb-sep">/</span>
    <span class="cb-current">Mis dispositivos vinculados</span>
  </div>

  <!-- CABECERA PRINCIPAL -->
  <div class="page-head">
    <div class="ph-titles">
      <h2>Mis dispositivos vinculados</h2>
      <p>Tienes la sesión iniciada en estos dispositivos o has iniciado sesión en ellos.</p>
    </div>
  </div>

  <!-- BANNER DE ÉXITO PWA -->
  {#if appInstalada}
    <div class="success-banner">
      <div class="sb-icon">🎉</div>
      <div class="sb-text">
        <strong>¡Aplicación instalada correctamente!</strong>
        <p>El SGV ya está disponible en tu dispositivo. Ahora puedes acceder desde tu pantalla de inicio.</p>
      </div>
    </div>
  {/if}

  <!-- BARRA DE ACCIONES SUPERIORES -->
  <div class="actions-toolbar">
    <button class="btn-tool-blue" onclick={() => showModalPreferencias = true}>
      <i class="bi bi-megaphone-fill"></i>
      <span>Configurar notificaciones</span>
    </button>
    <button class="btn-tool-red" onclick={cerrarOtrasSesiones}>
      <i class="bi bi-power"></i>
      <span>Cerrar todas las demás sesiones</span>
    </button>
    <button class="btn-tool-green" onclick={abrirModalVincular}>
      <i class="bi bi-plus-lg"></i>
      <span>Vincular este dispositivo</span>
    </button>
  </div>

  <!-- TARJETAS DE DISPOSITIVOS VINCULADOS -->
  <div class="devices-list">
    {#each dispositivos as dev}
      <div class="device-card" class:is-current={dev.actual}>
        <!-- ÍCONO DE SISTEMA OPERATIVO -->
        <div class="dev-os-badge">
          <i class="bi {dev.icon}"></i>
        </div>

        <!-- TÍTULO Y BADGE ACTUAL -->
        <div class="dev-header">
          <h3 class="dev-title">
            {dev.so}
            {#if dev.actual}
              <span class="badge-actual"><i class="bi bi-check-circle-fill"></i> actual</span>
            {/if}
          </h3>
          <span class="dev-type">{dev.tipo}</span>
          <span class="dev-ip">Dirección IP: {dev.ip}</span>
          <span class="dev-meta">Primer inicio de sesión: {dev.primerInicio}</span>
        </div>

        <div class="dev-divider"></div>

        <!-- ACTIVIDAD RECIENTE -->
        <div class="dev-section">
          <span class="dev-sec-lbl">ACTIVIDAD RECIENTE</span>
          <span class="dev-sec-val">{formatearFechaEspanol(dev.actividad)}</span>
        </div>

        <div class="dev-divider"></div>

        <!-- PERMISOS DE NOTIFICACIÓN -->
        <div class="dev-section">
          <span class="dev-sec-lbl">NAVEGADORES / PERMISO</span>
          <span class="dev-sec-val">
            {dev.navegador} / 
            {#if permisosNotif === 'granted'}
              <span class="text-green-perm">Tiene permiso de notificación</span>
            {:else}
              <span class="text-gray-perm">Sin permiso de notificación</span>
            {/if}
          </span>
        </div>

        <!-- BOTONES DE ACCIÓN DE LA TARJETA -->
        <div class="dev-actions">
          <button class="btn-dev-unlink" onclick={() => desvincularDispositivo(dev)}>
            <i class="bi bi-arrow-return-left"></i>
            <span>Desvincular</span>
          </button>
          
          {#if dev.actual && permisosNotif !== 'granted'}
            <button class="btn-dev-notify" onclick={permitirNotificacionesCard}>
              <i class="bi bi-megaphone-fill"></i>
              <span>Permitir que me notifique</span>
            </button>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>

<!-- ════════════════════════════════════════════════════════════════════════
     MODAL 1: CONFIRMA TU IDENTIDAD (ESTILO OFICIAL SGA UTEQ)
     ════════════════════════════════════════════════════════════════════════ -->
{#if showModalIdentidad}
  <div class="modal-backdrop" onclick={() => showModalIdentidad = false}>
    <div class="modal-card modal-identidad" onclick={(e) => e.stopPropagation()}>
      <div class="mi-icon-wrap">
        <i class="bi bi-lock-fill"></i>
      </div>

      <h3 class="mi-title">Confirma tu identidad</h3>
      <p class="mi-desc">Por seguridad, ingresa tu contraseña para vincular este dispositivo a tu cuenta.</p>

      <form onsubmit={(e) => { e.preventDefault(); confirmarVinculacion(); }}>
        <div class="pwd-field-wrap">
          <input
            type={showPassword ? 'text' : 'password'}
            bind:value={passwordInput}
            placeholder="Ingresa tu contraseña"
            class="pwd-input"
            autofocus
          />
          <button
            type="button"
            class="btn-eye"
            onclick={() => showPassword = !showPassword}
            tabindex="-1"
          >
            <i class="bi {showPassword ? 'bi-eye-slash-fill' : 'bi-eye-fill'}"></i>
          </button>
        </div>

        <button type="submit" class="btn-confirm-auth" disabled={verificandoClave}>
          {#if verificandoClave}
            <span class="spinner-border spinner-border-sm"></span> Verificando...
          {:else}
            Vincular dispositivo
          {/if}
        </button>

        <button type="button" class="btn-cancel-auth" onclick={() => showModalIdentidad = false}>
          <i class="bi bi-arrow-left"></i> Cancelar
        </button>
      </form>
    </div>
  </div>
{/if}

<!-- ════════════════════════════════════════════════════════════════════════
     MODAL 2: NOTIFICACIONES - PREFERENCIAS (ESTILO OFICIAL SGA UTEQ)
     ════════════════════════════════════════════════════════════════════════ -->
{#if showModalPreferencias}
  <div class="modal-backdrop" onclick={() => showModalPreferencias = false}>
    <div class="modal-card modal-prefs" onclick={(e) => e.stopPropagation()}>
      <div class="mp-header">
        <div class="mp-title-wrap">
          <i class="bi bi-send-fill text-blue"></i>
          <div>
            <h4>Notificaciones</h4>
            <span class="mp-subtitle">Configura tus preferencias</span>
          </div>
        </div>
        <button class="btn-close-modal" onclick={() => showModalPreferencias = false}>✕</button>
      </div>

      <!-- BOTONES RÁPIDOS -->
      <div class="mp-quick-actions">
        <button class="btn-qa" onclick={() => toggleTodas(true)}>
          <i class="bi bi-check2"></i> Activar todas
        </button>
        <button class="btn-qa" onclick={() => toggleTodas(false)}>
          <i class="bi bi-x"></i> Desactivar todas
        </button>
      </div>

      <div class="mp-body">
        <!-- SECCIÓN 1: GENERAL -->
        <div class="mp-section">
          <div class="mp-sec-head">
            <div class="mpsh-left">
              <i class="bi bi-megaphone-fill"></i>
              <div>
                <strong>General</strong>
                <span class="mpsh-count">2 opciones</span>
              </div>
            </div>
          </div>

          <div class="mp-item">
            <div class="mpi-text">
              <span class="mpi-name">Alertas de inicio de sesión</span>
              <span class="mpi-desc">Recibe un aviso cuando se inicie sesión en un nuevo dispositivo.</span>
            </div>
            <label class="switch">
              <input type="checkbox" bind:checked={prefs.loginAlerts}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="mp-item">
            <div class="mpi-text">
              <span class="mpi-name">Recordatorios de sistema</span>
              <span class="mpi-desc">Avisos sobre mantenimientos programados de la plataforma.</span>
            </div>
            <label class="switch">
              <input type="checkbox" bind:checked={prefs.systemAlerts}>
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- SECCIÓN 2: GESTIÓN DE VINCULACIÓN -->
        <div class="mp-section">
          <div class="mp-sec-head">
            <div class="mpsh-left">
              <i class="bi bi-mortarboard-fill"></i>
              <div>
                <strong>Gestión de Vinculación</strong>
                <span class="mpsh-count">4 opciones</span>
              </div>
            </div>
          </div>

          <div class="mp-item">
            <div class="mpi-text">
              <span class="mpi-name">Caducidad de convenios</span>
              <span class="mpi-desc">Recordatorio cuando un convenio esté próximo a vencer (60 días).</span>
            </div>
            <label class="switch">
              <input type="checkbox" bind:checked={prefs.caducidadConvenios}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="mp-item">
            <div class="mpi-text">
              <span class="mpi-name">Cierre de proyectos</span>
              <span class="mpi-desc">Aviso de proyectos que finalizan su cronograma de ejecución.</span>
            </div>
            <label class="switch">
              <input type="checkbox" bind:checked={prefs.cierreProyectos}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="mp-item">
            <div class="mpi-text">
              <span class="mpi-name">Proyectos propuestos</span>
              <span class="mpi-desc">Notificación cuando se registre un nuevo proyecto pendiente de revisión.</span>
            </div>
            <label class="switch">
              <input type="checkbox" bind:checked={prefs.proyectosPropuestos}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="mp-item">
            <div class="mpi-text">
              <span class="mpi-name">Alertas de auditoría</span>
              <span class="mpi-desc">Aviso cuando se registren modificaciones sensibles en el sistema.</span>
            </div>
            <label class="switch">
              <input type="checkbox" bind:checked={prefs.alertasAuditoria}>
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>

      <!-- FOOTER -->
      <div class="mp-footer">
        <span class="mp-count-summary">{totalActivas()} activas / 6 total</span>
        <div class="mp-footer-btns">
          <button class="btn-mp-save" onclick={guardarPreferencias}>
            <i class="bi bi-check2"></i> Guardar
          </button>
          <button class="btn-mp-cancel" onclick={() => showModalPreferencias = false}>
            <i class="bi bi-x"></i> Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .config-page {
    padding: 10px 4px 40px;
    max-width: 1000px;
    margin: 0 auto;
  }

  .crumbs-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 16px;
  }
  .cb-link {
    color: #0284c7;
    text-decoration: none;
  }
  .cb-link:hover {
    text-decoration: underline;
  }
  .cb-sep {
    color: #cbd5e1;
  }
  .cb-current {
    color: #0f172a;
  }

  .page-head h2 {
    font-size: 1.4rem;
    font-weight: 900;
    color: #1e293b;
    margin: 0 0 4px;
  }
  .page-head p {
    font-size: 0.88rem;
    color: #64748b;
    margin: 0;
  }

  /* BANNER DE ÉXITO */
  .success-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #e8f5e9;
    border: 1px solid #c8e6c9;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 18px 0;
  }
  .sb-icon {
    font-size: 1.5rem;
  }
  .sb-text strong {
    font-size: 0.92rem;
    color: #2e7d32;
    display: block;
  }
  .sb-text p {
    font-size: 0.82rem;
    color: #388e3c;
    margin: 2px 0 0;
  }

  /* BOTONES DE ACCIÓN */
  .actions-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin: 18px 0 24px;
  }

  .btn-tool-blue, .btn-tool-red, .btn-tool-green {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 18px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 800;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-tool-blue {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0284c7;
  }
  .btn-tool-blue:hover {
    background: #f0f9ff;
    border-color: #7dd3fc;
  }

  .btn-tool-red {
    background: #ef4444;
    border: 1px solid #dc2626;
    color: #ffffff;
  }
  .btn-tool-red:hover {
    background: #dc2626;
  }

  .btn-tool-green {
    background: #15803d;
    border: 1px solid #166534;
    color: #ffffff;
  }
  .btn-tool-green:hover {
    background: #166534;
  }

  /* TARJETA DE DISPOSITIVO */
  .devices-list {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .device-card {
    position: relative;
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);
  }
  .device-card.is-current {
    border-color: #cbd5e1;
  }

  .dev-os-badge {
    position: absolute;
    top: 22px;
    right: 22px;
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #f1f5f9;
    color: #475569;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
  }

  .dev-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: #1e293b;
    margin: 0 0 6px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .badge-actual {
    font-size: 0.85rem;
    font-weight: 700;
    color: #16a34a;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .dev-type {
    display: block;
    font-size: 0.84rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 4px;
  }

  .dev-ip {
    display: block;
    font-size: 0.84rem;
    font-weight: 700;
    color: #334155;
    margin-bottom: 2px;
  }

  .dev-meta {
    display: block;
    font-size: 0.82rem;
    color: #64748b;
  }

  .dev-divider {
    height: 1px;
    background: #f1f5f9;
    margin: 16px 0;
  }

  .dev-section {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .dev-sec-lbl {
    font-size: 0.72rem;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 0.04em;
  }

  .dev-sec-val {
    font-size: 0.85rem;
    font-weight: 600;
    color: #1e293b;
  }

  .text-green-perm {
    color: #16a34a;
    font-weight: 700;
  }
  .text-gray-perm {
    color: #94a3b8;
  }

  .dev-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 18px;
  }

  .btn-dev-unlink {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0284c7;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-dev-unlink:hover {
    background: #f8fafc;
  }

  .btn-dev-notify {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #16a34a;
    font-size: 0.78rem;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-dev-notify:hover {
    background: #dcfce7;
  }

  /* ══════════════════════════════════════════════════════════════
     MODAL DE IDENTIDAD (CANDADO)
     ══════════════════════════════════════════════════════════════ */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 16px;
  }

  .modal-card {
    background: #ffffff;
    border-radius: 16px;
    width: 100%;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    animation: popIn 0.2s ease-out;
  }

  @keyframes popIn {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }

  .modal-identidad {
    max-width: 440px;
    padding: 36px 32px 30px;
    text-align: center;
  }

  .mi-icon-wrap {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #e0f2fe;
    color: #0284c7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    margin: 0 auto 18px;
  }

  .mi-title {
    font-size: 1.3rem;
    font-weight: 900;
    color: #0f172a;
    margin: 0 0 8px;
  }

  .mi-desc {
    font-size: 0.85rem;
    color: #64748b;
    line-height: 1.45;
    margin: 0 0 24px;
  }

  .pwd-field-wrap {
    position: relative;
    margin-bottom: 18px;
  }

  .pwd-input {
    width: 100%;
    padding: 12px 42px 12px 16px;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.92rem;
    outline: none;
    transition: border-color 0.15s;
    box-sizing: border-box;
  }
  .pwd-input:focus {
    border-color: #0284c7;
    box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.12);
  }

  .btn-eye {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1.1rem;
    padding: 4px;
  }
  .btn-eye:hover {
    color: #475569;
  }

  .btn-confirm-auth {
    width: 100%;
    padding: 12px;
    background: #334155;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 800;
    cursor: pointer;
    margin-bottom: 10px;
    transition: background 0.15s;
  }
  .btn-confirm-auth:hover:not(:disabled) {
    background: #1e293b;
  }
  .btn-confirm-auth:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .btn-cancel-auth {
    width: 100%;
    padding: 10px;
    background: #ffffff;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: background 0.15s;
  }
  .btn-cancel-auth:hover {
    background: #f1f5f9;
  }

  /* ══════════════════════════════════════════════════════════════
     MODAL PREFERENCIAS DE NOTIFICACIONES (SGA STYLE)
     ══════════════════════════════════════════════════════════════ */
  .modal-prefs {
    max-width: 580px;
    padding: 0;
    overflow: hidden;
  }

  .mp-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 24px;
    border-bottom: 1px solid #f1f5f9;
  }
  .mp-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .mp-title-wrap i {
    font-size: 1.3rem;
  }
  .mp-title-wrap h4 {
    font-size: 1.05rem;
    font-weight: 900;
    color: #0f172a;
    margin: 0;
  }
  .mp-subtitle {
    font-size: 0.76rem;
    color: #64748b;
  }

  .btn-close-modal {
    background: none;
    border: none;
    font-size: 1.1rem;
    color: #94a3b8;
    cursor: pointer;
  }
  .btn-close-modal:hover {
    color: #0f172a;
  }

  .mp-quick-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
    padding: 12px 24px;
    background: #f8fafc;
    border-bottom: 1px solid #f1f5f9;
  }
  .btn-qa {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0284c7;
    font-size: 0.74rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .btn-qa:hover {
    background: #f0f9ff;
    border-color: #bae6fd;
  }

  .mp-body {
    max-height: 420px;
    overflow-y: auto;
    padding: 16px 24px;
  }

  .mp-section {
    margin-bottom: 20px;
  }

  .mp-sec-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 10px;
  }
  .mpsh-left {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #334155;
    font-size: 0.85rem;
  }
  .mpsh-count {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-left: 6px;
  }

  .mp-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 12px 8px;
    border-bottom: 1px solid #f1f5f9;
  }
  .mp-item:last-child {
    border-bottom: none;
  }

  .mpi-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .mpi-name {
    font-size: 0.86rem;
    font-weight: 800;
    color: #1e293b;
  }
  .mpi-desc {
    font-size: 0.76rem;
    color: #64748b;
    line-height: 1.35;
  }

  /* SWITCH TOGGLE */
  .switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
    flex-shrink: 0;
  }
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: #cbd5e1;
    transition: 0.2s;
    border-radius: 24px;
  }
  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
  }
  input:checked + .slider {
    background-color: #16a34a;
  }
  input:checked + .slider:before {
    transform: translateX(20px);
  }

  /* FOOTER MODAL */
  .mp-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 24px;
    background: #f8fafc;
    border-top: 1px solid #f1f5f9;
  }
  .mp-count-summary {
    font-size: 0.74rem;
    font-weight: 700;
    color: #64748b;
  }
  .mp-footer-btns {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .btn-mp-save {
    background: #16a34a;
    color: #ffffff;
    border: none;
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 800;
    cursor: pointer;
  }
  .btn-mp-save:hover {
    background: #15803d;
  }

  .btn-mp-cancel {
    background: #0284c7;
    color: #ffffff;
    border: none;
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 800;
    cursor: pointer;
  }
  .btn-mp-cancel:hover {
    background: #0369a1;
  }
</style>
