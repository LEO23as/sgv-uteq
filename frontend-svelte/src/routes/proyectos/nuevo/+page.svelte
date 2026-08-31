<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import MapaSelector from '$lib/MapaSelector.svelte';
  import OdsPicker from '$lib/OdsPicker.svelte';
  import ConvenioModal from '$lib/ConvenioModal.svelte';

  let facultades = $state([]);
  let periodos   = $state([]);
  let carrerasFil = $state([]);
  let ubicaciones = $state([]);

  let paso = $state(1);                 // 1..3
  let proyectoId = $state(null);        // se define al guardar el paso 1
  let saving = $state(false);
  let error  = $state('');

  const PASOS = [
    { n: 1, label: 'Datos del proyecto', icon: 'bi-clipboard-data' },
    { n: 2, label: 'Resolución de aprobación', icon: 'bi-file-earmark-check' },
    { n: 3, label: 'Convenios', icon: 'bi-people' },
  ];

  let form = $state({
    codigo:'', nombre:'', id_periodo_inicio:'', id_facultad:'', id_carrera:'',
    director_nombre:'', director_correo:'', estado:'EN_EJECUCION',
    linea_vinculacion:'', area_conocimiento:'', sub_area_conocimiento:'', programa:'',
    objetivo_general:'', fecha_inicio:'', fecha_fin_planificada:'', ods:'',
    provincia:'', canton:'', parroquia:'', sector:'', latitud:'', longitud:'',
    descripcion:'', observaciones:'', nombre_corto:'',
    presupuesto_planificado:'', terminos_negociacion:'',
  });
  let fotos = $state([]);
  let previews = $state([]);
  let odsSeleccionados = $state([]);   // números de ODS elegidos

  const ESTADOS = ['EN_EJECUCION','PROPUESTO','APROBADO','EN_CIERRE','DETENIDO','FINALIZADO','RECHAZADO'];
  const ESTADOS_LABEL = {
    EN_EJECUCION:'En ejecución',PROPUESTO:'Propuesto',APROBADO:'Aprobado',
    EN_CIERRE:'En cierre',DETENIDO:'Detenido',FINALIZADO:'Finalizado',RECHAZADO:'Rechazado',
  };

  onMount(async () => {
    periodos = await fetchAPI('/api/periodos/');
    const urlParams = new URLSearchParams(window.location.search);
    const pFac = urlParams.get('facultad');
    const pCar = urlParams.get('carrera');
    const pPer = urlParams.get('periodo') || (periodos.find(p => p.activo)?.id_periodo || periodos[0]?.id_periodo);

    if (pPer) {
      form.id_periodo_inicio = String(pPer);
      facultades = await fetchAPI(`/api/facultades-periodo/?periodo=${form.id_periodo_inicio}`);
      if (pFac) {
        form.id_facultad = String(pFac);
        carrerasFil = await fetchAPI(`/api/carreras-periodo/?periodo=${form.id_periodo_inicio}&facultad=${form.id_facultad}`);
        if (pCar) form.id_carrera = String(pCar);
      }
    }
  });

  async function onPeriodoChange() {
    form.id_facultad = ''; form.id_carrera = '';
    facultades = []; carrerasFil = [];
    if (!form.id_periodo_inicio) return;
    facultades = await fetchAPI(`/api/facultades-periodo/?periodo=${form.id_periodo_inicio}`);
  }

  async function onFacultadChange() {
    form.id_carrera = ''; carrerasFil = [];
    if (!form.id_facultad || !form.id_periodo_inicio) return;
    carrerasFil = await fetchAPI(`/api/carreras-periodo/?periodo=${form.id_periodo_inicio}&facultad=${form.id_facultad}`);
  }

  function onFotosChange(e) {
    const files = Array.from(e.target.files);
    fotos = [...fotos, ...files];
    files.forEach(f => {
      const reader = new FileReader();
      reader.onload = (ev) => { previews = [...previews, ev.target.result]; };
      reader.readAsDataURL(f);
    });
  }
  function quitarFoto(idx) {
    fotos = fotos.filter((_, i) => i !== idx);
    previews = previews.filter((_, i) => i !== idx);
  }

  // ── Documentos del portafolio ────────────────────────────────────
  let resolForm = $state({ resolucion_aprobacion:'', fecha_aprobacion:'' });
  let resolFiles = $state([]);
  let planFile  = $state(null);
  let mostrarPlanificacion = $state(false);
  let subiendo  = $state(false);

  function pickResol(e) {
    const files = Array.from(e.target.files);
    resolFiles = [...resolFiles, ...files];
    e.target.value = '';
  }
  function quitarResolFile(i) { resolFiles = resolFiles.filter((_, x) => x !== i); }

  function pickPlan(e)  { planFile  = e.target.files[0] || null; }

  // ── Paso 3: convenio (modal, sin salir del wizard) ───────────────
  let convenioFiles = $state([]);
  let modalConvenioOpen = $state(false);
  let convenioRegistrado = $state(false);
  function pickConvenio(e) {
    const files = Array.from(e.target.files);
    convenioFiles = [...convenioFiles, ...files];
    e.target.value = '';
  }
  function quitarConvenioFile(i) { convenioFiles = convenioFiles.filter((_, x) => x !== i); }
  function onConvenioCreado() { convenioRegistrado = true; }

  async function subirDocs(codigo_tipo, filesArray, extra = {}) {
    const fd = new FormData();
    fd.append('codigo_tipo', codigo_tipo);
    if (Array.isArray(filesArray)) {
      filesArray.forEach(f => fd.append('archivos', f));
    } else if (filesArray) {
      fd.append('archivos', filesArray);
    }
    Object.entries(extra).forEach(([k, v]) => { if (v) fd.append(k, v); });
    const res = await fetch(`/api/proyectos/${proyectoId}/documentos/subir/`, {
      method:'POST', credentials:'include', body: fd,
    });
    if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.error || 'Error al subir'); }
    return res.json();
  }

  async function guardarPaso2() {
    error = '';
    if (resolFiles.length === 0 && !resolForm.resolucion_aprobacion && !resolForm.fecha_aprobacion) { paso = 3; return; }
    subiendo = true;
    try {
      await subirDocs('DOC_01', resolFiles, {
        resolucion_aprobacion: resolForm.resolucion_aprobacion,
        fecha_aprobacion: resolForm.fecha_aprobacion,
      });
      resolFiles = [];
      toast.success('Resolución de aprobación guardada');
      paso = 3;
    } catch (e) { error = e.message; toast.error(e.message); } finally { subiendo = false; }
  }

  async function guardarPaso3() {
    error = '';
    if (convenioFiles.length === 0) { finalizar(); return; }
    subiendo = true;
    try {
      await subirDocs('DOC_03', convenioFiles);
      convenioFiles = [];
      toast.success('Documento(s) de convenio guardados en el portafolio');
      finalizar();
    } catch (e) { error = e.message; toast.error(e.message); } finally { subiendo = false; }
  }

  // ── Paso 1: crear el proyecto ───────────────────────────────────
  async function guardarPaso1() {
    error = '';
    if (!form.codigo || !form.nombre || !form.id_facultad || !form.id_carrera || !form.id_periodo_inicio) {
      error = 'Código, título, período, facultad y carrera son obligatorios.';
      toast.error(error);
      return;
    }
    if (!ubicaciones.length) { error = 'Agrega al menos una ubicación en el mapa.'; toast.error(error); return; }
    if (form.fecha_inicio && form.fecha_fin_planificada && form.fecha_fin_planificada <= form.fecha_inicio) {
      error = 'La fecha de finalización debe ser posterior a la de inicio.'; toast.error(error); return;
    }
    const principal = ubicaciones.find(u => u.es_principal) || ubicaciones[0];
    form.latitud = principal.latitud; form.longitud = principal.longitud;
    form.provincia = principal.provincia || ''; form.canton = principal.canton || '';
    form.parroquia = principal.parroquia || ''; form.sector = principal.sector || '';
    form.ods = odsSeleccionados.map(n => 'ODS ' + n).join(', ');

    saving = true;
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      fd.append('ubicaciones', JSON.stringify(ubicaciones));
      fotos.forEach(f => fd.append('fotos', f));
      const res = await fetch('/api/proyectos/create/', { method:'POST', credentials:'include', body: fd });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al crear proyecto'; toast.error(error); return; }
      proyectoId = data.id_proyecto;
      if (planFile) {
        try { await subirDoc('DOC_02', planFile); }
        catch (e) { toast.error('Proyecto creado, pero falló la planificación: ' + e.message); }
      }
      toast.success('Proyecto creado. Ahora sube la resolución de aprobación.');
      paso = 2;
    } catch { error = 'Error de conexión'; toast.error(error); }
    finally { saving = false; }
  }

  function finalizar() { goto('/proyectos/' + proyectoId); }
</script>

<svelte:head><title>Nuevo Proyecto — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/proyectos">Proyectos</a>
    <span class="sep">/</span>
    <span class="current">Nuevo proyecto</span>
  </nav>
</div>

<div class="form-wrap">
  <div class="form-card">
    <!-- INDICADOR DE PASOS -->
    <div class="stepper">
      {#each PASOS as p}
        <div class="step" class:activo={paso === p.n} class:hecho={paso > p.n}>
          <div class="step-circle">
            {#if paso > p.n}<i class="bi bi-check-lg"></i>{:else}{p.n}{/if}
          </div>
          <span class="step-label">{p.label}</span>
        </div>
        {#if p.n < 3}<div class="step-line" class:hecho={paso > p.n}></div>{/if}
      {/each}
    </div>
    <div class="stepper-divider"></div>

    {#if error}<div class="alert-error">{error}</div>{/if}

    <!-- ══════════ PASO 1: FICHA ══════════ -->
    {#if paso === 1}
      <h2 class="form-title"><i class="bi bi-clipboard-data"></i> Datos del proyecto</h2>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-card-text"></i> Identificación</h4>
        <div class="grid-row">
          <div class="field col-12">
            <label>Título del proyecto *</label>
            <input class="input-titulo" bind:value={form.nombre} placeholder="Implementación de huertos productivos de plantas aromáticas…" />
          </div>
          <div class="field col-4">
            <label>Código *</label>
            <input bind:value={form.codigo} placeholder="PVSUTEQ-FCAP-02" />
            <small>Formato: PVSUTEQ-[COD_FAC]-[NUM]</small>
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-diagram-3"></i> Clasificación</h4>
        <div class="grid-2">
          <div class="field"><label>Línea de investigación</label><input bind:value={form.linea_vinculacion} placeholder="Agricultura, Silvicultura y Producción animal" /></div>
          <div class="field"><label>Programa</label><input bind:value={form.programa} placeholder="Gestión de proyectos de vinculación con la sociedad" /></div>
          <div class="field"><label>Campo amplio</label><input bind:value={form.area_conocimiento} placeholder="Agricultura, Silvicultura, Pesca y Veterinaria" /></div>
          <div class="field"><label>Campo específico</label><input bind:value={form.sub_area_conocimiento} placeholder="Agricultura" /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-mortarboard"></i> Datos académicos y responsables</h4>
        <div class="grid-3 mb-12">
          <div class="field">
            <label>Período *</label>
            <select bind:value={form.id_periodo_inicio} onchange={onPeriodoChange}>
              <option value="">— Seleccionar —</option>
              {#each periodos as p}<option value={p.id_periodo}>{p.codigo || p.nombre}</option>{/each}
            </select>
            <small>Define la estructura histórica</small>
          </div>
          <div class="field">
            <label>Facultad *</label>
            <select bind:value={form.id_facultad} onchange={onFacultadChange} disabled={!form.id_periodo_inicio}>
              <option value="">{form.id_periodo_inicio ? '— Seleccionar —' : '— Elija período primero —'}</option>
              {#each facultades as f}
                <option value={f.id_facultad}>{f.nombre} ({f.codigo})</option>
              {/each}
            </select>
          </div>
          <div class="field">
            <label>Carrera *</label>
            <select bind:value={form.id_carrera} disabled={!carrerasFil.length}>
              <option value="">— Seleccionar facultad primero —</option>
              {#each carrerasFil as c}<option value={c.id_carrera}>{c.nombre}</option>{/each}
            </select>
          </div>
        </div>
        <div class="grid-3">
          <div class="field"><label>Director del proyecto</label><input bind:value={form.director_nombre} placeholder="Ing. Moisés Menace, MSc." /></div>
          <div class="field"><label>Correo del director</label><input type="email" bind:value={form.director_correo} placeholder="mmenace@uteq.edu.ec" /></div>
          <div class="field">
            <label>Estado *</label>
            <select bind:value={form.estado}>{#each ESTADOS as e}<option value={e}>{ESTADOS_LABEL[e]}</option>{/each}</select>
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-calendar3"></i> Objetivo y fechas</h4>
        <div class="grid-row mb-12">
          <div class="field col-12"><label>Objetivo general</label><textarea rows="2" bind:value={form.objetivo_general} placeholder="Elaborar abonos orgánicos para producir huertos hortícolas…"></textarea></div>
        </div>
        <div class="grid-2">
          <div class="field"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
          <div class="field"><label>Fecha de finalización</label><input type="date" bind:value={form.fecha_fin_planificada} /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-cash-coin"></i> Presupuesto y negociación</h4>
        <div class="grid-obs">
          <div class="field">
            <label>Presupuesto planificado (USD)</label>
            <input type="number" min="0" step="0.01" bind:value={form.presupuesto_planificado} placeholder="0.00" />
          </div>
          <div class="field">
            <label>Términos de negociación</label>
            <textarea rows="2" bind:value={form.terminos_negociacion} placeholder="Condiciones acordadas con la entidad cooperante, aportes, contrapartes…"></textarea>
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-list-task"></i> Planificación de actividades <span class="sec-note">— opcional, puedes subirla después</span></h4>
        {#if planFile}
          <label class="drop-zone doc">
            <input type="file" accept="application/pdf,image/*" onchange={pickPlan} />
            <i class="bi bi-file-earmark-arrow-up"></i>
            <span>{planFile.name}</span>
            <small>PDF o imagen — clic para reemplazar</small>
          </label>
        {:else if mostrarPlanificacion}
          <label class="drop-zone doc">
            <input type="file" accept="application/pdf,image/*" onchange={pickPlan} />
            <i class="bi bi-file-earmark-arrow-up"></i>
            <span>Clic para subir el PDF de planificación</span>
            <small>PDF o imagen</small>
          </label>
        {:else}
          <button type="button" class="btn-add-inline" onclick={() => mostrarPlanificacion = true}>
            <i class="bi bi-plus-lg"></i> Agregar planificación (PDF)
          </button>
        {/if}
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-globe"></i> Objetivos de Desarrollo Sostenible (ODS) <span class="sec-note">— marca los que atiende el proyecto</span></h4>
        <OdsPicker bind:seleccionados={odsSeleccionados} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-geo-alt"></i> Ubicación geográfica <span class="sec-note">— busca o marca en el mapa dónde se ejecuta (uno o varios lugares)</span></h4>
        <MapaSelector bind:ubicaciones={ubicaciones} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-images"></i> Evidencia fotográfica</h4>
        <label class="drop-zone">
          <input type="file" accept="image/*" multiple onchange={onFotosChange} />
          <i class="bi bi-cloud-arrow-up"></i>
          <span>Clic para subir fotos del proyecto</span>
          <small>JPG, PNG — múltiples archivos</small>
        </label>
        {#if previews.length}
          <div class="foto-previews">
            {#each previews as src, i}
              <div class="foto-prev-item"><img {src} alt="preview" /><button onclick={() => quitarFoto(i)}><i class="bi bi-x"></i></button></div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="form-actions">
        <a href="/proyectos" class="btn-cancel">Cancelar</a>
        <button class="btn-save" onclick={guardarPaso1} disabled={saving}>
          {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- ══════════ PASO 2: RESOLUCIÓN DE APROBACIÓN ══════════ -->
    {:else if paso === 2}
      <h2 class="form-title"><i class="bi bi-file-earmark-check"></i> Resolución de aprobación</h2>
      <p class="paso-desc">Sube los documentos o PDF(s) de la resolución con la que el Consejo Directivo aprobó el proyecto (DOC_01). Puedes subir uno o varios archivos.</p>

      <div class="sec">
        <div class="grid-row">
          <div class="field col-8"><label>Referencia de la resolución</label><input bind:value={resolForm.resolucion_aprobacion} placeholder="Consejo Directivo FCA — Sesión ordinaria 04/03/2021, Resolución OCTAVA" /></div>
          <div class="field col-4"><label>Fecha de aprobación</label><input type="date" bind:value={resolForm.fecha_aprobacion} /></div>
        </div>

        {#if resolFiles.length}
          <div class="pending-files-list">
            <span class="pending-title"><i class="bi bi-cloud-arrow-up"></i> Archivos seleccionados para subir ({resolFiles.length}):</span>
            {#each resolFiles as f, i}
              <div class="pending-file-item">
                <span><i class="bi bi-file-earmark"></i> {f.name} ({(f.size/1024).toFixed(1)} KB)</span>
                <button type="button" class="btn-quitar-file" onclick={() => quitarResolFile(i)} title="Quitar archivo"><i class="bi bi-x-lg"></i></button>
              </div>
            {/each}
          </div>
        {/if}

        <label class="drop-zone doc">
          <input type="file" multiple accept="application/pdf,image/*,.doc,.docx" onchange={pickResol} />
          <i class="bi bi-file-earmark-arrow-up"></i>
          <span>Subir documentos de resolución (permite varios)</span>
          <small>Haz clic o arrastra para seleccionar archivos PDF, Word o imágenes</small>
        </label>
      </div>

      <div class="form-actions between">
        <button class="btn-cancel" onclick={() => paso = 3}>Omitir por ahora</button>
        <button class="btn-save" onclick={guardarPaso2} disabled={subiendo}>
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Subiendo…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- ══════════ PASO 3: CONVENIOS ══════════ -->
    {:else}
      <h2 class="form-title"><i class="bi bi-people"></i> Convenios</h2>
      <p class="paso-desc">
        Registra el convenio con la entidad cooperante de este proyecto (buscar o crear la entidad,
        fechas, memorando) y sube aquí los documentos del convenio firmado (DOC_03). Puedes subir uno o varios archivos.
      </p>

      <div class="sec">
        {#if convenioRegistrado}
          <div class="convenio-ok"><i class="bi bi-check-circle-fill"></i> Convenio registrado</div>
        {:else}
          <button type="button" class="btn-side-add-lg" onclick={() => modalConvenioOpen = true}>
            <i class="bi bi-plus-lg"></i> Registrar convenio y entidad cooperante
          </button>
          <small class="pp-hint">Se abre en una ventana flotante, sin salir de este formulario.</small>
        {/if}
      </div>

      {#if convenioFiles.length}
        <div class="pending-files-list">
          <span class="pending-title"><i class="bi bi-cloud-arrow-up"></i> Archivos seleccionados para subir ({convenioFiles.length}):</span>
          {#each convenioFiles as f, i}
            <div class="pending-file-item">
              <span><i class="bi bi-file-earmark"></i> {f.name} ({(f.size/1024).toFixed(1)} KB)</span>
              <button type="button" class="btn-quitar-file" onclick={() => quitarConvenioFile(i)} title="Quitar archivo"><i class="bi bi-x-lg"></i></button>
            </div>
          {/each}
        </div>
      {/if}

      <div class="sec">
        <h4 class="sec-hdr">Documentos del convenio (permite varios)</h4>
        <label class="drop-zone doc">
          <input type="file" multiple accept="application/pdf,image/*,.doc,.docx" onchange={pickConvenio} />
          <i class="bi bi-file-earmark-arrow-up"></i>
          <span>Subir documentos del convenio (permite varios)</span>
          <small>Haz clic o arrastra para seleccionar archivos PDF, Word o imágenes</small>
        </label>
      </div>

      <div class="form-actions between">
        <button class="btn-cancel" onclick={() => paso = 2}><i class="bi bi-arrow-left"></i> Atrás</button>
        <button class="btn-save" onclick={guardarPaso3} disabled={subiendo}>
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Finalizar y ver el proyecto <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>
    {/if}
  </div>
</div>

<ConvenioModal bind:open={modalConvenioOpen} proyectoId={proyectoId} onCreated={onConvenioCreado} />

<style>
  .sec-note { font-size:.72rem; font-weight:600; color:var(--gris); }

  /* Stepper */
  .stepper { display:flex; align-items:center; justify-content:space-between; gap:0; margin:0 0 20px; width:100%; padding:0; box-sizing:border-box; }
  .stepper-divider { height:1px; background:#f0f0f0; margin-bottom:24px; width:100%; }
  .step { display:flex; flex-direction:column; align-items:center; gap:6px; flex-shrink:0; }
  .step-circle { width:34px; height:34px; border-radius:50%; background:#eee; color:#999; font-weight:800; font-size:.9rem;
    display:flex; align-items:center; justify-content:center; border:2px solid #e0e0e0; transition:all .2s; }
  .step-label { font-size:.72rem; font-weight:700; color:#aaa; text-align:center; max-width:96px; line-height:1.2; }
  .step.activo .step-circle { background:var(--verde); color:#fff; border-color:var(--verde); }
  .step.activo .step-label { color:var(--verde); }
  .step.hecho .step-circle { background:var(--verde-claro); color:var(--verde); border-color:var(--verde); }
  .step.hecho .step-label { color:var(--verde); }
  .step-line { flex:1; height:2px; background:#e0e0e0; margin:0 6px; margin-bottom:22px; min-width:24px; }
  .step-line.hecho { background:var(--verde); }

  .btn-save i { font-size:.9rem; }
  .form-actions.center { justify-content:center; }
  .form-actions.between { justify-content:space-between; }

  .paso-desc { font-size:.86rem; color:#666; line-height:1.5; margin:-4px 0 16px; }
  .drop-zone.doc { margin-top:12px; }

  .pending-files-list {
    display: flex; flex-direction: column; gap: 6px; margin: 10px 0;
    background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px 12px;
  }
  .pending-title { font-size: 0.74rem; font-weight: 800; color: #15803d; }
  .pending-file-item {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 0.8rem; font-weight: 600; color: #1e293b;
    background: #ffffff; border: 1px solid #bbf7d0; border-radius: 6px; padding: 6px 10px;
  }
  .btn-quitar-file {
    background: none; border: none; color: #ef4444; cursor: pointer;
    font-size: 0.8rem; padding: 2px 6px; border-radius: 4px;
  }
  .btn-quitar-file:hover { background: #fee2e2; }

  .btn-side-add-lg {
    display:flex; align-items:center; justify-content:center; gap:8px;
    background:var(--verde); color:#fff; border-radius:10px;
    padding:12px 18px; font-size:.9rem; font-weight:800; text-decoration:none;
    transition:opacity .2s;
  }
  .btn-side-add-lg:hover { opacity:.9; }
  .pp-hint { display:block; margin-top:8px; font-size:.76rem; color:var(--gris); }

  .convenio-ok {
    display:flex; align-items:center; gap:8px;
    background:var(--verde-claro); color:var(--verde); border-radius:10px;
    padding:12px 18px; font-size:.86rem; font-weight:800;
  }

  .input-titulo { font-size:1.15rem; font-weight:700; padding:12px 14px; }

  .btn-add-inline {
    display:inline-flex; align-items:center; gap:6px;
    background:var(--verde-claro); color:var(--verde); border:none; border-radius:8px;
    padding:9px 16px; font-size:.84rem; font-weight:800; cursor:pointer; font-family:inherit;
    transition:background .2s;
  }
  .btn-add-inline:hover { background:#c8e6b0; }
</style>
