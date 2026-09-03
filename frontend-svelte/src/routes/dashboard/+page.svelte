<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { notificaciones, cargarNotificaciones, marcarLeida } from '$lib/notifications';

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
      desc: 'Dispositivos, usuarios, períodos y auditoría', 
      key: null, 
      color: '#475569', 
      bg: '#f1f5f9',
      disabled: false 
    },
  ];

  let filtered = $derived(
    buscar.trim()
      ? modulos.filter(m => m.label.toLowerCase().includes(buscar.toLowerCase()))
      : modulos
  );

  onMount(async () => {
    try {
      await Promise.all([
        fetchAPI('/api/dashboard/stats/').then(res => stats = res),
        cargarNotificaciones()
      ]);
    } catch {}
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

  <!-- PANEL IZQUIERDO: DEPARTAMENTO DE VINCULACIÓN Y AVISOS -->
  <aside class="info-panel">
    
    <!-- CARD INSTITUCIONAL COMPACTA CON LOGO ORIGINAL UTEQ -->
    <div class="info-card inst-card">
      <div class="info-img-wrap">
        <img src="/logo-uteq.png" alt="Logo UTEQ" class="info-logo" />
      </div>
      <div class="info-text">
        <h3>Departamento de Vinculación</h3>
        <div class="info-sep"></div>
        <p>Sistema de Gestión de Proyectos</p>
      </div>
    </div>

    <!-- CARD DINÁMICA DE AVISOS Y ALERTAS -->
    <div class="info-card notice-panel">
      <div class="notice-head">
        <div class="nh-title">
          <i class="bi bi-megaphone-fill"></i>
          <span>Avisos del Sistema</span>
        </div>
        {#if $notificaciones.length > 0}
          <span class="nh-badge">{$notificaciones.length}</span>
        {/if}
      </div>

      <div class="notice-body-list">
        {#if $notificaciones.length === 0}
          <div class="notice-empty">
            <i class="bi bi-check-circle text-green"></i>
            <span>No hay avisos pendientes en este momento.</span>
          </div>
        {:else}
          {#each $notificaciones.slice(0, 5) as n}
            <a
              href={n.link}
              class="notice-item {n.prioridad}"
              onclick={() => marcarLeida(n.id)}
            >
              <div class="ni-icon">
                <i class="bi {n.icono}"></i>
              </div>
              <div class="ni-content">
                <span class="ni-title">{n.titulo}</span>
                <span class="ni-desc">{n.mensaje}</span>
              </div>
              <i class="bi bi-chevron-right ni-arrow"></i>
            </a>
          {/each}
        {/if}
      </div>
    </div>
  </aside>

  <!-- SECCIÓN DE CARDS DE MÓDULOS -->
  <section class="modulos-wrap">
    <div class="modulos-grid">
      {#each filtered as m}
        {#if m.disabled}
          <div class="mod-card disabled">
            <span class="mod-star"><i class="bi bi-star-fill"></i></span>
            <div class="mod-icon-container" style="background-color: {m.bg}; color: {m.color};">
              <i class="bi {m.bi}"></i>
            </div>
            <div class="mod-title">{m.label}</div>
            <div class="mod-desc">{m.desc}</div>
          </div>
        {:else}
          <a href={m.href} class="mod-card">
            <span class="mod-star"><i class="bi bi-star-fill"></i></span>
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
  padding: 20px 24px;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
}

/* ── PANEL IZQUIERDO ── */
.info-panel {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
@media (max-width: 900px) { .info-panel { display: none; } }

.info-card {
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.inst-card {
  padding: 12px 14px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.info-img-wrap {
  padding: 8px 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.info-logo {
  max-width: 130px;
  height: auto;
  object-fit: contain;
}
.info-text {
  padding: 4px 6px 0;
  text-align: center;
}
.info-text h3 {
  font-size: 0.84rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 6px 0;
  line-height: 1.25;
}
.info-sep {
  width: 32px;
  height: 3px;
  background: #d97706;
  border-radius: 2px;
  margin: 0 auto 6px;
}
.info-text p {
  font-size: 0.72rem;
  font-weight: 700;
  color: #d97706;
  margin: 0;
}

/* ── CARD DE AVISOS ── */
.notice-panel {
  display: flex;
  flex-direction: column;
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.nh-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  font-weight: 800;
  color: #1e293b;
}
.nh-title i { color: #d97706; font-size: 0.85rem; }

.nh-badge {
  background: #fee2e2;
  color: #dc2626;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

.notice-body-list {
  display: flex;
  flex-direction: column;
  max-height: 340px;
  overflow-y: auto;
}

.notice-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 18px 14px;
  font-size: 0.75rem;
  color: #64748b;
}
.text-green { color: #16a34a; }

.notice-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  text-decoration: none;
  transition: background 0.15s ease;
}
.notice-item:last-child { border-bottom: none; }
.notice-item:hover { background: #f8fafc; }

.ni-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  flex-shrink: 0;
}
.notice-item.danger .ni-icon { background: #fee2e2; color: #dc2626; }
.notice-item.warning .ni-icon { background: #fef3c7; color: #d97706; }
.notice-item.info .ni-icon { background: #e0f2fe; color: #0284c7; }
.notice-item.success .ni-icon { background: #dcfce7; color: #15803d; }

.ni-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.ni-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ni-desc {
  font-size: 0.68rem;
  color: #64748b;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ni-arrow {
  font-size: 0.7rem;
  color: #cbd5e1;
  align-self: center;
}

/* ── WRAPPER DE MÓDULOS ── */
.modulos-wrap {
  flex: 1;
}

.modulos-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.mod-card {
  position: relative;
  width: 178px;
  height: 200px;
  background: #ffffff;
  border-radius: 12px;
  padding: 18px 14px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  text-decoration: none;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  box-sizing: border-box;
}

.mod-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  border-color: #cbd5e1;
}

.mod-card.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.mod-star {
  position: absolute;
  top: 10px;
  left: 12px;
  font-size: 0.82rem;
  color: #f59e0b;
  opacity: 0.9;
}

.mod-icon-container {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.7rem;
  margin-bottom: 12px;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.mod-card:hover .mod-icon-container {
  transform: scale(1.08);
}

.mod-title {
  font-size: 0.88rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 4px;
  line-height: 1.2;
}

.mod-desc {
  font-size: 0.68rem;
  color: #64748b;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
