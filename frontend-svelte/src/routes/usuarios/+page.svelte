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

  // Modales
  let modalUsuario = $state(false);
  let modalCredenciales = $state(false);
  let modoEdicion = $state(false);
  let guardando = $state(false);
  let copiado = $state(false);

  // Formulario de Usuario
  let form = $state({
    id_usuario: null,
    nombres: '',
    apellidos: '',
    correo: '',
    id_rol: 3, // Default TECNICO (Asistente)
    id_facultad: '',
    username: '',
    password: '',
    activo: true,
  });

  // Credenciales generadas
  let credenciales = $state({
    username: '',
    nombres: '',
    password_temporal: '',
    correo: '',
    rol: '',
    correo_enviado: false,
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
      id_rol: roles.find(r => r.nombre === 'TECNICO')?.id_rol || (roles[0]?.id_rol ?? 3),
      id_facultad: '',
      username: '',
      password: '',
      activo: true,
    };
    modalUsuario = true;
  }

  function abrirEditarUsuario(u) {
    modoEdicion = true;
    const partes = (u.nombres || '').split(' ');
    form = {
      id_usuario: u.id_usuario,
      nombres: u.nombres,
      apellidos: '',
      correo: u.correo || '',
      id_rol: u.id_rol,
      id_facultad: u.id_facultad || '',
      username: u.username,
      password: '',
      activo: u.activo,
    };
    modalUsuario = true;
  }

  async function guardarUsuario() {
    if (!form.nombres.trim()) {
      toast.error('Ingresa los nombres del usuario');
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
        // Crear
        const res = await fetch('/api/usuarios/crear/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nombres: form.nombres.trim(),
            apellidos: form.apellidos.trim(),
            correo: form.correo.trim(),
            id_rol: form.id_rol,
            id_facultad: form.id_facultad || null,
            username: form.username.trim(),
            password: form.password.trim(),
          }),
          credentials: 'include',
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al crear usuario');

        modalUsuario = false;
        credenciales = {
          username: data.username,
          nombres: data.nombres,
          password_temporal: data.password_temporal,
          correo: data.correo,
          rol: data.rol,
          correo_enviado: data.correo_enviado,
        };
        copiado = false;
        modalCredenciales = true;
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

      credenciales = {
        username: data.username,
        nombres: data.nombres,
        password_temporal: data.password_temporal,
        correo: data.correo,
        rol: u.rol,
        correo_enviado: data.correo_enviado,
      };
      copiado = false;
      modalCredenciales = true;
      toast.success('Nueva contraseña temporal generada');
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

  function copiarAlPortapapeles() {
    const texto = `CREDENTIALES DE ACCESO - SGV UTEQ\n\nUsuario: ${credenciales.username}\nContraseña temporal: ${credenciales.password_temporal}\nRol: ${credenciales.rol}\n\nIngresa en: http://18.227.201.40:5174/`;
    navigator.clipboard.writeText(texto);
    copiado = true;
    toast.success('¡Credenciales copiadas al portapapeles!');
    setTimeout(() => { copiado = false; }, 3000);
  }

  function getRolBadgeClass(rol) {
    if (!rol) return 'badge-neutral';
    const r = rol.toUpperCase();
    if (r.includes('ADMIN') || r.includes('DIRECTOR')) return 'badge-admin';
    if (r.includes('TECNICO') || r.includes('ASISTENTE')) return 'badge-tecnico';
    if (r.includes('CONSULTA') || r.includes('SECRETARI')) return 'badge-consulta';
    return 'badge-docente';
  }

  function getRolFriendlyName(rol) {
    if (!rol) return 'Sin Rol';
    const r = rol.toUpperCase();
    if (r.includes('ADMIN')) return 'Administrador';
    if (r.includes('DIRECTOR')) return 'Director(a) de Vinculación';
    if (r.includes('TECNICO')) return 'Asistente / Técnico';
    if (r.includes('CONSULTA')) return 'Secretario(a) / Consulta';
    if (r.includes('DOCENTE')) return 'Docente';
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
          <p>Administración de cuentas de acceso, roles institucionales y permisos de seguridad.</p>
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
              <option value={r.id_rol}>{getRolFriendlyName(r.nombre)}</option>
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
              <th>CORREO INSTITUCIONAL</th>
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
                    <button class="btn-tbl reset" onclick={() => resetPassword(u)} title="Restablecer contraseña">
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
    <div class="modal-card" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <div class="m-icon">
          <i class="bi {modoEdicion ? 'bi-pencil-square' : 'bi-person-plus-fill'}"></i>
        </div>
        <div class="m-titles">
          <h3>{modoEdicion ? 'Editar Usuario' : 'Crear Nuevo Usuario'}</h3>
          <p>{modoEdicion ? 'Modifica los datos del usuario seleccionado' : 'Ingresa la información para generar una cuenta institucional'}</p>
        </div>
        <button class="m-close" onclick={() => { modalUsuario = false; }}>&times;</button>
      </div>

      <form onsubmit={(e) => { e.preventDefault(); guardarUsuario(); }} class="modal-form">
        <div class="form-grid">
          <div class="f-group">
            <label>Nombres *</label>
            <input type="text" bind:value={form.nombres} placeholder="Ej: Pedro Vicente" required />
          </div>

          {#if !modoEdicion}
            <div class="f-group">
              <label>Apellidos *</label>
              <input type="text" bind:value={form.apellidos} placeholder="Ej: Castro López" required />
            </div>
          {/if}

          <div class="f-group wide">
            <label>Correo Institucional</label>
            <input type="email" bind:value={form.correo} placeholder="ejemplo@uteq.edu.ec" />
            <span class="f-hint">Se utilizará para notificaciones y envío de credenciales.</span>
          </div>

          <div class="f-group">
            <label>Rol de Usuario *</label>
            <select bind:value={form.id_rol} required>
              {#each roles as r}
                <option value={r.id_rol}>{getRolFriendlyName(r.nombre)}</option>
              {/each}
            </select>
          </div>

          <div class="f-group">
            <label>Facultad (Opcional)</label>
            <select bind:value={form.id_facultad}>
              <option value="">Todas / Dirección Central</option>
              {#each facultades as f}
                <option value={f.id_facultad}>{f.nombre}</option>
              {/each}
            </select>
          </div>

          {#if !modoEdicion}
            <div class="f-group">
              <label>Nombre de Usuario <span class="f-opt">(Opcional)</span></label>
              <input type="text" bind:value={form.username} placeholder="Automático (ej: pcastrol)" />
            </div>

            <div class="f-group">
              <label>Contraseña Inicial <span class="f-opt">(Opcional)</span></label>
              <input type="text" bind:value={form.password} placeholder="Automática segura (10 caracteres)" />
            </div>
          {/if}
        </div>

        <div class="modal-footer">
          <button type="button" class="btn-cancelar" onclick={() => { modalUsuario = false; }}>Cancelar</button>
          <button type="submit" class="btn-guardar" disabled={guardando}>
            {#if guardando}
              <i class="bi bi-arrow-repeat spin"></i> Guardando...
            {:else}
              <i class="bi bi-check2-circle"></i> {modoEdicion ? 'Guardar cambios' : 'Crear usuario'}
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- MODAL: CREDENCIALES GENERADAS -->
{#if modalCredenciales}
  <div class="modal-backdrop" onclick={() => { modalCredenciales = false; }}>
    <div class="modal-card creds-modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header creds-header">
        <div class="m-icon success">
          <i class="bi bi-shield-check"></i>
        </div>
        <div class="m-titles">
          <h3>Credenciales Generadas con Éxito</h3>
          <p>Comparte estos accesos de forma segura con el usuario.</p>
        </div>
        <button class="m-close" onclick={() => { modalCredenciales = false; }}>&times;</button>
      </div>

      <div class="creds-body">
        <div class="creds-banner">
          <i class="bi bi-info-circle-fill"></i>
          <span>Por seguridad, el usuario deberá cambiar su contraseña temporal al ingresar por primera vez.</span>
        </div>

        <div class="cred-card-box">
          <div class="cred-row">
            <span class="cred-label">NOMBRE:</span>
            <span class="cred-val fw-bold">{credenciales.nombres}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">USUARIO:</span>
            <span class="cred-val code-val">{credenciales.username}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">CONTRASEÑA TEMPORAL:</span>
            <span class="cred-val pass-val">{credenciales.password_temporal}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">ROL ASIGNADO:</span>
            <span class="cred-val">{getRolFriendlyName(credenciales.rol)}</span>
          </div>
          {#if credenciales.correo}
            <div class="cred-row">
              <span class="cred-label">CORREO:</span>
              <span class="cred-val">{credenciales.correo}</span>
            </div>
          {/if}
        </div>

        <div class="creds-status">
          {#if credenciales.correo_enviado}
            <div class="alert ok-clean"><i class="bi bi-send-check-fill text-success"></i> Credenciales enviadas automáticamente al correo institucional.</div>
          {:else}
            <div class="alert note-clean"><i class="bi bi-clipboard-check"></i> Puedes copiar las credenciales a continuación para enviarlas al usuario.</div>
          {/if}
        </div>

        <div class="creds-actions">
          <button class="btn-copiar {copiado ? 'btn-copiado' : ''}" onclick={copiarAlPortapapeles}>
            <i class="bi {copiado ? 'bi-clipboard-check-fill' : 'bi-clipboard'}"></i>
            {copiado ? '¡Copiado al portapapeles!' : 'Copiar credenciales'}
          </button>
          <button class="btn-entendido" onclick={() => { modalCredenciales = false; }}>
            Listo, entendido
          </button>
        </div>
      </div>
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

.badge-docente {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
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

/* ── MODALES ── */
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

.modal-card {
  background: #ffffff;
  border-radius: 20px;
  width: 540px;
  max-width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  animation: modalIn 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 24px;
  border-bottom: 1px solid #eef2f6;
  position: relative;
}

.m-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #e8f5e9;
  color: #1b7a2b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}

.m-icon.success {
  background: #f0fdf4;
  color: #16a34a;
}

.m-titles h3 {
  font-size: 1rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 2px;
}

.m-titles p {
  font-size: 0.74rem;
  color: #64748b;
  margin: 0;
}

.m-close {
  position: absolute;
  top: 14px;
  right: 18px;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #94a3b8;
  cursor: pointer;
}

.modal-form {
  padding: 20px 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 16px;
}

.f-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.f-group.wide {
  grid-column: span 2;
}

.f-group label {
  font-size: 0.72rem;
  font-weight: 800;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.f-opt {
  text-transform: none;
  font-weight: 600;
  color: #94a3b8;
}

.f-hint {
  font-size: 0.7rem;
  color: #64748b;
}

.f-group input,
.f-group select {
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 0.85rem;
  font-family: inherit;
  font-weight: 600;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
}

.f-group input:focus,
.f-group select:focus {
  border-color: #1b7a2b;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
}

.btn-cancelar {
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-guardar {
  background: #1b7a2b;
  color: #ffffff;
  border: none;
  border-radius: 20px;
  padding: 8px 22px;
  font-size: 0.82rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 3px 10px rgba(27, 122, 43, 0.2);
}

.btn-guardar:hover:not(:disabled) { background: #155e04; }
.btn-guardar:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── MODAL CREDENCIALES ── */
.creds-modal {
  width: 480px;
}

.creds-body {
  padding: 20px 24px;
}

.creds-banner {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 0.78rem;
  font-weight: 600;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 16px;
}

.cred-card-box {
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.cred-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
}

.cred-label {
  font-size: 0.68rem;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.05em;
}

.cred-val {
  color: #0f172a;
}

.code-val {
  font-family: monospace;
  font-size: 0.95rem;
  font-weight: 800;
  color: #1b7a2b;
  background: #e8f5e9;
  padding: 2px 8px;
  border-radius: 6px;
}

.pass-val {
  font-family: monospace;
  font-size: 0.95rem;
  font-weight: 800;
  color: #7c3aed;
  background: #f5f3ff;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px dashed #c4b5fd;
}

.alert.ok-clean {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 0.78rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.alert.note-clean {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #475569;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 0.78rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.creds-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 18px;
}

.btn-copiar {
  background: #1b7a2b;
  color: #ffffff;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-size: 0.86rem;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(27, 122, 43, 0.2);
}

.btn-copiar:hover {
  background: #155e04;
}

.btn-copiado {
  background: #0f766e !important;
}

.btn-entendido {
  background: #f1f5f9;
  color: #334155;
  border: none;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin 0.7s linear infinite; }
</style>
