<script>
  import '../app.css';
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { get } from 'svelte/store';
  import { user, checkAuth, logout, capaNBIActiva } from '$lib/stores';
  import Toasts from '$lib/Toasts.svelte';

  let { children } = $props();

  const PUBLIC = ['/'];
  let authChecked = $state(false);
  let capasAbiertas = $state(false);

  // Dropdown & Modal states
  let showPeriodModal = $state(false);
  let showProfileDropdown = $state(false);
  let searchPeriod = $state('');
  
  let periodosList = $state([
    { id: 1, codigo: 'REGULAR - 2026-2027 PPA', activo: true },
    { id: 2, codigo: 'REGULAR - 2025-2026 SPA', activo: false },
    { id: 3, codigo: 'REGULAR - 2025-2026 PPA', activo: false },
    { id: 4, codigo: 'REGULAR - 2024-2025 - SPA', activo: false },
    { id: 5, codigo: 'REGULAR - 2024-2025 - PPA', activo: false },
    { id: 6, codigo: 'REGULAR - 2023-2024 - SPA', activo: false },
    { id: 7, codigo: 'REGULAR - 2023-2024 - PPA', activo: false },
  ]);

  let selectedPeriodCode = $state('REGULAR - 2026-2027 PPA');

  // Live Clock for Footer
  let currentTime = $state('');
  let clockInterval;

  function updateClock() {
    const now = new Date();
    currentTime = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  }

  onMount(async () => {
    await checkAuth();
    authChecked = true;
    const path = get(page).url.pathname;
    if (!$user && !PUBLIC.includes(path)) goto('/');

    updateClock();
    clockInterval = setInterval(updateClock, 1000);
  });

  onDestroy(() => {
    if (clockInterval) clearInterval(clockInterval);
  });

  async function handleLogout() {
    showProfileDropdown = false;
    await logout();
    goto('/');
  }

  function selectPeriod(p) {
    selectedPeriodCode = p.codigo;
    periodosList = periodosList.map(item => ({ ...item, activo: item.id === p.id }));
    showPeriodModal = false;
  }

  function togglePeriodModal(e) {
    e.stopPropagation();
    showPeriodModal = !showPeriodModal;
    showProfileDropdown = false;
  }

  function toggleProfileDropdown(e) {
    e.stopPropagation();
    showProfileDropdown = !showProfileDropdown;
    showPeriodModal = false;
  }

  function closeAllDropdowns() {
    showPeriodModal = false;
    showProfileDropdown = false;
  }

  let filteredPeriods = $derived(
    periodosList.filter(p => p.codigo.toLowerCase().includes(searchPeriod.toLowerCase()))
  );

  const ESTADOS = [
    { val:'EN_EJECUCION', label:'En ejecución', color:'#1b7505' },
    { val:'PROPUESTO',    label:'Propuesto',    color:'#dba112' },
    { val:'APROBADO',     label:'Aprobado',     color:'#0d6efd' },
    { val:'EN_CIERRE',    label:'En cierre',    color:'#fd7e14' },
    { val:'DETENIDO',     label:'Detenido',     color:'#dc3545' },
    { val:'FINALIZADO',   label:'Finalizado',   color:'#a8a8a7' },
    { val:'RECHAZADO',    label:'Rechazado',    color:'#6c757d' },
  ];

  const SIDEBAR_LINKS = {
    dashboard: { modulo: 'Dashboard',             links: [] },
    mapa:      { modulo: 'Mapa',                  links: [
                   { href: '/mapa', icon: 'bi-map', label: 'Ver mapa interactivo' },
                 ]},
    proyectos: { modulo: 'Proyectos',             links: [{ href: '/proyectos', icon: 'bi-list-ul', label: 'Lista de proyectos'  }] },
    entidades: { modulo: 'Entidades',             links: [{ href: '/entidades', icon: 'bi-list-ul', label: 'Lista de entidades'  }] },
    convenios: { modulo: 'Convenios',             links: [{ href: '/convenios', icon: 'bi-list-ul', label: 'Lista de convenios'  }] },
    periodos:  { modulo: 'Períodos',              links: [{ href: '/periodos',  icon: 'bi-list-ul', label: 'Lista de períodos'   }] },
    facultades:{ modulo: 'Facultades y Carreras', links: [
                   { href: '/facultades', icon: 'bi-bank', label: 'Facultades' },
                   { href: '/carreras',   icon: 'bi-book', label: 'Carreras'   },
                 ]},
    reportes:  { modulo: 'Reportes',             links: [{ href: '/reportes',  icon: 'bi-graph-up', label: 'Estadísticas' }] },
    configuracion: { modulo: 'Configuración',    links: [
                   { href: '/periodos',             icon: 'bi-calendar3',      label: 'Períodos académicos' },
                   { href: '/configuracion/capas',  icon: 'bi-layers-half',    label: 'Capas del mapa'     },
                 ]},
  };

  function getKey(pathname) {
    if (pathname.startsWith('/mapa'))          return 'mapa';
    if (pathname.startsWith('/proyectos'))     return 'proyectos';
    if (pathname.startsWith('/entidades'))     return 'entidades';
    if (pathname.startsWith('/convenios'))     return 'convenios';
    if (pathname.startsWith('/configuracion')) return 'configuracion';
    if (pathname.startsWith('/periodos'))      return 'configuracion';
    if (pathname.startsWith('/facultades') || pathname.startsWith('/carreras')) return 'facultades';
    if (pathname.startsWith('/reportes'))      return 'reportes';
    return 'dashboard';
  }

  let moduloKey   = $derived(getKey($page.url.pathname));
  let moduloData  = $derived(SIDEBAR_LINKS[moduloKey]);
  let isDashboard = $derived($page.url.pathname === '/dashboard');
  let isMapa      = $derived($page.url.pathname.startsWith('/mapa'));
</script>

<svelte:window onclick={closeAllDropdowns} />

<Toasts />

{#if PUBLIC.includes($page.url.pathname)}
  {#if authChecked}
    {@render children()}
  {/if}
{:else if !$user}
  {#if authChecked}
    {@render children()}
  {:else}
    <div class="checking">
      <i class="bi bi-arrow-repeat spin"></i> Verificando sesión...
    </div>
  {/if}
{:else}
  <div class="app-shell">

    <!-- NAVBAR (HEADER SUPERIOR ESTILO SGA UTEQ) -->
    <header class="sga-navbar">
      <div class="navbar-left">
        <a href="/dashboard" class="nav-brand" title="Ir al inicio">
          <span class="nav-brand-main">SGV</span>
          <span class="nav-brand-sep">|</span>
          <span class="nav-brand-sub">Sistema de Gestión de Vinculación</span>
        </a>
      </div>

      <div class="navbar-right">
        <!-- Notificaciones -->
        <button class="icon-btn" title="Notificaciones" onclick={(e) => e.stopPropagation()}>
          <i class="bi bi-bell-fill"></i>
          <span class="badge-dot">1</span>
        </button>

        <!-- Selector de Período Académico (Botón) -->
        <div class="period-btn-wrap">
          <button class="period-btn" onclick={togglePeriodModal} title="Cambiar período académico">
            <i class="bi bi-calendar-event"></i>
            <span class="period-text">{selectedPeriodCode}</span>
            <i class="bi bi-chevron-down caret-icon"></i>
          </button>

          <!-- MODAL / DROPDOWN DE PERÍODO ACADÉMICO (Exacto a SGA UTEQ) -->
          {#if showPeriodModal}
            <div class="sga-period-modal" onclick={(e) => e.stopPropagation()}>
              <div class="period-modal-header">
                <div class="modal-title">
                  <i class="bi bi-calendar3 green-icon"></i>
                  <span>PERÍODO ACADÉMICO</span>
                </div>
                <button class="btn-close-modal" onclick={() => showPeriodModal = false}>
                  <i class="bi bi-x-lg"></i>
                </button>
              </div>

              <div class="period-search-box">
                <i class="bi bi-search search-icon"></i>
                <input 
                  type="text" 
                  placeholder="Buscar período..." 
                  bind:value={searchPeriod} 
                />
              </div>

              <div class="period-list-container">
                <div class="period-subtitle">• PERÍODOS DISPONIBLES</div>
                <div class="period-items-list">
                  {#each filteredPeriods as p}
                    <button 
                      class="period-item-row" 
                      class:selected-period={p.activo || p.codigo === selectedPeriodCode}
                      onclick={() => selectPeriod(p)}
                    >
                      <span class="radio-indicator">
                        {#if p.activo || p.codigo === selectedPeriodCode}
                          <i class="bi bi-check-lg check-active"></i>
                        {:else}
                          <span class="radio-circle"></span>
                        {/if}
                      </span>
                      <span class="period-item-label">{p.codigo}</span>
                    </button>
                  {/each}
                </div>
              </div>

              <div class="period-modal-footer">
                <i class="bi bi-info-circle info-icon"></i>
                <span>Selecciona un período para cambiar</span>
              </div>
            </div>
          {/if}
        </div>

        <!-- Selector de Usuario / Perfil (Botón) -->
        <div class="profile-menu-container">
          <button class="profile-btn" class:active={showProfileDropdown} onclick={toggleProfileDropdown} title="Menú de usuario">
            <div class="user-avatar-sm">
              <i class="bi bi-person-fill"></i>
            </div>
            <span class="profile-name">{$user?.username || 'SOFT-R'}</span>
            <i class="bi bi-chevron-down caret-icon"></i>
          </button>

          <!-- DROPDOWN DE PERFIL DE USUARIO (Exacto a SGA UTEQ) -->
          {#if showProfileDropdown}
            <div class="profile-dropdown show" onclick={(e) => e.stopPropagation()}>
              <!-- User Info Card Header -->
              <div class="profile-dropdown-header">
                <div class="profile-avatar-lg">
                  <i class="bi bi-person-circle"></i>
                </div>
                <div class="profile-dropdown-info">
                  <div class="profile-full-name">{$user?.nombre || 'Castro Lopez Pedro Leonardo'}</div>
                  <div class="profile-email">{$user?.email || 'pcastrol@uteq.edu.ec'}</div>
                </div>
              </div>

              <!-- Roles / Profiles Available -->
              <div class="profile-roles-section">
                <div class="profile-section-label">• PERFILES DISPONIBLES</div>
                <div class="profile-role-item active-role">
                  <i class="bi bi-check-lg check-role"></i>
                  <span>{$user?.rol || 'SOFT-R'}</span>
                </div>
              </div>

              <div class="profile-divider"></div>

              <!-- Menu Options -->
              <div class="profile-menu-items">
                <a href="/configuracion" class="pmenu-item" onclick={() => showProfileDropdown = false}>
                  <i class="bi bi-person"></i>
                  <span>Mi perfil</span>
                </a>
                <a href="/configuracion" class="pmenu-item" onclick={() => showProfileDropdown = false}>
                  <i class="bi bi-display"></i>
                  <span>Mis dispositivos</span>
                </a>
                <a href="/configuracion" class="pmenu-item" onclick={() => showProfileDropdown = false}>
                  <i class="bi bi-image"></i>
                  <span>Cambio de foto</span>
                </a>
                <a href="/configuracion" class="pmenu-item" onclick={() => showProfileDropdown = false}>
                  <i class="bi bi-lock"></i>
                  <span>Cambio de clave</span>
                </a>
                <a href="/configuracion" class="pmenu-item" onclick={() => showProfileDropdown = false}>
                  <i class="bi bi-envelope"></i>
                  <span>Gestión de correos</span>
                  <span class="badge-nuevo">NUEVO</span>
                </a>
              </div>

              <div class="profile-divider"></div>

              <!-- Logout Button -->
              <div class="profile-menu-footer">
                <button class="pmenu-item btn-logout-red" onclick={handleLogout}>
                  <i class="bi bi-box-arrow-left"></i>
                  <span>Cerrar sesión</span>
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </header>

    <!-- CUERPO DEL SISTEMA -->
    <div class="body-row" class:no-sidebar={isDashboard}>

      {#if !isDashboard}
      <!-- COLUMNA IZQUIERDA -->
      <div class="left-col">

        <!-- MENÚ MÓDULO -->
        <div class="float-card">
          <p class="fc-label">MÓDULO</p>

          {#each moduloData.links as link}
            <a
              href={link.href}
              class="fc-link"
              class:fc-active={$page.url.pathname === link.href || $page.url.pathname.startsWith(link.href + '/')}
            >
              <i class="bi {link.icon}"></i>
              <span>{link.label}</span>
            </a>
          {/each}

          <!-- Capas expandible: solo en mapa -->
          {#if isMapa}
            <button class="fc-capas-btn" onclick={() => capasAbiertas = !capasAbiertas}>
              <i class="bi bi-layers"></i>
              <span>Capas temáticas</span>
              <i class="bi bi-chevron-{capasAbiertas ? 'up' : 'down'} fc-caret"></i>
            </button>
            {#if capasAbiertas}
              <div class="fc-capas-panel">
                <label class="fc-check">
                  <input type="checkbox" checked disabled />
                  <span>Proyectos vinculación</span>
                </label>
                <label class="fc-check">
                  <input
                    type="checkbox"
                    checked={$capaNBIActiva}
                    onchange={(e) => capaNBIActiva.set(e.target.checked)}
                  />
                  <span>NBI por Sector (INEC 2022)</span>
                </label>
              </div>
            {/if}
          {/if}

          <div class="fc-divider"></div>

          <a href="/dashboard" class="fc-link fc-home">
            <i class="bi bi-house-door"></i>
            <span>Volver al inicio</span>
          </a>
        </div>

        <!-- ESTADOS: solo en mapa, debajo del menú -->
        {#if isMapa}
        <div class="estados-card">
          <p class="sc-label">ESTADOS</p>
          <div class="sc-pills">
            {#each ESTADOS as e}
              <span class="sc-pill" style="--c:{e.color}">
                <span class="sc-dot"></span>{e.label}
              </span>
            {/each}
          </div>
        </div>
        {/if}

      </div>
      {/if}

      <!-- CONTENIDO PRINCIPAL -->
      <main class="content">
        {@render children()}
      </main>

    </div>

    <!-- FOOTER INFERIOR FIJO (Estilo SGA UTEQ) -->
    <footer class="sga-fixed-footer">
      <div class="footer-left">Universidad Técnica Estatal De Quevedo</div>
      <div class="footer-center">© 2026 - Todos los derechos reservados</div>
      <div class="footer-right">{currentTime}</div>
    </footer>

  </div>
{/if}

<style>
/* ── GENERAL ── */
.app-shell { 
  display: flex; 
  flex-direction: column; 
  min-height: 100vh; 
  background: #f4f6f3; 
  padding-bottom: 28px; /* espacio para footer fijo */
}

.checking { 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  height: 100vh; 
  color: #888; 
  font-family: system-ui, -apple-system, sans-serif; 
  font-size: .9rem; 
  gap: 10px; 
}

/* ── NAVBAR SUPERIOR (SGA UTEQ) ── */
.sga-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1b7a2b; /* Verde institucional UTEQ */
  height: 48px;
  padding: 0 16px;
  position: sticky;
  top: 0;
  z-index: 500;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  color: #ffffff;
}

.navbar-left { display: flex; align-items: center; gap: 10px; }
.navbar-right { display: flex; align-items: center; gap: 12px; }

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ffffff;
  text-decoration: none;
  font-size: 1rem;
}

.nav-brand-main { font-weight: 800; }
.nav-brand-sep { opacity: 0.8; }
.nav-brand-sub { font-weight: 400; font-size: 0.9rem; }

.icon-btn {
  position: relative;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background 0.2s;
}

.icon-btn:hover { background: rgba(255, 255, 255, 0.25); }

.badge-dot {
  position: absolute;
  top: 1px;
  right: 1px;
  background: #e67e22;
  color: #ffffff;
  font-size: 0.55rem;
  font-weight: 800;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #1b7a2b;
}

/* ── PERÍODO BUTTON & DROPDOWN ── */
.period-btn-wrap { position: relative; }

.period-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 6px;
  padding: 4px 10px;
  color: #ffffff;
  font-size: 0.78rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.period-btn:hover { background: rgba(255, 255, 255, 0.25); }
.caret-icon { font-size: 0.65rem; opacity: 0.8; }

/* MODAL DE PERÍODO (SGA UTEQ) */
.sga-period-modal {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 320px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(26, 117, 4, 0.15), 0 0 0 1px rgba(26, 117, 4, 0.08);
  padding: 16px;
  z-index: 1000;
  color: #333333;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.period-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #1a7504;
  letter-spacing: 0.3px;
}

.green-icon { color: #1a7504; font-size: 1.1rem; }

.btn-close-modal {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-close-modal:hover { background: #f0f0f0; color: #333; }

.period-search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: #999;
  font-size: 0.85rem;
}

.period-search-box input {
  width: 100%;
  padding: 7px 10px 7px 32px;
  font-size: 0.82rem;
  border: 1.5px solid #007bff;
  border-radius: 8px;
  outline: none;
  box-sizing: border-box;
}

.period-subtitle {
  font-size: 0.68rem;
  font-weight: 700;
  color: #888888;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.period-items-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 220px;
  overflow-y: auto;
}

.period-item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font-size: 0.78rem;
  color: #444444;
  transition: background 0.15s;
}

.period-item-row:hover { background: #f4f6f8; }

.selected-period {
  background: #f0f9f4 !important;
  color: #1a7504 !important;
  font-weight: 700 !important;
}

.radio-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
}

.check-active { color: #1a7504; font-weight: bold; font-size: 1rem; }

.radio-circle {
  width: 12px;
  height: 12px;
  border: 1.5px solid #ccc;
  border-radius: 50%;
}

.period-modal-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  color: #777777;
  padding-top: 8px;
  border-top: 1px solid #eeeeee;
}

/* ── PROFILE MENU & DROPDOWN ── */
.profile-menu-container { position: relative; }

.profile-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  padding: 3px 10px 3px 4px;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.profile-btn:hover, .profile-btn.active { background: rgba(255, 255, 255, 0.25); }

.user-avatar-sm {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #ffffff;
  color: #1b7a2b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
}

.profile-name {
  font-size: 0.8rem;
  font-weight: 700;
}

/* DROPDOWN DE PERFIL (CSS exacto del SGA) */
.profile-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 310px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(26, 117, 4, 0.15), 0 0 0 1px rgba(26, 117, 4, 0.08);
  padding: 16px;
  z-index: 1000;
  color: #333333;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 8px;
}

.profile-avatar-lg {
  font-size: 2.2rem;
  color: #1b7a2b;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-dropdown-info { display: flex; flex-direction: column; }

.profile-full-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #111111;
  line-height: 1.25;
}

.profile-email {
  font-size: 0.72rem;
  color: #666666;
}

.profile-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #888888;
  letter-spacing: 0.5px;
  margin-top: 4px;
  margin-bottom: 4px;
}

.profile-role-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 700;
}

.active-role {
  background: #f0f9f4;
  color: #1a7504;
}

.check-role { font-size: 1rem; color: #1a7504; }

.profile-divider {
  height: 1px;
  background: #eeeeee;
  margin: 2px 0;
}

.profile-menu-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pmenu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  font-size: 0.8rem;
  color: #444444;
  text-decoration: none;
  border-radius: 6px;
  transition: background 0.15s;
  background: none;
  border: none;
  width: 100%;
  cursor: pointer;
  text-align: left;
}

.pmenu-item:hover { background: #f4f6f8; color: #1a7504; }

.badge-nuevo {
  margin-left: auto;
  background: #28a745;
  color: #ffffff;
  font-size: 0.55rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 10px;
}

.btn-logout-red {
  color: #c13e3e !important;
  font-weight: 700;
}

.btn-logout-red:hover {
  background: #fde8e8 !important;
}

/* ── CUERPO ── */
.body-row {
  display: grid;
  grid-template: "sub sub" auto
                 "side main" 1fr / 252px 1fr;
  flex: 1;
  min-height: 0;
}

.body-row.no-sidebar {
  grid-template: "sub" auto
                 "main" 1fr / 1fr;
}

.content { display: contents; }
:global(.content > .subbar) { grid-area: sub; }
:global(.content > :not(.subbar)) { grid-area: main; min-width: 0; }

/* ── COLUMNA IZQUIERDA ── */
.left-col {
  grid-area: side;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 58px;
  align-self: flex-start;
  padding: 14px 12px 14px 16px;
}

/* ── ESTADOS CARD ── */
.estados-card {
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 3px 14px rgba(0,0,0,.08), 0 1px 3px rgba(0,0,0,.05);
  border: 1px solid #ebebeb;
  padding: 12px 14px 10px;
}

.sc-label {
  font-size: .58rem;
  font-weight: 800;
  color: #bbb;
  text-transform: uppercase;
  letter-spacing: .1em;
  margin: 0 0 8px;
}

.sc-pills { display: flex; flex-direction: column; gap: 5px; }

.sc-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: .74rem;
  font-weight: 700;
  color: #444;
  border-radius: 20px;
  padding: 3px 10px 3px 7px;
  width: fit-content;
  border: 1px solid color-mix(in srgb,var(--c) 35%,#e0e0e0);
  background: color-mix(in srgb,var(--c) 10%,#fff);
}

.sc-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--c); flex-shrink: 0; }

/* ── MENÚ MÓDULO (float-card) ── */
.float-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,.10), 0 1px 4px rgba(0,0,0,.06);
  border: 1px solid #ebebeb;
  padding: 14px 0 10px;
}

.fc-label {
  font-size: .6rem;
  font-weight: 800;
  color: #bbb;
  text-transform: uppercase;
  letter-spacing: .1em;
  padding: 0 18px 8px;
  margin: 0;
}

.fc-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 18px;
  font-size: .85rem;
  font-weight: 600;
  color: #3a3a5c;
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: background .14s, color .14s, border-color .14s;
}

.fc-link i { font-size: .95rem; color: #9999bb; flex-shrink: 0; transition: color .14s; }
.fc-link:hover { background: var(--verde-claro); color: var(--verde); border-left-color: var(--verde); }
.fc-link:hover i { color: var(--verde); }
.fc-active { background: var(--verde-claro); color: var(--verde); border-left-color: var(--verde); font-weight: 700; }
.fc-active i { color: var(--verde); }

/* Capas expandible */
.fc-capas-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 9px 18px;
  font-size: .85rem;
  font-weight: 600;
  color: #3a3a5c;
  background: none;
  border: none;
  border-left: 3px solid transparent;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: background .14s, color .14s, border-color .14s;
}

.fc-capas-btn i:first-child { font-size: .95rem; color: #9999bb; flex-shrink: 0; }
.fc-capas-btn span { flex: 1; }
.fc-caret { font-size: .65rem; color: #bbb; }
.fc-capas-btn:hover { background: var(--verde-claro); color: var(--verde); border-left-color: var(--verde); }
.fc-capas-btn:hover i { color: var(--verde); }

.fc-capas-panel {
  background: #f9fafb;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  padding: 10px 18px 10px 22px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fc-check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: .78rem;
  color: #555;
  font-weight: 600;
  cursor: pointer;
}

.fc-check input { accent-color: var(--verde); }

.fc-divider { height: 1px; background: #f0f0f0; margin: 8px 16px; }
.fc-home { color: #444 !important; font-weight: 600 !important; }
.fc-home i { color: #aaa !important; }
.fc-home:hover { background: #f5faf0 !important; color: var(--verde) !important; border-left-color: var(--verde) !important; }
.fc-home:hover i { color: var(--verde) !important; }

/* ── FOOTER FIJO (ESTILO SGA UTEQ) ── */
.sga-fixed-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 28px;
  background: #1b7a2b; /* Verde institucional UTEQ */
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 500;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
}

.footer-left, .footer-center, .footer-right {
  display: flex;
  align-items: center;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }
</style>
