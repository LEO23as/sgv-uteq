<script>
  import { toast } from '$lib/toast';

  let {
    open = $bindable(false),
    proyectoId,
    onCreated = () => {},
  } = $props();

  let entidades = $state([]);
  let tipos = $state([]);
  let periodos = $state([]);
  let cargado = $state(false);
  let saving = $state(false);
  let error = $state('');

  let nuevaEntidad = $state(false);

  // Buscador de entidad existente
  let busquedaEntidad = $state('');
  let entidadSeleccionada = $state(null);
  let mostrarDropdown = $state(false);

  let form = $state({
    id_entidad:'', id_periodo:'', numero_memorando:'',
    estado:'VIGENTE', fecha_firma:'', fecha_inicio:'', fecha_fin:'',
    duracion_anios:2, estudiantes_asignados:'', observaciones:'',
  });

  let entidadForm = $state({ nombre:'', id_tipo:'', ruc:'', telefono:'', correo:'' });

  const ESTADOS = ['VIGENTE','VENCIDO','RENOVADO','CANCELADO'];

  $effect(() => {
    if (open && !cargado) cargar();
  });

  async function cargar() {
    try {
      const [entRes, tiposRes, perRes] = await Promise.all([
        fetch('/api/entidades/', { credentials:'include' }).then(r => r.json()),
        fetch('/api/entidades/create/', { credentials:'include' }).then(r => r.json()),
        fetch('/api/periodos/', { credentials:'include' }).then(r => r.json()),
      ]);
      entidades = entRes || [];
      tipos = tiposRes.tipos || [];
      periodos = perRes || [];
      cargado = true;
    } catch { toast.error('No se pudieron cargar los datos del formulario'); }
  }

  // Filtrado reactivo de entidades por Nombre, RUC o Cédula
  let entidadesFiltradas = $derived.by(() => {
    const q = busquedaEntidad.trim().toLowerCase();
    if (!q) return entidades.slice(0, 15);
    return entidades.filter(e => {
      const nom = (e.nombre || '').toLowerCase();
      const ruc = (e.ruc || '').toLowerCase();
      const tipo = (e.tipo_nombre || e.tipo || '').toLowerCase();
      const rep = (e.representante_legal || '').toLowerCase();
      return nom.includes(q) || ruc.includes(q) || tipo.includes(q) || rep.includes(q);
    }).slice(0, 25);
  });

  function seleccionarEntidad(e) {
    entidadSeleccionada = e;
    form.id_entidad = e.id_entidad;
    busquedaEntidad = '';
    mostrarDropdown = false;
  }

  function deseleccionarEntidad() {
    entidadSeleccionada = null;
    form.id_entidad = '';
    busquedaEntidad = '';
  }

  function cerrar() {
    open = false;
    error = '';
    nuevaEntidad = false;
    entidadSeleccionada = null;
    busquedaEntidad = '';
    mostrarDropdown = false;
    form = { id_entidad:'', id_periodo:'', numero_memorando:'', estado:'VIGENTE',
      fecha_firma:'', fecha_inicio:'', fecha_fin:'', duracion_anios:2,
      estudiantes_asignados:'', observaciones:'' };
    entidadForm = { nombre:'', id_tipo:'', ruc:'', telefono:'', correo:'' };
  }

  async function guardar() {
    error = '';
    if (nuevaEntidad) {
      if (!entidadForm.nombre || !entidadForm.id_tipo) {
        error = 'Nombre y tipo de la entidad son obligatorios.'; return;
      }
    } else if (!form.id_entidad) {
      error = 'Debes buscar y seleccionar una entidad cooperante.'; return;
    }
    if (form.fecha_inicio && form.fecha_fin && form.fecha_fin < form.fecha_inicio) {
      error = 'La fecha de fin no puede ser anterior a la fecha de inicio.'; return;
    }
    saving = true;
    try {
      let idEntidad = form.id_entidad;
      if (nuevaEntidad) {
        const resEnt = await fetch('/api/entidades/create/', {
          method:'POST', credentials:'include',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify(entidadForm),
        });
        const dataEnt = await resEnt.json();
        if (!resEnt.ok) { error = dataEnt.error || 'Error al crear la entidad'; return; }
        idEntidad = dataEnt.id_entidad;
      }
      const res = await fetch('/api/convenios/create/', {
        method:'POST', credentials:'include',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ ...form, id_proyecto: proyectoId, id_entidad: idEntidad }),
      });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear el convenio'; return; }
      toast.success('Convenio registrado exitosamente');
      onCreated(data);
      cerrar();
    } catch { error = 'Error de conexión con el servidor'; }
    finally { saving = false; }
  }
</script>

{#if open}
  <div class="modal-overlay" onclick={cerrar}>
    <div class="modal-card" onclick={(e) => e.stopPropagation()}>
      
      <!-- HEADER MODAL INSTITUCIONAL LIMPIO -->
      <div class="modal-hdr">
        <div class="hdr-title-wrap">
          <div class="hdr-icon"><i class="bi bi-file-earmark-text-fill"></i></div>
          <div>
            <h3>Registrar Convenio</h3>
            <span class="hdr-sub">Vinculación institucional y entidad cooperante</span>
          </div>
        </div>
        <button class="modal-close" onclick={cerrar} aria-label="Cerrar"><i class="bi bi-x-lg"></i></button>
      </div>

      {#if error}<div class="alert-error"><i class="bi bi-exclamation-triangle-fill"></i> {error}</div>{/if}

      <div class="modal-body">
        
        <!-- SELECCIÓN O REGISTRO DE ENTIDAD COOPERANTE -->
        <div class="sec">
          <div class="entidad-toggle">
            <button type="button" class:activo={!nuevaEntidad} onclick={() => { nuevaEntidad = false; }}>
              <i class="bi bi-search"></i> Buscar Entidad Existente
            </button>
            <button type="button" class:activo={nuevaEntidad} onclick={() => { nuevaEntidad = true; deseleccionarEntidad(); }}>
              <i class="bi bi-plus-circle"></i> + Nueva Entidad Cooperante
            </button>
          </div>

          {#if !nuevaEntidad}
            <div class="field full-width">
              <label>Entidad Cooperante *</label>
              
              {#if entidadSeleccionada}
                <!-- TARJETA DE ENTIDAD SELECCIONADA -->
                <div class="entidad-selected-card">
                  <div class="esc-info">
                    <div class="esc-title">
                      <i class="bi bi-building-check text-green"></i>
                      <span>{entidadSeleccionada.nombre}</span>
                    </div>
                    <div class="esc-meta">
                      {#if entidadSeleccionada.ruc}<span class="esc-badge"><i class="bi bi-card-heading"></i> RUC: {entidadSeleccionada.ruc}</span>{/if}
                      {#if entidadSeleccionada.tipo_nombre || entidadSeleccionada.tipo}<span class="esc-badge gray">{entidadSeleccionada.tipo_nombre || entidadSeleccionada.tipo}</span>{/if}
                      {#if entidadSeleccionada.canton}<span>· {entidadSeleccionada.canton}</span>{/if}
                    </div>
                  </div>
                  <button type="button" class="btn-cambiar-ent" onclick={deseleccionarEntidad} title="Cambiar entidad seleccionada">
                    <i class="bi bi-arrow-repeat"></i> Cambiar
                  </button>
                </div>
              {:else}
                <!-- BUSCADOR INTELIGENTE POR NOMBRE O RUC -->
                <div class="ent-search-wrapper">
                  <div class="ent-search-box" class:focused={mostrarDropdown}>
                    <i class="bi bi-search"></i>
                    <input
                      bind:value={busquedaEntidad}
                      onfocus={() => mostrarDropdown = true}
                      placeholder="Escribe el nombre de la empresa, GAD, RUC o Cédula..."
                    />
                    {#if busquedaEntidad}
                      <button type="button" class="btn-clear-search" onclick={() => busquedaEntidad = ''}><i class="bi bi-x"></i></button>
                    {/if}
                  </div>

                  {#if mostrarDropdown}
                    <ul class="ent-results-dropdown">
                      {#if entidadesFiltradas.length}
                        {#each entidadesFiltradas as e}
                          <li onclick={() => seleccionarEntidad(e)}>
                            <div class="er-main">
                              <i class="bi bi-building"></i>
                              <span class="er-name">{e.nombre}</span>
                            </div>
                            <div class="er-meta">
                              {#if e.ruc}<span class="er-ruc">RUC: {e.ruc}</span>{/if}
                              {#if e.tipo_nombre || e.tipo}<span class="er-tipo">{e.tipo_nombre || e.tipo}</span>{/if}
                            </div>
                          </li>
                        {/each}
                      {:else}
                        <li class="er-empty">
                          <span>No se encontraron entidades con "<strong>{busquedaEntidad}</strong>".</span>
                          <button type="button" class="btn-crear-inline" onclick={() => { nuevaEntidad = true; entidadForm.nombre = busquedaEntidad; }}>
                            <i class="bi bi-plus-lg"></i> Registrar como nueva entidad
                          </button>
                        </li>
                      {/if}
                    </ul>
                  {/if}
                </div>
              {/if}
            </div>

          {:else}
            <!-- FORMULARIO DE NUEVA ENTIDAD -->
            <div class="grid-3 mb-12">
              <div class="field col-span-2">
                <label>Nombre completo de la Entidad *</label>
                <input bind:value={entidadForm.nombre} placeholder="Ej: Gobierno Autónomo Descentralizado Municipal..." />
              </div>
              <div class="field">
                <label>Tipo de entidad *</label>
                <select bind:value={entidadForm.id_tipo}>
                  <option value="">— Seleccionar —</option>
                  {#each tipos as t}<option value={t.id_tipo}>{t.nombre}</option>{/each}
                </select>
              </div>
            </div>
            <div class="grid-3">
              <div class="field">
                <label>RUC o Cédula</label>
                <input
                  type="text"
                  maxlength="13"
                  bind:value={entidadForm.ruc}
                  oninput={(e) => e.target.value = e.target.value.replace(/\D/g, '').slice(0, 13)}
                  placeholder="Ej. 1291823912001"
                />
              </div>
              <div class="field"><label>Teléfono</label><input bind:value={entidadForm.telefono} placeholder="Ej. 0991234567" /></div>
              <div class="field"><label>Correo Electrónico</label><input type="email" bind:value={entidadForm.correo} placeholder="contacto@entidad.gob.ec" /></div>
            </div>
          {/if}
        </div>

        <!-- PERÍODO, MEMORANDO Y ESTADO -->
        <div class="sec">
          <div class="grid-3">
            <div class="field">
              <label>Período Académico</label>
              <select bind:value={form.id_periodo}>
                <option value="">— Seleccionar período —</option>
                {#each periodos as p}<option value={p.id_periodo}>{p.nombre || p.codigo}</option>{/each}
              </select>
            </div>
            <div class="field">
              <label>N° Memorando / Código</label>
              <input bind:value={form.numero_memorando} placeholder="Ej. VCL-2025-001" />
            </div>
            <div class="field">
              <label>Estado del Convenio *</label>
              <select bind:value={form.estado}>
                {#each ESTADOS as e}<option value={e}>{e}</option>{/each}
              </select>
            </div>
          </div>
        </div>

        <!-- FECHAS Y DURACIÓN -->
        <div class="sec">
          <div class="grid-4">
            <div class="field"><label>Fecha de firma</label><input type="date" bind:value={form.fecha_firma} /></div>
            <div class="field"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
            <div class="field"><label>Fecha de fin</label><input type="date" bind:value={form.fecha_fin} min={form.fecha_inicio} /></div>
            <div class="field"><label>Duración (años)</label><input type="number" min="1" max="10" bind:value={form.duracion_anios} /></div>
          </div>
        </div>

        <!-- ESTUDIANTES Y OBSERVACIONES -->
        <div class="sec no-border">
          <div class="grid-obs">
            <div class="field">
              <label>Estudiantes asignados</label>
              <input type="number" min="0" bind:value={form.estudiantes_asignados} placeholder="0" />
            </div>
            <div class="field">
              <label>Observaciones del convenio</label>
              <textarea rows="3" bind:value={form.observaciones} placeholder="Detalles u observaciones adicionales del convenio..."></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- FOOTER ACCIONES -->
      <div class="modal-actions">
        <button class="btn-cancel" onclick={cerrar}>Cancelar</button>
        <button class="btn-registrar" onclick={guardar} disabled={saving}>
          {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}<i class="bi bi-check-lg"></i> Registrar convenio{/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(3px);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999; padding: 20px;
  }
  .modal-card {
    background: #ffffff; border-radius: 16px; max-width: 860px; width: 100%; max-height: 90vh;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
    display: flex; flex-direction: column; overflow: hidden;
    border: 1px solid #e2e8f0;
  }

  /* HEADER MODERNO */
  .modal-hdr {
    display: flex; align-items: center; justify-content: space-between; padding: 18px 24px;
    background: #ffffff; border-bottom: 1px solid #e2e8f0; flex-shrink: 0;
  }
  .hdr-title-wrap { display: flex; align-items: center; gap: 12px; }
  .hdr-icon {
    width: 38px; height: 38px; border-radius: 10px;
    background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0;
    display: flex; align-items: center; justify-content: center; font-size: 1.15rem;
  }
  .hdr-title-wrap h3 { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin: 0; }
  .hdr-sub { font-size: 0.76rem; color: #64748b; font-weight: 600; }
  
  .modal-close {
    background: #f1f5f9; border: 1px solid #e2e8f0; color: #64748b; font-size: 0.95rem;
    cursor: pointer; width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center; transition: all 0.18s;
  }
  .modal-close:hover { background: #fee2e2; color: #dc2626; border-color: #fecaca; }
  
  .modal-body { padding: 22px 26px; overflow-y: auto; min-height: 0; display: flex; flex-direction: column; gap: 18px; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 26px; background: #f8fafc; border-top: 1px solid #e2e8f0; flex-shrink: 0; }

  .sec { border-bottom: 1px solid #f1f5f9; padding-bottom: 16px; }
  .sec.no-border { border-bottom: none; padding-bottom: 0; }

  /* TOGGLE TABS ENTIDAD */
  .entidad-toggle {
    display: flex; gap: 6px; background: #f1f5f9; padding: 4px; border-radius: 10px; margin-bottom: 14px;
  }
  .entidad-toggle button {
    flex: 1; padding: 8px 14px; border: none; border-radius: 7px;
    background: transparent; font-family: inherit; font-size: 0.82rem; font-weight: 700; color: #64748b; cursor: pointer;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    transition: all 0.15s ease;
  }
  .entidad-toggle button:hover { color: #16a34a; }
  .entidad-toggle button.activo { background: #ffffff; color: #15803d; box-shadow: 0 2px 6px rgba(0,0,0,0.06); font-weight: 800; }

  /* BUSCADOR DE ENTIDADES COMBOBOX */
  .ent-search-wrapper { position: relative; width: 100%; }
  .ent-search-box {
    display: flex; align-items: center; gap: 9px;
    border: 1.5px solid #cbd5e1; border-radius: 10px;
    padding: 9px 14px; background: #ffffff; transition: all 0.2s;
  }
  .ent-search-box.focused, .ent-search-box:focus-within {
    border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.12);
  }
  .ent-search-box > .bi-search { color: #94a3b8; font-size: 0.95rem; }
  .ent-search-box input {
    flex: 1; border: none; background: transparent; outline: none;
    font-size: 0.86rem; font-family: inherit; font-weight: 600; color: #1e293b;
  }
  .btn-clear-search { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 1.1rem; padding: 0 4px; }
  .btn-clear-search:hover { color: #334155; }

  .ent-results-dropdown {
    list-style: none; position: absolute; top: calc(100% + 5px); left: 0; right: 0;
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15); z-index: 1200;
    max-height: 240px; overflow-y: auto; margin: 0; padding: 0;
  }
  .ent-results-dropdown li {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #f1f5f9; gap: 10px;
    transition: background 0.15s;
  }
  .ent-results-dropdown li:last-child { border-bottom: none; }
  .ent-results-dropdown li:hover { background: #f0fdf4; }
  .er-main { display: flex; align-items: center; gap: 8px; min-width: 0; }
  .er-main i { color: #16a34a; font-size: 0.95rem; flex-shrink: 0; }
  .er-name { font-size: 0.84rem; font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .er-meta { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
  .er-ruc { font-size: 0.72rem; font-weight: 700; color: #0284c7; background: #e0f2fe; padding: 2px 6px; border-radius: 4px; }
  .er-tipo { font-size: 0.7rem; font-weight: 600; color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }

  .er-empty { flex-direction: column; align-items: center; gap: 8px; padding: 18px 14px; text-align: center; color: #64748b; font-size: 0.82rem; }
  .btn-crear-inline {
    background: #16a34a; color: #ffffff; border: none; border-radius: 6px;
    padding: 6px 12px; font-size: 0.78rem; font-weight: 700; cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px;
  }
  .btn-crear-inline:hover { background: #15803d; }

  /* TARJETA DE ENTIDAD SELECCIONADA */
  .entidad-selected-card {
    display: flex; align-items: center; justify-content: space-between;
    background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 10px;
    padding: 10px 14px;
  }
  .esc-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .esc-title { display: flex; align-items: center; gap: 8px; font-size: 0.88rem; font-weight: 800; color: #14532d; }
  .text-green { color: #16a34a; }
  .esc-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-size: 0.74rem; color: #64748b; }
  .esc-badge { background: #dcfce7; color: #15803d; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; }
  .esc-badge.gray { background: #f1f5f9; color: #475569; }
  .btn-cambiar-ent {
    background: #ffffff; border: 1px solid #cbd5e1; color: #475569;
    font-size: 0.76rem; font-weight: 700; border-radius: 6px; padding: 5px 10px;
    cursor: pointer; display: inline-flex; align-items: center; gap: 5px;
    transition: all 0.15s; flex-shrink: 0;
  }
  .btn-cambiar-ent:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

  /* GRID */
  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px 16px; width: 100%; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px 16px; width: 100%; }
  .grid-obs { display: grid; grid-template-columns: 1fr 3fr; gap: 14px 16px; width: 100%; align-items: flex-start; }
  .mb-12 { margin-bottom: 12px; }
  .col-span-2 { grid-column: span 2; }
  .full-width { width: 100%; }

  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label { font-size: 0.72rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }
  .field input:not([type="file"]), .field select {
    height: 40px; border: 1.5px solid #cbd5e1; border-radius: 8px;
    padding: 0 12px; font-size: 0.85rem; font-family: inherit; outline: none; background: #ffffff;
    width: 100%; box-sizing: border-box; transition: all 0.2s; color: #1e293b;
  }
  .field textarea {
    border: 1.5px solid #cbd5e1; border-radius: 8px;
    padding: 10px 12px; font-size: 0.85rem; font-family: inherit; outline: none; background: #ffffff;
    width: 100%; box-sizing: border-box; transition: all 0.2s;
    resize: vertical; min-height: 75px; color: #1e293b;
  }
  .field input:focus, .field select:focus, .field textarea:focus {
    border-color: #16a34a; box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.12);
  }

  .btn-cancel {
    background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px;
    padding: 9px 20px; font-size: 0.84rem; font-weight: 700; color: #475569; cursor: pointer;
    transition: all 0.15s;
  }
  .btn-cancel:hover { background: #f1f5f9; color: #1e293b; }
  
  .btn-registrar {
    background: #16a34a; color: #ffffff; border: none; border-radius: 8px;
    padding: 9px 24px; font-size: 0.84rem; font-weight: 800; cursor: pointer;
    display: flex; align-items: center; gap: 8px; transition: background 0.15s;
  }
  .btn-registrar:hover:not(:disabled) { background: #15803d; }
  .btn-registrar:disabled { opacity: 0.65; cursor: not-allowed; }

  .alert-error {
    margin: 0 26px; margin-top: 14px; background: #fef2f2; border: 1px solid #fecaca;
    color: #dc2626; border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; font-weight: 700;
    display: flex; align-items: center; gap: 8px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 0.7s linear infinite; }
</style>
