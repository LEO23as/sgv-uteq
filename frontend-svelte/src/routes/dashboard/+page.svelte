<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';

  let stats      = $state(null);
  let cargando   = $state(true);
  let buscar     = $state('');

  const modulos = [
    { href: '/mapa',       icon: '/icons/mapa.png',       label: 'Mapa',       desc: 'Proyectos georreferenciados',  key: null,        disabled: false },
    { href: '/proyectos',  icon: '/icons/proyectos.png',  label: 'Proyectos',  desc: 'Gestión de proyectos',         key: 'proyectos', disabled: false },
    { href: '/entidades',  icon: '/icons/entidades.png',  label: 'Entidades',  desc: 'Organizaciones aliadas',       key: 'entidades', disabled: false },
    { href: '/convenios',  icon: '/icons/convenios.png',  label: 'Convenios',  desc: 'Acuerdos institucionales',     key: 'convenios', disabled: false },
    { href: '/facultades', icon: '/icons/facultades.png', label: 'Facultades', desc: 'Unidades académicas',          key: 'facultades',disabled: false },
    { href: '/reportes',      icon: '/icons/reportes.png',   label: 'Reportes',      desc: 'Estadísticas y gráficas',      key: null,        disabled: false },
    { href: '/configuracion', icon: '/icons/periodos.png',   label: 'Configuración', desc: 'Períodos, capas y ajustes',    key: null,        disabled: false, bi: 'bi-gear-fill' },
    { href: null,             icon: '/icons/docentes.png',   label: 'Docentes',      desc: 'Próximamente',                 key: null,        disabled: true  },
    { href: null,             icon: '/icons/usuarios.png',   label: 'Usuarios',      desc: 'Gestión de accesos',           key: null,        disabled: true  },
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
    <input bind:value={buscar} placeholder="Buscar..." />
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

  <!-- SECCIÓN DE CARDS DE MÓDULOS (ESTILO EXACTO SGA UTEQ) -->
  <section class="modulos-wrap">
    <div class="modulos-grid">
      {#each filtered as m}
        {#if m.disabled}
          <div class="mod-card disabled">
            <div class="mod-card-top">
              <i class="bi bi-star mod-star"></i>
            </div>
            <div class="mod-icon-wrap">
              {#if m.bi}
                <i class="bi {m.bi} mod-bi"></i>
              {:else}
                <img src={m.icon} alt={m.label} class="mod-img" />
              {/if}
            </div>
            <div class="mod-card-bottom">
              <div class="mod-name">{m.label}</div>
              <div class="mod-desc">{m.desc}</div>
            </div>
          </div>
        {:else}
          <a href={m.href} class="mod-card">
            <div class="mod-card-top">
              <i class="bi bi-star-fill mod-star"></i>
              {#if !cargando && stats && m.key && stats[m.key] !== undefined}
                <span class="mod-badge">{stats[m.key]}</span>
              {/if}
            </div>
            <div class="mod-icon-wrap">
              {#if m.bi}
                <i class="bi {m.bi} mod-bi"></i>
              {:else}
                <img src={m.icon} alt={m.label} class="mod-img" />
              {/if}
            </div>
            <div class="mod-card-bottom">
              <div class="mod-name">{m.label}</div>
              <div class="mod-desc">{m.desc}</div>
            </div>
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
  border-bottom: 1px solid #e0e0e0;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
}

.breadcrumb a {
  color: #0056b3;
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.breadcrumb .sep {
  color: #999999;
}

.breadcrumb .current {
  color: #1b7a2b;
  font-weight: 700;
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #ced4da;
  border-radius: 18px;
  padding: 0 14px;
  width: 220px;
  transition: border-color 0.2s;
}
.search-wrap:focus-within { border-color: #1b7a2b; }
.search-wrap i { color: #888888; font-size: 0.85rem; }
.search-wrap input {
  border: none; 
  outline: none;
  padding: 6px 0;
  font-size: 0.82rem;
  font-family: inherit;
  background: transparent;
  width: 100%;
}

/* ── BODY ── */
.dash-body {
  display: flex;
  align-items: flex-start;
  padding: 20px 24px;
  gap: 20px;
}

/* ── PANEL IZQUIERDO ── */
.info-panel {
  width: 230px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
@media (max-width: 900px) { .info-panel { display: none; } }

.info-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e3e3e3;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.info-img-wrap {
  background: #1b7a2b;
  padding: 24px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.info-logo {
  width: 130px;
  filter: brightness(0) invert(1);
}
.info-text {
  padding: 14px 14px 18px;
  text-align: center;
}
.info-text h3 {
  font-size: 0.88rem;
  font-weight: 800;
  color: #222222;
  margin-bottom: 8px;
}
.info-sep {
  width: 36px;
  height: 3px;
  background: #d4a017;
  border-radius: 2px;
  margin: 0 auto 8px;
}
.info-text p {
  font-size: 0.76rem;
  color: #d4a017;
  font-weight: 700;
  margin: 0;
}

.notice {
  display: flex;
  flex-direction: column;
  padding: 14px;
  gap: 8px;
}
.notice-icon {
  width: 34px; 
  height: 34px;
  background: #eaf5ea;
  border-radius: 8px;
  display: flex; 
  align-items: center; 
  justify-content: center;
  color: #1b7a2b;
  font-size: 1rem;
}
.notice-body strong {
  font-size: 0.82rem;
  font-weight: 800;
  color: #222222;
  display: block;
  margin-bottom: 2px;
}
.notice-body p {
  font-size: 0.73rem;
  color: #777777;
  margin: 0;
}

/* ── CARDS MÓDULOS (ESTILO EXACTO SGA UTEQ) ── */
.modulos-wrap { flex: 1; min-width: 0; }

.modulos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
  gap: 16px;
}

.mod-card {
  background: #ffffff;
  border: 1px solid #e3e3e3;
  border-radius: 10px;
  padding: 10px 10px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  text-align: center;
  text-decoration: none;
  position: relative;
  transition: background 0.18s, border-color 0.18s, box-shadow 0.18s;
  height: 200px;
  box-sizing: border-box;
}

.mod-card:hover {
  background: #ebf3fb; /* Resalte azul-grisáceo suave estilo SGA */
  border-color: #b8d4f2;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.mod-card.disabled { 
  opacity: 0.5; 
  cursor: not-allowed; 
  pointer-events: none; 
}

.mod-card-top {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 18px;
}

.mod-star {
  color: #f39c12;
  font-size: 0.75rem;
}

.mod-card.disabled .mod-star {
  color: #d0d0d0;
}

.mod-badge {
  background: #1b7a2b;
  color: #ffffff;
  font-size: 0.62rem;
  font-weight: 800;
  padding: 1px 7px;
  border-radius: 12px;
  line-height: 1.3;
}

/* Contenedor ícono */
.mod-icon-wrap {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin: 4px 0;
}

.mod-img {
  width: 78px;
  height: 78px;
  object-fit: contain;
}

.mod-bi {
  font-size: 64px;
  color: #1b7a2b;
  line-height: 1;
}

.mod-card-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.mod-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: #222222;
  line-height: 1.2;
}

.mod-card:hover .mod-name { 
  color: #0056b3; 
}

.mod-desc { 
  font-size: 0.7rem; 
  color: #888888; 
  font-weight: 400; 
  line-height: 1.2; 
}
</style>
