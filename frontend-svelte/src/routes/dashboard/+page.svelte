<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

  let stats      = $state(null);
  let cargando   = $state(true);
  let buscar     = $state('');

  const modulos = [
    { 
      href: '/mapa', 
      bi: 'bi-geo-alt', 
      label: 'Mapa', 
      desc: 'Proyectos georreferenciados', 
      key: null, 
      color: '#0284c7', 
      bg: '#e0f2fe',
      disabled: false 
    },
    { 
      href: '/proyectos', 
      bi: 'bi-briefcase', 
      label: 'Proyectos', 
      desc: 'Gestión de proyectos', 
      key: 'proyectos', 
      color: '#7c3aed', 
      bg: '#f5f3ff',
      disabled: false 
    },
    { 
      href: '/entidades', 
      bi: 'bi-building', 
      label: 'Entidades', 
      desc: 'Organizaciones aliadas', 
      key: 'entidades', 
      color: '#d97706', 
      bg: '#fffbeb',
      disabled: false 
    },
    { 
      href: '/convenios', 
      bi: 'bi-award', 
      label: 'Convenios', 
      desc: 'Acuerdos institucionales', 
      key: 'convenios', 
      color: '#e11d48', 
      bg: '#fff1f2',
      disabled: false 
    },
    { 
      href: '/facultades', 
      bi: 'bi-mortarboard', 
      label: 'Facultades', 
      desc: 'Unidades académicas', 
      key: 'facultades', 
      color: '#16a34a', 
      bg: '#f0fdf4',
      disabled: false 
    },
    { 
      href: '/reportes', 
      bi: 'bi-bar-chart-line', 
      label: 'Reportes', 
      desc: 'Estadísticas y gráficos', 
      key: null, 
      color: '#0d9488', 
      bg: '#f0fdfa',
      disabled: false 
    },
    { 
      href: '/configuracion', 
      bi: 'bi-sliders', 
      label: 'Configuración', 
      desc: 'Períodos, capas y ajustes', 
      key: null, 
      color: '#475569', 
      bg: '#f1f5f9',
      disabled: false 
    },
    { 
      href: null, 
      bi: 'bi-person-badge', 
      label: 'Docentes', 
      desc: 'Próximamente', 
      key: null, 
      color: '#64748b', 
      bg: '#f8fafc',
      disabled: true 
    },
    { 
      href: null, 
      bi: 'bi-people', 
      label: 'Usuarios', 
      desc: 'Gestión de accesos', 
      key: null, 
      color: '#9333ea', 
      bg: '#faf5ff',
      disabled: true 
    },
  ];

  let filtered = $derived(
    buscar.trim()
      ? modulos.filter(m => m.label.toLowerCase().includes(buscar.toLowerCase()))
      : modulos
  );

  onMount(async () => {
    try { stats = await fetchAPI('/api/dashboard/stats/'); } catch {}
    cargando = false;
  });
</script>

<svelte:head><title>Dashboard — SGV UTEQ</title></svelte:head>

<!-- BARRA SECUNDARIA BREADCRUMB + BUSCADOR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Dashboard</span>
    <span class="sep">/</span>
  </nav>
  <div class="search-wrap">
    <i class="bi bi-search"></i>
    <input bind:value={buscar} placeholder="Buscar módulo..." />
  </div>
</div>

<!-- CUERPO PRINCIPAL DEL DASHBOARD -->
<div class="dash-body">

  <!-- PANEL IZQUIERDO: DEPARTAMENTO DE VINCULACIÓN -->
  <aside class="info-panel">
    <div class="info-card">
      <div class="info-img-wrap">
        <img src="/logo-uteq.png" alt="UTEQ" class="info-logo" />
      </div>
      <div class="info-text">
        <h3>Departamento de Vinculación</h3>
        <div class="info-sep"></div>
        <p>Sistema de Gestión de Proyectos</p>
      </div>
    </div>

    <div class="info-card notice">
      <div class="notice-icon"><i class="bi bi-megaphone-fill"></i></div>
      <div class="notice-body">
        <strong>Avisos</strong>
        <p>No hay avisos por el momento.</p>
      </div>
    </div>
  </aside>

  <!-- SECCIÓN DE CARDS DE MÓDULOS (DISEÑO MODERNO Y ELEGANTE) -->
  <section class="modulos-wrap">
    <div class="modulos-grid">
      {#each filtered as m}
        {#if m.disabled}
          <div class="mod-card disabled">
            <div class="mod-icon-container" style="background-color: {m.bg}; color: {m.color};">
              <i class="bi {m.bi}"></i>
            </div>
            <div class="mod-title">{m.label}</div>
            <div class="mod-desc">{m.desc}</div>
          </div>
        {:else}
          <a href={m.href} class="mod-card">
            {#if !cargando && stats && m.key && stats[m.key] !== undefined}
              <span class="mod-card-badge">{stats[m.key]}</span>
            {/if}
            <div class="mod-icon-container" style="background-color: {m.bg}; color: {m.color};">
              <i class="bi {m.bi}"></i>
            </div>
            <div class="mod-title">{m.label}</div>
            <div class="mod-desc">{m.desc}</div>
          </a>
        {/if}
      {/each}
    </div>
  </section>

</div>

<style>
/* ── SUBBAR ── */
.subbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 24px;
  background: #ffffff;
  border-bottom: 1px solid #eef2f6;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
}

.breadcrumb a {
  color: #0284c7;
  text-decoration: none;
  font-weight: 500;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.breadcrumb .sep {
  color: #94a3b8;
}

.breadcrumb .current {
  color: #1b7a2b;
  font-weight: 700;
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 0 14px;
  width: 240px;
  transition: all 0.2s;
}
.search-wrap:focus-within { 
  border-color: #1b7a2b; 
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.1);
}
.search-wrap i { color: #94a3b8; font-size: 0.85rem; }
.search-wrap input {
  border: none; 
  outline: none;
  padding: 7px 0;
  font-size: 0.82rem;
  font-family: inherit;
  background: transparent;
  width: 100%;
  color: #1e293b;
}

/* ── BODY ── */
.dash-body {
  display: flex;
  align-items: flex-start;
  padding: 24px 28px;
  gap: 24px;
}

/* ── PANEL IZQUIERDO ── */
.info-panel {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
@media (max-width: 900px) { .info-panel { display: none; } }

.info-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid #eef2f6;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
}

.info-img-wrap {
  background: #1b7a2b;
  padding: 26px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.info-logo {
  width: 135px;
  filter: brightness(0) invert(1);
}
.info-text {
  padding: 16px 16px 20px;
  text-align: center;
}
.info-text h3 {
  font-size: 0.9rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
}
.info-sep {
  width: 36px;
  height: 3px;
  background: #d97706;
  border-radius: 2px;
  margin: 0 auto 8px;
}
.info-text p {
  font-size: 0.76rem;
  color: #d97706;
  font-weight: 700;
  margin: 0;
}

.notice {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 10px;
}
.notice-icon {
  width: 36px; 
  height: 36px;
  background: #f0fdf4;
  border-radius: 10px;
  display: flex; 
  align-items: center; 
  justify-content: center;
  color: #1b7a2b;
  font-size: 1.05rem;
}
.notice-body strong {
  font-size: 0.85rem;
  font-weight: 800;
  color: #1e293b;
  display: block;
  margin-bottom: 2px;
}
.notice-body p {
  font-size: 0.74rem;
  color: #64748b;
  margin: 0;
}

/* ── CARDS MÓDULOS (ESTILO MODERNO ELEGANTE) ── */
.modulos-wrap { flex: 1; min-width: 0; }

.modulos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 18px;
}

.mod-card {
  background: #ffffff;
  border: 1px solid #eef2f6;
  border-radius: 20px;
  padding: 24px 14px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  text-decoration: none;
  position: relative;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 185px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02), 0 1px 2px rgba(0, 0, 0, 0.03);
  box-sizing: border-box;
}

.mod-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.06);
  border-color: #cbd5e1;
  background: #ffffff;
}

.mod-card.disabled { 
  opacity: 0.55; 
  cursor: not-allowed; 
  pointer-events: none; 
}

.mod-card-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: #1b7a2b;
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 20px;
  line-height: 1.2;
  box-shadow: 0 2px 6px rgba(27, 122, 43, 0.25);
}

/* Squircle Icon Container */
.mod-icon-container {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  transition: transform 0.2s ease;
}

.mod-card:hover .mod-icon-container {
  transform: scale(1.08);
}

.mod-icon-container i {
  font-size: 1.65rem;
  line-height: 1;
}

.mod-title {
  font-size: 0.94rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
  line-height: 1.25;
  transition: color 0.18s;
}

.mod-card:hover .mod-title { 
  color: #0f172a; 
}

.mod-desc { 
  font-size: 0.73rem; 
  color: #64748b; 
  font-weight: 400; 
  line-height: 1.25; 
}
</style>
