<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';

  let usuarios = $state([]);
  let roles = $state([]);
  let facultades = $state([]);
  let cargando = $state(true);
  let buscar = $state('');
  let filtroRol = $state('');

  // Modal de Crear / Editar
  let modalUsuario = $state(false);
  let modoEdicion = $state(false);
  let guardando = $state(false);

  // Formulario de Usuario (Automático)
  let form = $state({
    id_usuario: null,
    nombres: '',
    apellidos: '',
    correo: '',
    id_rol: '',
    id_facultad: '',
    activo: true,
  });

  // Filtrado reactivo
  let usuariosFiltrados = $derived(
    usuarios.filter(u => {
      const matchTexto = 
        u.username.toLowerCase().includes(buscar.toLowerCase()) ||
        u.nombres.toLowerCase().includes(buscar.toLowerCase()) ||
        (u.correo && u.correo.toLowerCase().includes(buscar.toLowerCase()));
      const matchRol = filtroRol ? String(u.id_rol) === String(filtroRol) : true;
      return matchTexto && matchRol;
    })
  );

  async function cargarDatos() {
    cargando = true;
    try {
      const [u, r, f] = await Promise.all([
        fetchAPI('/api/usuarios/'),
        fetchAPI('/api/roles/'),
        fetchAPI('/api/facultades/'),
      ]);
      usuarios = u;
      roles = r;
      facultades = f;
    } catch (e) {
      toast.error('Error al cargar usuarios');
    } finally {
      cargando = false;
    }
  }

  onMount(cargarDatos);

  function abrirNuevoUsuario() {
    modoEdicion = false;
    form = {
      id_usuario: null,
      nombres: '',
      apellidos: '',
      correo: '',
      id_rol: roles.find(r => r.nombre === 'TECNICO')?.id_rol || roles[0]?.id_rol,
      id_facultad: '',
      activo: true,
    };
    modalUsuario = true;
  }

  function abrirEditarUsuario(u) {
    modoEdicion = true;
    form = {
      id_usuario: u.id_usuario,
      nombres: u.nombres,
      apellidos: '',
      correo: u.correo || '',
      id_rol: u.id_rol,
      id_facultad: u.id_facultad || '',
      activo: u.activo,
    };
    modalUsuario = true;
  }

  async function guardarUsuario() {
    if (!form.nombres.trim()) {
      toast.error('Ingresa los nombres del usuario');
      return;
    }
    if (!modoEdicion && !form.apellidos.trim()) {
      toast.error('Ingresa los apellidos para generar el usuario');
      return;
    }
    if (!form.correo.trim()) {
      toast.error('Ingresa el correo electrónico para enviar las credenciales');
      return;
    }
    if (!form.id_rol) {
      toast.error('Selecciona un rol');
      return;
    }

    guardando = true;
    try {
      if (modoEdicion) {
        // Editar
        const res = await fetch(`/api/usuarios/${form.id_usuario}/editar/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nombres: form.nombres.trim(),
            correo: form.correo.trim(),
            id_rol: form.id_rol,
            id_facultad: form.id_facultad || null,
            activo: form.activo,
          }),
          credentials: 'include',
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al actualizar');
        toast.success('Usuario actualizado correctamente');
        modalUsuario = false;
        await cargarDatos();
      } else {
        // Crear automáticamente y enviar por correo
        const res = await fetch('/api/usuarios/crear/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nombres: form.nombres.trim(),
            apellidos: form.apellidos.trim(),
            correo: form.correo.trim(),
            id_rol: form.id_rol,
            id_facultad: form.id_facultad || null,
          }),
          credentials: 'include',
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al crear usuario');

        modalUsuario = false;
        toast.success(`Usuario "${data.username}" creado exitosamente. Se enviaron las credenciales a ${data.correo}.`);
        await cargarDatos();
      }
    } catch (e) {
      toast.error(e.message || 'Error al procesar la solicitud');
    } finally {
      guardando = false;
    }
  }

  async function resetPassword(u) {
    if (!confirm(`¿Deseas restablecer la contraseña del usuario "${u.username}" (${u.nombres})?`)) return;

    try {
      const res = await fetch(`/api/usuarios/${u.id_usuario}/reset-password/`, {
        method: 'POST',
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al restablecer contraseña');

      toast.success(`Contraseña restablecida. Se envió la nueva clave temporal al correo institucional.`);
    } catch (e) {
      toast.error(e.message || 'Error al restablecer contraseña');
    }
  }

  async function toggleActivo(u) {
    const accion = u.activo ? 'inactivar' : 'activar';
    if (!confirm(`¿Confirmas que deseas ${accion} al usuario "${u.username}"?`)) return;

    try {
      const res = await fetch(`/api/usuarios/${u.id_usuario}/toggle-activo/`, {
        method: 'POST',
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al cambiar estado');
      toast.success(data.mensaje);
      await cargarDatos();
    } catch (e) {
      toast.error(e.message || 'Error al cambiar estado');
    }
  }

  function getRolBadgeClass(rol) {
    if (!rol) return 'badge-neutral';
    const r = rol.toUpperCase();
    if (r.includes('ADMIN') || r.includes('DIRECTOR')) return 'badge-admin';
    if (r.includes('TECNICO') || r.includes('ASISTENTE')) return 'badge-tecnico';
    return 'badge-consulta';
  }

  function getRolFriendlyName(rol) {
    if (!rol) return 'Sin Rol';
    const r = rol.toUpperCase();
    if (r.includes('ADMIN') || r.includes('DIRECTOR')) return 'Director(a) / Administrador';
    if (r.includes('TECNICO') || r.includes('ASISTENTE')) return 'Asistente';
    if (r.includes('CONSULTA') || r.includes('SECRETARI')) return 'Secretaria / Secretario';
    return rol;
  }
</script>

<svelte:head><title>Gestión de Usuarios — SGV UTEQ</title></svelte:head>

<!-- BARRA SUBBAR -->
<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <span class="current">Gestión de Usuarios</span>
  </nav>

  <div class="subbar-actions">
    <button class="btn-nuevo" onclick={abrirNuevoUsuario}>
      <i class="bi bi-person-plus-fill"></i> Nuevo usuario
    </button>
  </div>
</div>

<!-- CUERPO PRINCIPAL -->
<div class="page-body">

  <!-- CARD CONTENEDORA -->
  <div class="main-card">
    
    <!-- HEADER Y FILTROS -->
    <div class="card-header-bar">
      <div class="header-titles">
        <div class="header-icon">
          <i class="bi bi-people-fill"></i>
        </div>
        <div>
          <h2>Usuarios del Sistema</h2>
          <p>Administración de cuentas institucionales y permisos de seguridad (Directores, Asistentes y Secretarías).</p>
        </div>
      </div>

      <div class="filters-wrap">
        <!-- BUSCADOR -->
        <div class="search-box">
          <i class="bi bi-search"></i>
          <input bind:value={buscar} placeholder="Buscar por nombre, usuario o correo..." />
          {#if buscar}
            <button class="btn-clear" onclick={() => { buscar = ''; }} title="Limpiar"><i class="bi bi-x"></i></button>
          {/if}
        </div>

        <!-- FILTRO POR ROL -->
        <div class="select-box">
          <select bind:value={filtroRol}>
            <option value="">Todos los roles</option>
            {#each roles as r}
              <option value={r.id_rol}>{r.nombre_amigable || getRolFriendlyName(r.nombre)}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <!-- TABLA ESTILO VERDE SGA -->
    {#if cargando}
      <div class="empty-state"><i class="bi bi-arrow-repeat spin"></i> Cargando usuarios...</div>
    {:else if !usuariosFiltrados.length}
      <div class="empty-state">
        <i class="bi bi-search" style="font-size: 2rem; margin-bottom: 8px; display: block;"></i>
        No se encontraron usuarios que coincidan con los criterios de búsqueda.
      </div>
    {:else}
      <div class="table-container">
        <table class="sga-table">
          <thead>
            <tr>
              <th>USUARIO</th>
              <th>NOMBRES Y APELLIDOS</th>
              <th>CORREO ELECTRÓNICO</th>
              <th>ROL / PERFIL</th>
              <th>ÚLTIMO ACCESO</th>
              <th>ESTADO</th>
              <th class="text-center">ACCIONES</th>
            </tr>
          </thead>
          <tbody>
            {#each usuariosFiltrados as u}
              <tr class={!u.activo ? 'row-inactiva' : ''}>
                <td>
                  <div class="user-cell">
                    <div class="avatar-circle">
                      {u.nombres ? u.nombres.charAt(0).toUpperCase() : u.username.charAt(0).toUpperCase()}
                    </div>
                    <span class="user-handle">{u.username}</span>
                  </div>
                </td>
                <td class="fw-bold text-dark">{u.nombres}</td>
                <td>
                  {#if u.correo}
                    <span class="email-text"><i class="bi bi-envelope-at text-muted"></i> {u.correo}</span>
                  {:else}
                    <span class="text-muted fst-italic">Sin correo asignado</span>
                  {/if}
                </td>
                <td>
                  <span class="rol-badge {getRolBadgeClass(u.rol)}">
                    {getRolFriendlyName(u.rol)}
                  </span>
                </td>
                <td class="text-muted small">
                  {u.ultimo_acceso || 'Nunca'}
                </td>
                <td>
                  {#if u.activo}
                    <span class="badge-activo"><i class="bi bi-check-circle-fill"></i> Activo</span>
                  {:else}
                    <span class="badge-inactivo"><i class="bi bi-dash-circle-fill"></i> Inactivo</span>
                  {/if}
                </td>
                <td class="text-center">
                  <div class="actions-wrap">
                    <button class="btn-tbl reset" onclick={() => resetPassword(u)} title="Restablecer contraseña y enviar por correo">
                      <i class="bi bi-key-fill"></i>
                    </button>
                    <button class="btn-tbl edit" onclick={() => abrirEditarUsuario(u)} title="Editar usuario">
                      <i class="bi bi-pencil-square"></i>
                    </button>
                    <button 
                      class="btn-tbl {u.activo ? 'toggle-off' : 'toggle-on'}" 
                      onclick={() => toggleActivo(u)} 
                      title={u.activo ? 'Inactivar acceso' : 'Reactivar acceso'}
                    >
                      <i class="bi {u.activo ? 'bi-person-slash' : 'bi-person-check'}"></i>
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

  </div>
</div>

<!-- MODAL: CREAR / EDITAR USUARIO -->
{#if modalUsuario}
  <div class="modal-backdrop" onclick={() => { modalUsuario = false; }}>
    <div class="sga-modal-window" onclick={(e) => e.stopPropagation()}>
      
      <!-- HEADER INSTITUCIONAL SGA -->
      <div class="sga-modal-header">
        <div class="sga-modal-title">
          <i class="bi {modoEdicion ? 'bi-pencil-square' : 'bi-person-plus-fill'} green-icon"></i>
          <span>{modoEdicion ? 'EDITAR USUARIO' : 'CREAR NUEVO USUARIO'}</span>
        </div>
        <button class="sga-modal-close" onclick={() => { modalUsuario = false; }}>
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="sga-modal-subtitle">
        • INGRESA LA INFORMACIÓN PARA GENERAR LA CUENTA Y ENVIAR CREDENCIALES AL CORREO
      </div>

      <!-- FORMULARIO LIMPIO -->
      <form onsubmit={(e) => { e.preventDefault(); guardarUsuario(); }} class="sga-modal-body">
        <div class="sga-form-grid">
          <div class="sga-fg">
            <label>NOMBRES *</label>
            <input type="text" bind:value={form.nombres} placeholder="Ej: Juan Carlos" required />
          </div>

          {#if !modoEdicion}
            <div class="sga-fg">
              <label>APELLIDOS *</label>
              <input type="text" bind:value={form.apellidos} placeholder="Ej: Mendoza Morales" required />
            </div>
          {/if}

          <div class="sga-fg wide">
            <label>CORREO ELECTRÓNICO *</label>
            <input type="email" bind:value={form.correo} placeholder="usuario@uteq.edu.ec" required />
            <span class="sga-hint">Las credenciales de acceso se enviarán directamente a este correo.</span>
          </div>

          <div class="sga-fg {modoEdicion ? 'wide' : ''}">
            <label>ROL DE USUARIO *</label>
            <select bind:value={form.id_rol} required>
              {#each roles as r}
                <option value={r.id_rol}>{r.nombre_amigable || getRolFriendlyName(r.nombre)}</option>
              {/each}
            </select>
          </div>

          <div class="sga-fg {modoEdicion ? 'wide' : ''}">
            <label>FACULTAD (OPCIONAL)</label>
            <select bind:value={form.id_facultad}>
              <option value="">Todas / Dirección Central</option>
              {#each facultades as f}
                <option value={f.id_facultad}>{f.nombre}</option>
              {/each}
            </select>
          </div>
        </div>

        <div class="sga-modal-footer">
          <button type="button" class="sga-btn-cancel" onclick={() => { modalUsuario = false; }}>
            Cancelar
          </button>
          <button type="submit" class="sga-btn-submit" disabled={guardando}>
            {#if guardando}
              <i class="bi bi-arrow-repeat spin"></i> Creando y enviando correo...
            {:else}
              <i class="bi bi-check2-circle"></i> {modoEdicion ? 'Guardar cambios' : 'Crear usuario y enviar correo'}
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
/* ── SUBBAR ── */
.subbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 28px;
  background: #ffffff;
  border-bottom: 1px solid #eef2f6;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.84rem;
}

.breadcrumb a {
  color: #1b7a2b;
  text-decoration: none;
  font-weight: 700;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.breadcrumb .sep {
  color: #94a3b8;
}

.breadcrumb .current {
  color: #1e293b;
  font-weight: 800;
}

.btn-nuevo {
  background: #1b7a2b;
  color: #ffffff;
  border: none;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 0.84rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 3px 10px rgba(27, 122, 43, 0.2);
}

.btn-nuevo:hover {
  background: #155e04;
  transform: translateY(-1px);
}

/* ── PAGE BODY ── */
.page-body {
  padding: 24px 28px;
}

.main-card {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid #eef2f6;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  padding: 24px 26px;
}

/* ── HEADER Y FILTROS ── */
.card-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 22px;
}

.header-titles {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: #f5f3ff;
  color: #7c3aed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.45rem;
  flex-shrink: 0;
}

.header-titles h2 {
  font-size: 1.08rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 3px;
}

.header-titles p {
  font-size: 0.78rem;
  color: #64748b;
  margin: 0;
}

.filters-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  padding: 0 14px;
  width: 280px;
  transition: all 0.2s;
}

.search-box:focus-within {
  border-color: #1b7a2b;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.1);
}

.search-box i {
  color: #94a3b8;
  font-size: 0.85rem;
}

.search-box input {
  border: none;
  outline: none;
  padding: 8px 0;
  font-size: 0.82rem;
  font-family: inherit;
  background: transparent;
  width: 100%;
  color: #1e293b;
}

.btn-clear {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1.1rem;
}

.select-box select {
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
  background: #f8fafc;
  outline: none;
  cursor: pointer;
}

/* ── TABLA ESTILO VERDE SGA ── */
.table-container {
  overflow-x: auto;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
}

.sga-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.sga-table thead {
  background: #1b7a2b;
}

.sga-table th {
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 14px;
  text-align: left;
  border: none;
  white-space: nowrap;
}

.sga-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
  vertical-align: middle;
}

.sga-table tbody tr:hover {
  background: #f8fafc;
}

.row-inactiva {
  opacity: 0.6;
  background: #fafafa;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e8f5e9;
  color: #1b7a2b;
  font-weight: 800;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-handle {
  font-family: monospace;
  font-weight: 700;
  color: #1b7a2b;
  font-size: 0.88rem;
}

.email-text {
  font-size: 0.82rem;
  color: #334155;
}

/* Badges de Roles */
.rol-badge {
  font-size: 0.74rem;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 20px;
  display: inline-block;
  white-space: nowrap;
}

.badge-admin {
  background: #f5f3ff;
  color: #7c3aed;
  border: 1px solid #ddd6fe;
}

.badge-tecnico {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fde68a;
}

.badge-consulta {
  background: #e0f2fe;
  color: #0284c7;
  border: 1px solid #bae6fd;
}

/* Badges de Estado */
.badge-activo {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.badge-inactivo {
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* Acciones */
.actions-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-tbl {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.18s ease;
}

.btn-tbl.reset { color: #d97706; border-color: #fde68a; }
.btn-tbl.reset:hover { background: #fffbeb; }

.btn-tbl.edit { color: #0284c7; border-color: #bae6fd; }
.btn-tbl.edit:hover { background: #e0f2fe; }

.btn-tbl.toggle-off { color: #e11d48; border-color: #fecdd3; }
.btn-tbl.toggle-off:hover { background: #ffe4e6; }

.btn-tbl.toggle-on { color: #16a34a; border-color: #bbf7d0; }
.btn-tbl.toggle-on:hover { background: #f0fdf4; }

.fw-bold { font-weight: 700; }
.text-dark { color: #0f172a; }
.text-muted { color: #94a3b8; }
.text-center { text-align: center; }
.small { font-size: 0.76rem; }
.fst-italic { font-style: italic; }

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 0.88rem;
  font-weight: 600;
}

/* ── MODALES AL ESTILO SGA UTEQ (UNIFORME Y CONSISTENTE) ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.sga-modal-window {
  background: #ffffff;
  border-radius: 16px;
  width: 580px;
  max-width: 95vw;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: modalPop 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #e2e8f0;
}

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.sga-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
  background: #ffffff;
  border-bottom: 1px solid #eef2f6;
}

.sga-modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
  font-weight: 800;
  color: #1b7a2b;
  letter-spacing: 0.04em;
}

.green-icon {
  font-size: 1.15rem;
  color: #1b7a2b;
}

.sga-modal-close {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.18s;
}

.sga-modal-close:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.sga-modal-subtitle {
  padding: 8px 22px;
  background: #f8fafc;
  font-size: 0.72rem;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #eef2f6;
}

.sga-modal-body {
  padding: 22px 24px;
}

.sga-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 18px;
}

.sga-fg {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sga-fg.wide {
  grid-column: span 2;
}

.sga-fg label {
  font-size: 0.72rem;
  font-weight: 800;
  color: #475569;
  letter-spacing: 0.04em;
}

.sga-hint {
  font-size: 0.7rem;
  color: #64748b;
}

.sga-fg input,
.sga-fg select {
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 9px 13px;
  font-size: 0.86rem;
  font-family: inherit;
  font-weight: 600;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
  transition: all 0.2s ease;
}

.sga-fg input:focus,
.sga-fg select:focus {
  border-color: #1b7a2b;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.1);
}

.sga-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.sga-btn-cancel {
  background: #f1f5f9;
  color: #475569;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  padding: 8px 20px;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.sga-btn-cancel:hover {
  background: #e2e8f0;
}

.sga-btn-submit {
  background: #1b7a2b;
  color: #ffffff;
  border: none;
  border-radius: 20px;
  padding: 8px 24px;
  font-size: 0.84rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  box-shadow: 0 4px 12px rgba(27, 122, 43, 0.25);
  transition: all 0.2s;
}

.sga-btn-submit:hover:not(:disabled) {
  background: #155e04;
  transform: translateY(-1px);
}

.sga-btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin 0.7s linear infinite; }
</style>
