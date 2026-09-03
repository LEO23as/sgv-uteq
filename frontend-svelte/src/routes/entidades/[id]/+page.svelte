<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

    const id = $derived($page.params.id);
  let tipos = $state([]);
  let saving = $state(false);
  let loading = $state(true);
  let error = $state('');
  let form = $state({
    nombre:'', nombre_corto:'', id_tipo:'', ruc:'', sector:'', telefono:'', correo:'', pagina_web:'',
    representante_legal:'', cargo_representante:'',
    provincia:'', canton:'', parroquia:'', direccion:'', observaciones:'', activo:true,
  });

  onMount(async () => {
    try {
      const [tipoData, data] = await Promise.all([
        fetch('/api/entidades/create/', { credentials:'include' }).then(r => r.json()),
        fetch(`/api/entidades/${id}/`, { credentials:'include' }).then(r => r.json()),
      ]);
      tipos = tipoData.tipos || [];
      form = {
        nombre: data.nombre, nombre_corto: data.nombre_corto || '', id_tipo: String(data.id_tipo || ''),
        ruc: data.ruc || '', sector: data.sector || '', telefono: data.telefono || '',
        correo: data.correo || '', pagina_web: data.pagina_web || '',
        representante_legal: data.representante_legal || '', cargo_representante: data.cargo_representante || '',
        provincia: data.provincia || '', canton: data.canton || '', parroquia: data.parroquia || '',
        direccion: data.direccion || '', observaciones: data.observaciones || '', activo: data.activo,
      };
    } finally { loading = false; }
  });

  async function guardar() {
    error = ''; saving = true;
    try {
      const res = await fetch(`/api/entidades/${id}/`, {
        method:'PUT', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; return; }
      goto('/entidades');
    } catch { error = 'Error de conexión'; }
    finally { saving = false; }
  }
</script>

<svelte:head><title>Editar Entidad — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/entidades">Entidades cooperantes</a>
    <span class="sep">/</span>
    <span class="current">Editar entidad</span>
  </nav>
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <h2 class="form-title">
      <i class="bi bi-building"></i> Editar Entidad Cooperante
    </h2>

    {#if error}
      <div class="alert-error">
        <i class="bi bi-exclamation-triangle-fill"></i> {error}
      </div>
    {/if}

    <!-- SECCIÓN 1: INFORMACIÓN GENERAL -->
    <div class="sec">
      <h4 class="sec-hdr"><i class="bi bi-info-circle"></i> Información General</h4>
      <div class="form-grid">
        <div class="field col-8">
          <label for="f-nombre">Nombre completo o Razón Social *</label>
          <input
            id="f-nombre"
            bind:value={form.nombre}
            placeholder="Ej: Gobierno Autónomo Descentralizado Municipal de Quevedo"
          />
        </div>

        <div class="field col-4">
          <label for="f-corto">Siglas / Nombre corto</label>
          <input
            id="f-corto"
            bind:value={form.nombre_corto}
            placeholder="Ej: GADM Quevedo, MINEDUC..."
          />
        </div>

        <div class="field col-4">
          <label for="f-tipo">Tipo de entidad *</label>
          <select id="f-tipo" bind:value={form.id_tipo}>
            {#each tipos as t}
              <option value={String(t.id_tipo)}>{t.nombre}</option>
            {/each}
          </select>
        </div>

        <div class="field col-4">
          <label for="f-ruc">Número de RUC (13 dígitos)</label>
          <input
            id="f-ruc"
            type="text"
            maxlength="13"
            bind:value={form.ruc}
            oninput={(e) => e.target.value = e.target.value.replace(/\D/g, '').slice(0, 13)}
            placeholder="1203456789001"
          />
        </div>

        <div class="field col-4">
          <label for="f-sector">Sector Institucional</label>
          <input
            id="f-sector"
            bind:value={form.sector}
            placeholder="Público, Privado, Comunitario, ONG..."
          />
        </div>

        <div class="field col-4">
          <label for="f-tel">Teléfono de contacto</label>
          <input
            id="f-tel"
            bind:value={form.telefono}
            placeholder="052750000 / 099..."
          />
        </div>

        <div class="field col-4">
          <label for="f-correo">Correo electrónico</label>
          <input
            id="f-correo"
            type="email"
            bind:value={form.correo}
            placeholder="contacto@entidad.gob.ec"
          />
        </div>

        <div class="field col-4">
          <label for="f-web">Sitio Web institucional</label>
          <input
            id="f-web"
            bind:value={form.pagina_web}
            placeholder="https://www.entidad.gob.ec"
          />
        </div>
      </div>
    </div>

    <!-- SECCIÓN 2: REPRESENTANTE LEGAL -->
    <div class="sec">
      <h4 class="sec-hdr"><i class="bi bi-person-badge"></i> Representante Legal</h4>
      <div class="form-grid">
        <div class="field col-7">
          <label for="f-rep">Nombres y Apellidos del Representante</label>
          <input
            id="f-rep"
            type="text"
            bind:value={form.representante_legal}
            placeholder="Ej: Ing. Marco Antonio Solís, M.Sc."
          />
        </div>

        <div class="field col-5">
          <label for="f-cargo">Cargo o Función</label>
          <input
            id="f-cargo"
            bind:value={form.cargo_representante}
            placeholder="Ej: Alcalde, Director Ejecutivo, Gerente..."
          />
        </div>
      </div>
    </div>

    <!-- SECCIÓN 3: UBICACIÓN -->
    <div class="sec">
      <h4 class="sec-hdr"><i class="bi bi-geo-alt"></i> Ubicación y Domicilio</h4>
      <div class="form-grid">
        <div class="field col-4">
          <label for="f-prov">Provincia</label>
          <input
            id="f-prov"
            bind:value={form.provincia}
            placeholder="Ej: Los Ríos"
          />
        </div>

        <div class="field col-4">
          <label for="f-canton">Cantón</label>
          <input
            id="f-canton"
            bind:value={form.canton}
            placeholder="Ej: Quevedo"
          />
        </div>

        <div class="field col-4">
          <label for="f-parr">Parroquia</label>
          <input
            id="f-parr"
            bind:value={form.parroquia}
            placeholder="Ej: San Camilo, El Guayacán..."
          />
        </div>

        <div class="field col-12">
          <label for="f-dir">Dirección exacta / Referencia</label>
          <input
            id="f-dir"
            bind:value={form.direccion}
            placeholder="Av. Principal y Calle Secundaria, Edificio Central..."
          />
        </div>
      </div>
    </div>

    <!-- SECCIÓN 4: OBSERVACIONES Y ESTADO -->
    <div class="sec">
      <h4 class="sec-hdr"><i class="bi bi-card-text"></i> Observaciones y Estado</h4>
      <div class="form-grid">
        <div class="field col-8">
          <label for="f-obs">Observaciones adicionales</label>
          <textarea
            id="f-obs"
            rows="2"
            bind:value={form.observaciones}
            placeholder="Notas adicionales sobre la cooperación institucional..."
          ></textarea>
        </div>

        <div class="field col-4">
          <label>Estado de la entidad</label>
          <label class="toggle-card" class:active={form.activo}>
            <input type="checkbox" bind:checked={form.activo} />
            <div class="tc-content">
              <i class="bi {form.activo ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}"></i>
              <div>
                <strong>{form.activo ? 'Entidad Activa' : 'Entidad Inactiva'}</strong>
                <p>{form.activo ? 'Disponible para convenios' : 'Deshabilitada temporalmente'}</p>
              </div>
            </div>
          </label>
        </div>
      </div>
    </div>

    <div class="form-actions">
      <a href="/entidades" class="btn-cancel">Cancelar</a>
      <button class="btn-save" onclick={guardar} disabled={saving}>
        {#if saving}
          <i class="bi bi-arrow-repeat spin"></i> Guardando...
        {:else}
          <i class="bi bi-check2-circle"></i> Guardar cambios
        {/if}
      </button>
    </div>
  </div>
</div>
{/if}

<style>
  .loading-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--gris);
    padding: 60px;
    justify-content: center;
    font-size: 1rem;
    font-weight: 700;
  }
  .form-wrap {
    padding: 24px;
    max-width: 1100px;
    margin: 0 auto;
  }
  .form-card {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 28px 32px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
  }
  .form-title {
    font-size: 1.25rem;
    font-weight: 900;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 24px;
  }
  .form-title i {
    color: #1b7505;
    font-size: 1.4rem;
  }
  .alert-error {
    background: #fef2f2;
    border: 1.5px solid #fecaca;
    color: #b91c1c;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.88rem;
    font-weight: 700;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .sec {
    margin-bottom: 26px;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 22px;
  }
  .sec:last-of-type {
    border-bottom: none;
    margin-bottom: 12px;
    padding-bottom: 0;
  }
  .sec-hdr {
    font-size: 0.8rem;
    font-weight: 800;
    color: #1b7505;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* Grid de 12 Columnas perfecto */
  .form-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 16px 18px;
    width: 100%;
  }
  .col-12 { grid-column: span 12; }
  .col-8  { grid-column: span 8; }
  .col-7  { grid-column: span 7; }
  .col-5  { grid-column: span 5; }
  .col-4  { grid-column: span 4; }

  @media (max-width: 900px) {
    .col-8, .col-7, .col-5, .col-4 {
      grid-column: span 12;
    }
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .field label {
    font-size: 0.72rem;
    font-weight: 800;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    min-height: 18px;
    display: flex;
    align-items: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .field input,
  .field select,
  .field textarea {
    height: 42px;
    border: 1.5px solid #cbd5e1;
    border-radius: 9px;
    padding: 0 14px;
    font-size: 0.88rem;
    font-family: inherit;
    background: #ffffff;
    color: #1e293b;
    box-sizing: border-box;
    transition: all 0.2s ease;
  }
  .field textarea {
    height: auto;
    min-height: 76px;
    padding: 10px 14px;
    resize: vertical;
  }
  .field input:focus,
  .field select:focus,
  .field textarea:focus {
    border-color: #1b7505;
    box-shadow: 0 0 0 3px rgba(27, 117, 5, 0.12);
    outline: none;
  }

  /* Toggle Card de Estado */
  .toggle-card {
    display: flex;
    align-items: center;
    border: 1.5px solid #cbd5e1;
    border-radius: 9px;
    padding: 8px 14px;
    cursor: pointer;
    background: #f8fafc;
    transition: all 0.2s ease;
    height: 76px;
    box-sizing: border-box;
  }
  .toggle-card.active {
    border-color: #1b7505;
    background: #f0fdf4;
  }
  .toggle-card input {
    display: none;
  }
  .tc-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .tc-content i {
    font-size: 1.4rem;
    color: #94a3b8;
  }
  .toggle-card.active .tc-content i {
    color: #1b7505;
  }
  .tc-content strong {
    display: block;
    font-size: 0.88rem;
    color: #1e293b;
  }
  .tc-content p {
    margin: 2px 0 0 0;
    font-size: 0.74rem;
    color: #64748b;
  }

  /* Acciones */
  .form-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
  }
  .btn-cancel {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 9px;
    padding: 10px 22px;
    font-size: 0.88rem;
    font-weight: 700;
    color: #475569;
    text-decoration: none;
    transition: all 0.15s ease;
  }
  .btn-cancel:hover {
    background: #f1f5f9;
    color: #1e293b;
  }
  .btn-save {
    background: #1b7505;
    border: none;
    border-radius: 9px;
    padding: 10px 28px;
    font-size: 0.88rem;
    font-weight: 800;
    color: #ffffff;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background 0.2s, transform 0.15s;
  }
  .btn-save:hover:not(:disabled) {
    background: #155e04;
  }
  .btn-save:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .spin {
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
