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
  let showModalAyudaPermiso = $state(false);
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
    if (/android/i.test(ua)) return { so: 'Android', tipo: 'Móvil', icon: 'bi-phone-fill' };
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
    if (typeof window !== 'undefined') {
      permisosNotif = 'Notification' in window ? Notification.permission : 'default';
      appInstalada = window.matchMedia('(display-mode: standalone)').matches || Boolean(navigator.standalone);

      const savedPrefs = localStorage.getItem('sgv_pref_notificaciones');
      if (savedPrefs) {
        try { Object.assign(prefs, JSON.parse(savedPrefs)); } catch {}
      }
    }

    try {
      const health = await fetchAPI('/api/health/');
      if (health?.timestamp) {
        // Obtenemos telemetría
      }
    } catch {}

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
      actualDev.actividad = new Date().toISOString();
      actualDev.navegador = navActual;
      dispositivos = [...dispositivos];
      localStorage.setItem('sgv_dispositivos_vinculados', JSON.stringify(dispositivos));
    }

    cargando = false;
  });

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

      if (data.ip) ipActual = data.ip;
      showModalIdentidad = false;
      toast.success('¡Identidad verificada exitosamente!');

      const ok = await solicitarPermisoNotificaciones();
      if (ok) {
        permisosNotif = 'granted';
        toast.success('Permiso de notificaciones concedido.');

        if ('Notification' in window && Notification.permission === 'granted') {
          const userNom = $user?.nombre || 'Usuario';
          const notifMsg = `¡Bienvenido, ${userNom}! Dispositivo vinculado exitosamente al SGV UTEQ.`;
          try {
            new Notification('SGV UTEQ • Dispositivo Vinculado', {
              body: notifMsg,
              icon: '/icons/icon-192.png'
            });
          } catch {}
        }
      } else {
        if ('Notification' in window && Notification.permission === 'denied') {
          showModalAyudaPermiso = true;
        }
      }

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
    if ('Notification' in window && Notification.permission === 'denied') {
      showModalAyudaPermiso = true;
      return;
    }

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
      if ('Notification' in window && Notification.permission === 'denied') {
        showModalAyudaPermiso = true;
      } else {
        toast.info('Solicitud de notificación cancelada.');
      }
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

  function guardarPreferencias() {
    localStorage.setItem('sgv_pref_notificaciones', JSON.stringify(prefs));
    showModalPreferencias = false;
    toast.success('Preferencias de notificación guardadas.');
  }

  function toggleTodas(estado) {
    for (const k in prefs) prefs[k] = estado;
  }
</script>

<svelte:head>
  <title>Mis Dispositivos — SGV UTEQ</title>
</svelte:head>

<!-- SUBBAR INSTITUCIONAL (ESTILO UNIFORME SGV) -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Configuración</span>
    <span class="sep">/</span>
    <span class="current">Mis dispositivos</span>
  </nav>

  <div class="subbar-actions">
    <button class="btn-nuevo" onclick={abrirModalVincular}>
      <i class="bi bi-plus-lg"></i> Vincular dispositivo
    </button>
  </div>
</div>

<!-- CUERPO PRINCIPAL DEL MÓDULO -->
<div class="page-wrap">

  <!-- PESTAÑAS DE CONFIGURACIÓN -->
  <div class="config-tabs-nav">
    <a href="/configuracion" class="cfg-tab active">
      <i class="bi bi-phone"></i>
      <span>Mis dispositivos</span>
    </a>
    <a href="/usuarios" class="cfg-tab">
      <i class="bi bi-people-fill"></i>
      <span>Gestión de usuarios</span>
    </a>
    <a href="/periodos" class="cfg-tab">
      <i class="bi bi-calendar3"></i>
      <span>Períodos académicos</span>
    </a>
    <a href="/auditoria" class="cfg-tab">
      <i class="bi bi-shield-check"></i>
      <span>Bitácora de Auditoría</span>
    </a>
  </div>

  <div class="page-top">
    <div>
      <h2 class="page-title"><i class="bi bi-phone"></i> Mis dispositivos vinculados</h2>
      <p class="page-sub">Tienes la sesión iniciada en estos dispositivos o has iniciado sesión en ellos.</p>
    </div>
  </div>

  <!-- BANNER DE ÉXITO PWA -->
  {#if appInstalada}
    <div class="alert-pwa-success">
      <div class="aps-icon">🎉</div>
      <div class="aps-content">
        <strong>¡Aplicación instalada correctamente!</strong>
        <p>El SGV ya está disponible en tu dispositivo. Ahora puedes acceder desde tu pantalla de inicio.</p>
      </div>
    </div>
  {/if}

  <!-- BARRA DE ACCIONES SUPERIORES (ESTILO SGA UTEQ) -->
  <div class="toolbar-sga">
    <button class="btn-sga-blue" onclick={() => showModalPreferencias = true}>
      <i class="bi bi-megaphone-fill"></i>
      <span>Configurar notificaciones</span>
    </button>
    <button class="btn-sga-red" onclick={cerrarOtrasSesiones}>
      <i class="bi bi-power"></i>
      <span>Cerrar todas las demás sesiones</span>
    </button>
    <button class="btn-sga-green" onclick={abrirModalVincular}>
      <i class="bi bi-plus-lg"></i>
      <span>Vincular este dispositivo</span>
    </button>
  </div>

  <!-- TARJETAS DE DISPOSITIVOS VINCULADOS -->
  <div class="devices-stack">
    {#each dispositivos as dev}
      <div class="dev-card-sga" class:is-current={dev.actual}>
        <div class="dev-badge-icon">
          <i class="bi {dev.icon}"></i>
        </div>

        <div class="dev-top-info">
          <div class="dev-name-row">
            <span class="dev-os-title">{dev.so}</span>
            {#if dev.actual}
              <span class="dev-actual-tag"><i class="bi bi-check-circle-fill"></i> actual</span>
            {/if}
          </div>
          <span class="dev-sub-type">{dev.tipo}</span>
          <span class="dev-ip-info">Dirección IP: {dev.ip}</span>
          <span class="dev-login-first">Primer inicio de sesión: {dev.primerInicio}</span>
        </div>

        <div class="dev-hr"></div>

        <div class="dev-meta-block">
          <span class="dmb-label">ACTIVIDAD RECIENTE</span>
          <span class="dmb-value">{formatearFechaEspanol(dev.actividad)}</span>
        </div>

        <div class="dev-hr"></div>

        <div class="dev-meta-block">
          <span class="dmb-label">NAVEGADORES / PERMISO</span>
          <span class="dmb-value">
            {dev.navegador} / 
            {#if permisosNotif === 'granted'}
              <span class="badge-perm-ok">Tiene permiso de notificación</span>
            {:else}
              <span class="badge-perm-no">Sin permiso de notificación</span>
            {/if}
          </span>
        </div>

        <div class="dev-card-footer">
          <button class="btn-card-unlink" onclick={() => desvincularDispositivo(dev)}>
            <i class="bi bi-arrow-return-left"></i>
            <span>Desvincular</span>
          </button>
          
          {#if dev.actual && permisosNotif !== 'granted'}
            <button class="btn-card-notify" onclick={permitirNotificacionesCard}>
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
    <div class="modal-box modal-identidad" onclick={(e) => e.stopPropagation()}>
      <div class="mi-lock-circle">
        <i class="bi bi-lock-fill"></i>
      </div>

      <h3 class="mi-title">Confirma tu identidad</h3>
      <p class="mi-subtitle">Por seguridad, ingresa tu contraseña para vincular este dispositivo a tu cuenta.</p>

      <form onsubmit={(e) => { e.preventDefault(); confirmarVinculacion(); }}>
        <div class="pwd-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            bind:value={passwordInput}
            placeholder="Ingresa tu contraseña"
            class="pwd-input"
            autofocus
          />
          <button
            type="button"
            class="btn-eye-toggle"
            onclick={() => showPassword = !showPassword}
            tabindex="-1"
          >
            <i class="bi {showPassword ? 'bi-eye-slash-fill' : 'bi-eye-fill'}"></i>
          </button>
        </div>

        <button type="submit" class="btn-auth-submit" disabled={verificandoClave}>
          {#if verificandoClave}
            <span class="spinner-border spinner-border-sm"></span> Verificando...
          {:else}
            Vincular dispositivo
          {/if}
        </button>

        <button type="button" class="btn-auth-cancel" onclick={() => showModalIdentidad = false}>
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
    <div class="modal-box modal-prefs" onclick={(e) => e.stopPropagation()}>
      <div class="mp-head">
        <div class="mp-head-title">
          <i class="bi bi-send-fill text-blue"></i>
          <div>
            <h4>Notificaciones</h4>
            <span>Configura tus preferencias</span>
          </div>
        </div>
        <button class="btn-mp-close" onclick={() => showModalPreferencias = false}>✕</button>
      </div>

      <div class="mp-actions-bar">
        <button class="btn-mp-action" onclick={() => toggleTodas(true)}>
          <i class="bi bi-check2"></i> Activar todas
        </button>
        <button class="btn-mp-action" onclick={() => toggleTodas(false)}>
          <i class="bi bi-x"></i> Desactivar todas
        </button>
      </div>

      <div class="mp-scroll-body">
        <div class="mp-group">
          <div class="mp-group-title">
            <i class="bi bi-megaphone-fill"></i>
            <span>General</span>
            <small>2 opciones</small>
          </div>

          <div class="mp-row">
            <div class="mpr-info">
              <span class="mpr-name">Alertas de inicio de sesión</span>
              <span class="mpr-desc">Recibe un aviso cuando se inicie sesión en un nuevo dispositivo.</span>
            </div>
            <label class="switch-sga">
              <input type="checkbox" bind:checked={prefs.loginAlerts}>
              <span class="slider-sga"></span>
            </label>
          </div>

          <div class="mp-row">
            <div class="mpr-info">
              <span class="mpr-name">Recordatorios de sistema</span>
              <span class="mpr-desc">Avisos sobre mantenimientos programados de la plataforma.</span>
            </div>
            <label class="switch-sga">
              <input type="checkbox" bind:checked={prefs.systemAlerts}>
              <span class="slider-sga"></span>
            </label>
          </div>
        </div>

        <div class="mp-group">
          <div class="mp-group-title">
            <i class="bi bi-mortarboard-fill"></i>
            <span>Gestión de Vinculación</span>
            <small>4 opciones</small>
          </div>

          <div class="mp-row">
            <div class="mpr-info">
              <span class="mpr-name">Caducidad de convenios</span>
              <span class="mpr-desc">Recordatorio cuando un convenio esté próximo a vencer (60 días).</span>
            </div>
            <label class="switch-sga">
              <input type="checkbox" bind:checked={prefs.caducidadConvenios}>
              <span class="slider-sga"></span>
            </label>
          </div>

          <div class="mp-row">
            <div class="mpr-info">
              <span class="mpr-name">Cierre de proyectos</span>
              <span class="mpr-desc">Aviso de proyectos que finalizan su cronograma de ejecución.</span>
            </div>
            <label class="switch-sga">
              <input type="checkbox" bind:checked={prefs.cierreProyectos}>
              <span class="slider-sga"></span>
            </label>
          </div>

          <div class="mp-row">
            <div class="mpr-info">
              <span class="mpr-name">Proyectos propuestos</span>
              <span class="mpr-desc">Notificación cuando se registre un nuevo proyecto pendiente de revisión.</span>
            </div>
            <label class="switch-sga">
              <input type="checkbox" bind:checked={prefs.proyectosPropuestos}>
              <span class="slider-sga"></span>
            </label>
          </div>

          <div class="mp-row">
            <div class="mpr-info">
              <span class="mpr-name">Alertas de auditoría</span>
              <span class="mpr-desc">Aviso cuando se registren modificaciones sensibles en el sistema.</span>
            </div>
            <label class="switch-sga">
              <input type="checkbox" bind:checked={prefs.alertasAuditoria}>
              <span class="slider-sga"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="mp-foot">
        <span class="mp-total-txt">{totalActivas()} activas / 6 total</span>
        <div class="mp-foot-btns">
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

<!-- ════════════════════════════════════════════════════════════════════════
     MODAL 3: GUÍA PARA DESBLOQUEAR NOTIFICACIONES EN EL NAVEGADOR
     ════════════════════════════════════════════════════════════════════════ -->
{#if showModalAyudaPermiso}
  <div class="modal-backdrop" onclick={() => showModalAyudaPermiso = false}>
    <div class="modal-box modal-ayuda" onclick={(e) => e.stopPropagation()}>
      <div class="may-icon">
        <i class="bi bi-exclamation-triangle-fill"></i>
      </div>
      <h3 class="may-title">Notificaciones bloqueadas en tu navegador</h3>
      <p class="may-desc">Tu navegador tiene bloqueado el permiso de notificaciones para este enlace. Para habilitarlas sigue estos 3 pasos:</p>

      <div class="may-steps">
        <div class="may-step">
          <span class="ms-num">1</span>
          <div class="ms-txt">Haz clic en el icono <strong>"No es seguro"</strong> o candado a la izquierda de la dirección URL en la barra superior.</div>
        </div>
        <div class="may-step">
          <span class="ms-num">2</span>
          <div class="ms-txt">Busca la opción <strong>"Notificaciones"</strong> y cambia de <em>Bloquear</em> a <strong>"Permitir"</strong>.</div>
        </div>
        <div class="may-step">
          <span class="ms-num">3</span>
          <div class="ms-txt">Recarga la página (presiona <strong>Ctrl + F5</strong>) para aplicar los cambios.</div>
        </div>
      </div>

      <button class="btn-auth-submit" onclick={() => showModalAyudaPermiso = false}>
        ¡Entendido!
      </button>
    </div>
  </div>
{/if}

<style>
  /* Pestañas de Configuración */
  .config-tabs-nav {
    display: flex;
    gap: 8px;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 18px;
    flex-wrap: wrap;
    background: #fff;
    padding: 6px 16px 0;
    border-radius: 12px 12px 0 0;
  }
  .cfg-tab {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    font-size: 0.86rem;
    font-weight: 700;
    color: #64748b;
    text-decoration: none;
    border-bottom: 2.5px solid transparent;
    margin-bottom: -2px;
    transition: all 0.2s ease;
  }
  .cfg-tab:hover {
    color: #1b7505;
    background: #f8fafc;
    border-radius: 6px 6px 0 0;
  }
  .cfg-tab.active {
    color: #1b7505;
    border-bottom-color: #1b7505;
  }

  /* ══════════════════════════════════════════════════════════════
     ESTILOS BASE UNIFORMES SGV UTEQ
     ══════════════════════════════════════════════════════════════ */
  .subbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 24px;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 20px;
  }
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    font-weight: 700;
  }
  .breadcrumb a {
    color: #0284c7;
    text-decoration: none;
  }
  .breadcrumb a:hover {
    text-decoration: underline;
  }
  .breadcrumb .sep {
    color: #94a3b8;
  }
  .breadcrumb .current {
    color: #1e293b;
  }

  .btn-nuevo {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #15803d;
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 800;
    padding: 7px 14px;
    border-radius: 7px;
    border: none;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-nuevo:hover {
    background: #166534;
  }

  .page-wrap {
    padding: 0 24px 40px;
    max-width: 1040px;
    margin: 0 auto;
  }
  .page-top {
    margin-bottom: 18px;
  }
  .page-title {
    font-size: 1.35rem;
    font-weight: 900;
    color: #1e293b;
    margin: 0 0 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .page-title i {
    color: #15803d;
  }
  .page-sub {
    font-size: 0.85rem;
    color: #64748b;
    margin: 0;
  }

  /* BANNER ÉXITO */
  .alert-pwa-success {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #e8f5e9;
    border: 1px solid #c8e6c9;
    border-radius: 10px;
    padding: 12px 18px;
    margin-bottom: 18px;
  }
  .aps-icon {
    font-size: 1.4rem;
  }
  .aps-content strong {
    font-size: 0.9rem;
    color: #2e7d32;
    display: block;
  }
  .aps-content p {
    font-size: 0.8rem;
    color: #388e3c;
    margin: 2px 0 0;
  }

  /* BARRA DE ACCIONES SGA */
  .toolbar-sga {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 22px;
  }
  .btn-sga-blue, .btn-sga-red, .btn-sga-green {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 800;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-sga-blue {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0284c7;
  }
  .btn-sga-blue:hover {
    background: #f0f9ff;
    border-color: #7dd3fc;
  }
  .btn-sga-red {
    background: #ef4444;
    border: 1px solid #dc2626;
    color: #ffffff;
  }
  .btn-sga-red:hover {
    background: #dc2626;
  }
  .btn-sga-green {
    background: #15803d;
    border: 1px solid #166534;
    color: #ffffff;
  }
  .btn-sga-green:hover {
    background: #166534;
  }

  /* TARJETAS DE DISPOSITIVO SGA */
  .devices-stack {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .dev-card-sga {
    position: relative;
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
  }
  .dev-badge-icon {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: #f1f5f9;
    color: #475569;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
  }

  .dev-name-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
  }
  .dev-os-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: #1e293b;
  }
  .dev-actual-tag {
    font-size: 0.84rem;
    font-weight: 700;
    color: #16a34a;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .dev-sub-type {
    display: block;
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 3px;
  }
  .dev-ip-info {
    display: block;
    font-size: 0.82rem;
    font-weight: 700;
    color: #334155;
    margin-bottom: 2px;
  }
  .dev-login-first {
    display: block;
    font-size: 0.8rem;
    color: #64748b;
  }

  .dev-hr {
    height: 1px;
    background: #f1f5f9;
    margin: 14px 0;
  }

  .dev-meta-block {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .dmb-label {
    font-size: 0.7rem;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 0.04em;
  }
  .dmb-value {
    font-size: 0.84rem;
    font-weight: 600;
    color: #1e293b;
  }
  .badge-perm-ok {
    color: #16a34a;
    font-weight: 700;
  }
  .badge-perm-no {
    color: #94a3b8;
  }

  .dev-card-footer {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 16px;
  }
  .btn-card-unlink {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0284c7;
    font-size: 0.76rem;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-card-unlink:hover {
    background: #f8fafc;
  }
  .btn-card-notify {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #16a34a;
    font-size: 0.76rem;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-card-notify:hover {
    background: #dcfce7;
  }

  /* ══════════════════════════════════════════════════════════════
     MODALES
     ══════════════════════════════════════════════════════════════ */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 16px;
  }
  .modal-box {
    background: #ffffff;
    border-radius: 14px;
    width: 100%;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  }

  .modal-identidad {
    max-width: 440px;
    padding: 34px 30px 28px;
    text-align: center;
  }
  .mi-lock-circle {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: #e0f2fe;
    color: #0284c7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.7rem;
    margin: 0 auto 16px;
  }
  .mi-title {
    font-size: 1.25rem;
    font-weight: 900;
    color: #0f172a;
    margin: 0 0 6px;
  }
  .mi-subtitle {
    font-size: 0.84rem;
    color: #64748b;
    margin: 0 0 20px;
    line-height: 1.4;
  }

  .pwd-wrapper {
    position: relative;
    margin-bottom: 16px;
  }
  .pwd-input {
    width: 100%;
    padding: 12px 42px 12px 14px;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.9rem;
    outline: none;
    box-sizing: border-box;
  }
  .pwd-input:focus {
    border-color: #0284c7;
  }
  .btn-eye-toggle {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1.05rem;
  }

  .btn-auth-submit {
    width: 100%;
    padding: 11px;
    background: #334155;
    color: #ffffff;
    border: none;
    border-radius: 7px;
    font-size: 0.86rem;
    font-weight: 800;
    cursor: pointer;
    margin-bottom: 8px;
  }
  .btn-auth-submit:hover:not(:disabled) {
    background: #1e293b;
  }
  .btn-auth-cancel {
    width: 100%;
    padding: 9px;
    background: #ffffff;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    font-size: 0.82rem;
    font-weight: 700;
    cursor: pointer;
  }

  /* MODAL PREFERENCIAS */
  .modal-prefs {
    max-width: 560px;
    overflow: hidden;
  }
  .mp-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid #f1f5f9;
  }
  .mp-head-title {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .mp-head-title i {
    font-size: 1.25rem;
  }
  .mp-head-title h4 {
    font-size: 1rem;
    font-weight: 900;
    color: #0f172a;
    margin: 0;
  }
  .mp-head-title span {
    font-size: 0.74rem;
    color: #64748b;
  }
  .btn-mp-close {
    background: none;
    border: none;
    font-size: 1.1rem;
    color: #94a3b8;
    cursor: pointer;
  }

  .mp-actions-bar {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 10px 20px;
    background: #f8fafc;
    border-bottom: 1px solid #f1f5f9;
  }
  .btn-mp-action {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0284c7;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 6px;
    cursor: pointer;
  }

  .mp-scroll-body {
    max-height: 400px;
    overflow-y: auto;
    padding: 14px 20px;
  }
  .mp-group {
    margin-bottom: 16px;
  }
  .mp-group-title {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f8fafc;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 800;
    color: #334155;
    margin-bottom: 8px;
  }
  .mp-group-title small {
    font-size: 0.7rem;
    color: #94a3b8;
    margin-left: auto;
  }
  .mp-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 6px;
    border-bottom: 1px solid #f8fafc;
  }
  .mpr-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .mpr-name {
    font-size: 0.84rem;
    font-weight: 800;
    color: #1e293b;
  }
  .mpr-desc {
    font-size: 0.74rem;
    color: #64748b;
  }

  .switch-sga {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 22px;
    flex-shrink: 0;
  }
  .switch-sga input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider-sga {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: #cbd5e1;
    transition: 0.2s;
    border-radius: 22px;
  }
  .slider-sga:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
  }
  input:checked + .slider-sga {
    background-color: #16a34a;
  }
  input:checked + .slider-sga:before {
    transform: translateX(18px);
  }

  .mp-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: #f8fafc;
    border-top: 1px solid #f1f5f9;
  }
  .mp-total-txt {
    font-size: 0.72rem;
    font-weight: 700;
    color: #64748b;
  }
  .mp-foot-btns {
    display: flex;
    gap: 8px;
  }
  .btn-mp-save {
    background: #16a34a;
    color: #ffffff;
    border: none;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.76rem;
    font-weight: 800;
    cursor: pointer;
  }
  .btn-mp-cancel {
    background: #0284c7;
    color: #ffffff;
    border: none;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.76rem;
    font-weight: 800;
    cursor: pointer;
  }

  /* MODAL AYUDA */
  .modal-ayuda {
    max-width: 460px;
    padding: 28px 24px 22px;
    text-align: center;
  }
  .may-icon {
    font-size: 2.2rem;
    color: #f59e0b;
    margin-bottom: 12px;
  }
  .may-title {
    font-size: 1.15rem;
    font-weight: 900;
    color: #1e293b;
    margin: 0 0 8px;
  }
  .may-desc {
    font-size: 0.82rem;
    color: #64748b;
    margin: 0 0 16px;
    line-height: 1.4;
  }
  .may-steps {
    text-align: left;
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
    background: #f8fafc;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }
  .may-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .ms-num {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #0284c7;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 800;
    flex-shrink: 0;
  }
  .ms-txt {
    font-size: 0.8rem;
    color: #334155;
    line-height: 1.35;
  }
</style>
