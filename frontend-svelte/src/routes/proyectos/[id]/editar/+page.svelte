<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import MapaSelector from '$lib/MapaSelector.svelte';
  import OdsPicker from '$lib/OdsPicker.svelte';
  import ConvenioModal from '$lib/ConvenioModal.svelte';

  const id = $derived($page.params.id);

  let facultades = $state([]);
  let carrerasFil = $state([]);
  let periodos = $state([]);
  let fotosExist = $state([]);
  let ubicaciones = $state([]);
  let odsSeleccionados = $state([]);
  let documentos = $state([]);            // documentos ya subidos
  let loading = $state(true);
  let saving = $state(false);
  let subiendo = $state(false);
  let error = $state('');

  let paso = $state(1);

  const PASOS = [
    { n: 1, label: 'Datos del proyecto', icon: 'bi-clipboard-data' },
    { n: 2, label: 'Resolución de aprobación', icon: 'bi-file-earmark-check' },
    { n: 3, label: 'Convenios', icon: 'bi-people' },
  ];

  let form = $state({
    codigo:'', nombre:'', nombre_corto:'', id_facultad:'', id_carrera:'', id_periodo_inicio:'',
    director_nombre:'', director_correo:'', estado:'EN_EJECUCION',
    linea_vinculacion:'', programa:'', area_conocimiento:'', sub_area_conocimiento:'',
    objetivo_general:'', fecha_inicio:'', fecha_fin_planificada:'', ods:'',
    provincia:'', canton:'', parroquia:'', sector:'', latitud:'', longitud:'',
    descripcion:'', observaciones:'', presupuesto_planificado:'', terminos_negociacion:'',
  });
  let proyecto = $state(null);
  let nuevasFotos = $state([]);
  let previews = $state([]);
  let resolForm = $state({ resolucion_aprobacion:'', fecha_aprobacion:'' });
  let resolFiles = $state([]);
  let planFile  = $state(null);
  let mostrarPlanificacion = $state(false);
  let convenioFiles = $state([]);
  let modalConvenioOpen = $state(false);
  let convenioRegistrado = $state(false);
  function onConvenioCreado() { convenioRegistrado = true; }

  const ESTADOS = ['EN_EJECUCION','PROPUESTO','APROBADO','EN_CIERRE','DETENIDO','FINALIZADO','RECHAZADO'];
  const ESTADOS_LABEL = {
    EN_EJECUCION:'En ejecución',PROPUESTO:'Propuesto',APROBADO:'Aprobado',
    EN_CIERRE:'En cierre',DETENIDO:'Detenido',FINALIZADO:'Finalizado',RECHAZADO:'Rechazado',
  };

  onMount(async () => {
    try {
      const [pers, data] = await Promise.all([
        fetchAPI('/api/periodos/'),
        fetchAPI(`/api/proyectos/${id}/detalle/`),
      ]);
      periodos = pers;
      proyecto = data;
      Object.keys(form).forEach(k => {
        if (data[k] !== undefined && data[k] !== null) form[k] = data[k];
      });
      if (data.ods) {
        odsSeleccionados = data.ods.split(',').map(s => {
          const m = s.trim().match(/\d+/);
          return m ? parseInt(m[0]) : null;
        }).filter(Boolean);
      }
      ubicaciones = data.ubicaciones || [];
      fotosExist = data.fotos || [];
      if (data.resolucion_aprobacion) resolForm.resolucion_aprobacion = data.resolucion_aprobacion;
      if (data.fecha_aprobacion) resolForm.fecha_aprobacion = data.fecha_aprobacion;

      if (form.id_periodo_inicio) {
        facultades = await fetchAPI(`/api/facultades-periodo/?periodo=${form.id_periodo_inicio}`);
        if (form.id_facultad)
          carrerasFil = await fetchAPI(`/api/carreras-periodo/?periodo=${form.id_periodo_inicio}&facultad=${form.id_facultad}`);
      }
      await cargarDocumentos();
    } catch { toast.error('No se pudo cargar el proyecto'); }
    finally { loading = false; }
  });

  async function cargarDocumentos() {
    try { documentos = await fetchAPI(`/api/proyectos/${id}/documentos/`); } catch { documentos = []; }
  }
  const docsPorTipo = (codigo) => documentos.filter(d => d.codigo_tipo === codigo || d.tipo === codigo);
  const docPorTipo = (codigo) => documentos.find(d => d.codigo_tipo === codigo || d.tipo === codigo);

  async function onPeriodoChange() {
    form.id_facultad = ''; form.id_carrera = ''; facultades = []; carrerasFil = [];
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
    nuevasFotos = [...nuevasFotos, ...files];
    files.forEach(f => { const r = new FileReader(); r.onload = ev => previews = [...previews, ev.target.result]; r.readAsDataURL(f); });
  }
  function quitarNueva(i) { nuevasFotos = nuevasFotos.filter((_,x)=>x!==i); previews = previews.filter((_,x)=>x!==i); }
  async function eliminarFotoExist(idFoto) {
    try { await fetch(`/api/proyectos/fotos/${idFoto}/`, { method:'DELETE', credentials:'include' });
      fotosExist = fotosExist.filter(f => f.id !== idFoto); toast.success('Foto eliminada');
    } catch { toast.error('No se pudo eliminar la foto'); }
  }

  function pickResol(e){
    const files = Array.from(e.target.files);
    resolFiles = [...resolFiles, ...files];
    e.target.value = '';
  }
  function quitarResolFile(i) { resolFiles = resolFiles.filter((_, x) => x !== i); }

  function pickPlan(e){ planFile = e.target.files[0] || null; }

  function pickConvenio(e){
    const files = Array.from(e.target.files);
    convenioFiles = [...convenioFiles, ...files];
    e.target.value = '';
  }
  function quitarConvenioFile(i) { convenioFiles = convenioFiles.filter((_, x) => x !== i); }

  async function subirDocs(codigo_tipo, filesArray, extra = {}) {
    const fd = new FormData();
    fd.append('codigo_tipo', codigo_tipo);
    if (Array.isArray(filesArray)) {
      filesArray.forEach(f => fd.append('archivos', f));
    } else if (filesArray) {
      fd.append('archivos', filesArray);
    }
    Object.entries(extra).forEach(([k,v]) => { if (v) fd.append(k, v); });
    const res = await fetch(`/api/proyectos/${id}/documentos/subir/`, { method:'POST', credentials:'include', body: fd });
    if (!res.ok) { const d = await res.json().catch(()=>({})); throw new Error(d.error || 'Error al subir'); }
    return res.json();
  }

  async function guardarPaso2() {
    error = '';
    if (resolFiles.length === 0 && !resolForm.resolucion_aprobacion && !resolForm.fecha_aprobacion) { paso = 3; return; }
    subiendo = true;
    try {
      await subirDocs('DOC_01', resolFiles, { resolucion_aprobacion: resolForm.resolucion_aprobacion, fecha_aprobacion: resolForm.fecha_aprobacion });
      resolFiles = []; await cargarDocumentos();
      toast.success('Resolución y documento(s) guardados');
      paso = 3;
    } catch (e) { error = e.message; toast.error(e.message); } finally { subiendo = false; }
  }

  async function guardarPaso3() {
    error = '';
    if (convenioFiles.length === 0) { finalizar(); return; }
    subiendo = true;
    try {
      await subirDocs('DOC_03', convenioFiles);
      convenioFiles = []; await cargarDocumentos();
      toast.success('Documento(s) de convenio guardados');
      finalizar();
    } catch (e) { error = e.message; toast.error(e.message); } finally { subiendo = false; }
  }

  // ── Paso 1: guardar la ficha ────────────────────────────────────
  async function guardarPaso1() {
    error = '';
    if (!form.codigo || !form.nombre || !form.id_facultad || !form.id_carrera || !form.id_periodo_inicio) {
      error = 'Código, título, período, facultad y carrera son obligatorios.'; toast.error(error); return;
    }
    if (form.fecha_inicio && form.fecha_fin_planificada && form.fecha_fin_planificada <= form.fecha_inicio) {
      error = 'La fecha de finalización debe ser posterior a la de inicio.'; toast.error(error); return;
    }
    if (ubicaciones.length) {
      const pr = ubicaciones.find(u => u.es_principal) || ubicaciones[0];
      form.latitud = pr.latitud; form.longitud = pr.longitud;
      form.provincia = pr.provincia || ''; form.canton = pr.canton || '';
      form.parroquia = pr.parroquia || ''; form.sector = pr.sector || '';
    }
    form.ods = odsSeleccionados.map(n => 'ODS ' + n).join(', ');
    saving = true;
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      fd.append('ubicaciones', JSON.stringify(ubicaciones));
      nuevasFotos.forEach(f => fd.append('fotos', f));
      const res = await fetch(`/api/proyectos/${id}/edit/`, { method:'POST', credentials:'include', body:fd });
      const data = await res.json();
      if (!res.ok) { error = data.error || 'Error al guardar'; toast.error(error); return; }
      nuevasFotos = []; previews = [];
      if (planFile) {
        try { await subirDocs('DOC_02', [planFile]); planFile = null; await cargarDocumentos(); }
        catch (e) { toast.error('Guardado, pero falló la planificación: ' + e.message); }
      }
      toast.success('Datos del proyecto guardados');
      paso = 2;
    } catch { error = 'Error de conexión'; toast.error(error); }
    finally { saving = false; }
  }

  async function eliminarDoc(idDoc) {
    try { await fetch(`/api/documentos/${idDoc}/`, { method:'DELETE', credentials:'include' });
      await cargarDocumentos(); toast.success('Documento eliminado');
    } catch { toast.error('No se pudo eliminar'); }
  }

  function finalizar() { toast.success('Cambios guardados'); goto('/proyectos/' + id); }
</script>

<svelte:head><title>Editar Proyecto — SGV</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/proyectos">Proyectos</a>
    <span class="sep">/</span>
    <a href="/proyectos/{id}">Detalle</a>
    <span class="sep">/</span>
    <span class="current">Editar</span>
  </nav>
</div>

{#if loading}
  <div class="loading-wrap"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
{:else}
<div class="form-wrap">
  <div class="form-card">
    <!-- INDICADOR DE PASOS -->
    <div class="stepper">
      {#each PASOS as p}
        <button class="step" class:activo={paso === p.n} class:hecho={paso > p.n} onclick={() => paso = p.n}>
          <div class="step-circle">{#if paso > p.n}<i class="bi bi-check-lg"></i>{:else}{p.n}{/if}</div>
          <span class="step-label">{p.label}</span>
        </button>
        {#if p.n < 3}<div class="step-line" class:hecho={paso > p.n}></div>{/if}
      {/each}
    </div>
    <div class="stepper-divider"></div>

    {#if error}<div class="alert-error">{error}</div>{/if}

    <!-- PASO 1: FICHA -->
    {#if paso === 1}
      <h2 class="form-title"><i class="bi bi-pencil-square"></i> Datos del proyecto</h2>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-card-text"></i> Identificación</h4>
        <div class="grid-row">
          <div class="field col-12"><label>Título del proyecto *</label><input class="input-titulo" bind:value={form.nombre} placeholder="Título completo del proyecto de vinculación..." /></div>
          <div class="field col-4"><label>Código *</label><input bind:value={form.codigo} placeholder="Ej. PVSUTFQ-FCAF-01" /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-diagram-3"></i> Clasificación</h4>
        <div class="grid-2">
          <div class="field"><label>Línea de investigación</label><input bind:value={form.linea_vinculacion} placeholder="Ej. Desarrollo e Innovación de Procesos" /></div>
          <div class="field"><label>Programa</label><input bind:value={form.programa} placeholder="Ej. Gestión de proyectos de vinculación..." /></div>
          <div class="field"><label>Campo amplio</label><input bind:value={form.area_conocimiento} placeholder="Ej. Agricultura, silvicultura, pesca y veterinaria" /></div>
          <div class="field"><label>Campo específico</label><input bind:value={form.sub_area_conocimiento} placeholder="Ej. Agricultura" /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-mortarboard"></i> Datos académicos y responsables</h4>
        <div class="grid-3 mb-12">
          <div class="field">
            <label>Período *</label>
            <select bind:value={form.id_periodo_inicio} onchange={onPeriodoChange}>
              <option value="">— Seleccionar —</option>
              {#each periodos as p}<option value={String(p.id_periodo)}>{p.codigo || p.nombre}</option>{/each}
            </select>
          </div>
          <div class="field">
            <label>Facultad *</label>
            <select bind:value={form.id_facultad} onchange={onFacultadChange} disabled={!form.id_periodo_inicio}>
              <option value="">— Seleccionar —</option>
              {#each facultades as f}<option value={String(f.id_facultad)}>{f.nombre} ({f.codigo})</option>{/each}
            </select>
          </div>
          <div class="field">
            <label>Carrera *</label>
            <select bind:value={form.id_carrera} disabled={!carrerasFil.length}>
              <option value="">— Seleccionar —</option>
              {#each carrerasFil as c}<option value={String(c.id_carrera)}>{c.nombre}</option>{/each}
            </select>
          </div>
        </div>
        <div class="grid-3">
          <div class="field"><label>Director del proyecto</label><input bind:value={form.director_nombre} placeholder="Nombre completo del director..." /></div>
          <div class="field"><label>Correo del director</label><input type="email" bind:value={form.director_correo} placeholder="director@uteq.edu.ec" /></div>
          <div class="field">
            <label>Estado del proyecto *</label>
            <select bind:value={form.estado}>{#each ESTADOS as e}<option value={e}>{ESTADOS_LABEL[e]}</option>{/each}</select>
          </div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-calendar3"></i> Objetivo y fechas</h4>
        <div class="grid-row mb-12">
          <div class="field col-12"><label>Objetivo general</label><textarea rows="2" bind:value={form.objetivo_general} placeholder="Describa el objetivo general del proyecto..."></textarea></div>
        </div>
        <div class="grid-2">
          <div class="field"><label>Fecha de inicio</label><input type="date" bind:value={form.fecha_inicio} /></div>
          <div class="field"><label>Fecha de finalización planificada</label><input type="date" bind:value={form.fecha_fin_planificada} /></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-cash-coin"></i> Presupuesto y negociación</h4>
        <div class="grid-obs">
          <div class="field"><label>Presupuesto planificado (USD)</label><input type="number" min="0" step="0.01" bind:value={form.presupuesto_planificado} placeholder="0.00" /></div>
          <div class="field"><label>Términos de negociación</label><textarea rows="2" bind:value={form.terminos_negociacion} placeholder="Detalles de negociación o acuerdos..."></textarea></div>
        </div>
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-list-task"></i> Planificación de actividades <span class="sec-note">— opcional</span></h4>
        {#if docPorTipo('DOC_02')}
          <div class="doc-existe">
            <i class="bi bi-file-earmark-pdf"></i>
            <a href={docPorTipo('DOC_02').url} target="_blank">{docPorTipo('DOC_02').nombre}</a>
            <span class="doc-kb">{docPorTipo('DOC_02').tamanio_kb} KB</span>
            <button class="doc-del" onclick={() => eliminarDoc(docPorTipo('DOC_02').id)} title="Eliminar"><i class="bi bi-trash"></i></button>
          </div>
        {/if}
        {#if planFile || docPorTipo('DOC_02') || mostrarPlanificacion}
          <label class="drop-zone doc">
            <input type="file" accept="application/pdf,image/*" onchange={pickPlan} />
            <i class="bi bi-file-earmark-arrow-up"></i>
            <span>{planFile ? planFile.name : (docPorTipo('DOC_02') ? 'Reemplazar el PDF' : 'Clic para subir el PDF de planificación')}</span>
            <small>PDF o imagen</small>
          </label>
        {:else}
          <button type="button" class="btn-add-inline" onclick={() => mostrarPlanificacion = true}>
            <i class="bi bi-plus-lg"></i> Agregar planificación (PDF)
          </button>
        {/if}
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-globe"></i> Objetivos de Desarrollo Sostenible (ODS)</h4>
        <OdsPicker bind:seleccionados={odsSeleccionados} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-geo-alt"></i> Ubicación geográfica <span class="sec-note">— busca o marca en el mapa (uno o varios lugares)</span></h4>
        <MapaSelector bind:ubicaciones={ubicaciones} />
      </div>

      <div class="sec">
        <h4 class="sec-hdr"><i class="bi bi-images"></i> Fotografías del proyecto</h4>
        {#if fotosExist.length}
          <div class="fotos-existentes">
            {#each fotosExist as f}
              <div class="foto-exist"><img src={f.url} alt={f.titulo} /><button onclick={() => eliminarFotoExist(f.id)}><i class="bi bi-x"></i></button></div>
            {/each}
          </div>
        {/if}
        <label class="drop-zone">
          <input type="file" accept="image/*" multiple onchange={onFotosChange} />
          <i class="bi bi-cloud-arrow-up"></i><span>Agregar más fotos</span><small>JPG, PNG</small>
        </label>
        {#if previews.length}
          <div class="foto-previews">
            {#each previews as src, i}<div class="foto-prev-item"><img {src} alt="preview" /><button onclick={() => quitarNueva(i)}><i class="bi bi-x"></i></button></div>{/each}
          </div>
        {/if}
      </div>

      <div class="form-actions between">
        <a href="/proyectos/{id}" class="btn-cancel">Cancelar</a>
        <button class="btn-save" onclick={guardarPaso1} disabled={saving}>
          {#if saving}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- PASO 2: RESOLUCIÓN -->
    {:else if paso === 2}
      <h2 class="form-title"><i class="bi bi-file-earmark-check"></i> Resolución de aprobación</h2>
      <p class="paso-desc">Datos y documentos de la resolución que aprobó el proyecto (DOC_01). Puedes subir uno o varios archivos.</p>
      
      {#if docsPorTipo('DOC_01').length}
        <div class="docs-list-box">
          <span class="docs-list-title"><i class="bi bi-folder-check"></i> Documentos de resolución guardados ({docsPorTipo('DOC_01').length}):</span>
          {#each docsPorTipo('DOC_01') as doc}
            <div class="doc-existe">
              <i class="bi bi-file-earmark-pdf"></i>
              <a href={doc.url} target="_blank">{doc.nombre}</a>
              <span class="doc-kb">{doc.tamanio_kb} KB</span>
              <button type="button" class="doc-del" onclick={() => eliminarDoc(doc.id)} title="Eliminar"><i class="bi bi-trash"></i></button>
            </div>
          {/each}
        </div>
      {/if}

      <div class="sec">
        <div class="grid-row">
          <div class="field col-8"><label>Referencia de la resolución</label><input bind:value={resolForm.resolucion_aprobacion} placeholder="Consejo Directivo FCA — Sesión 04/03/2021, Res. OCTAVA" /></div>
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
          <span>Subir documentos de la resolución (permite varios)</span>
          <small>Haz clic o arrastra para seleccionar archivos PDF, Word o imágenes</small>
        </label>
      </div>

      <div class="form-actions between">
        <button class="btn-cancel" onclick={() => paso = 1}><i class="bi bi-arrow-left"></i> Atrás</button>
        <button class="btn-save" onclick={guardarPaso2} disabled={subiendo}>
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Guardar y continuar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>

    <!-- PASO 3: CONVENIOS -->
    {:else}
      <h2 class="form-title"><i class="bi bi-people"></i> Convenios</h2>
      <p class="paso-desc">Registra el convenio con la entidad cooperante y sube aquí los documentos del convenio (DOC_03). Puedes subir uno o varios archivos.</p>

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

      {#if docsPorTipo('DOC_03').length}
        <div class="docs-list-box">
          <span class="docs-list-title"><i class="bi bi-folder-check"></i> Documentos de convenio guardados ({docsPorTipo('DOC_03').length}):</span>
          {#each docsPorTipo('DOC_03') as doc}
            <div class="doc-existe">
              <i class="bi bi-file-earmark-pdf"></i>
              <a href={doc.url} target="_blank">{doc.nombre}</a>
              <span class="doc-kb">{doc.tamanio_kb} KB</span>
              <button type="button" class="doc-del" onclick={() => eliminarDoc(doc.id)} title="Eliminar"><i class="bi bi-trash"></i></button>
            </div>
          {/each}
        </div>
      {/if}

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
          {#if subiendo}<i class="bi bi-arrow-repeat spin"></i> Guardando…{:else}Finalizar <i class="bi bi-arrow-right"></i>{/if}
        </button>
      </div>
    {/if}
  </div>
</div>
{/if}

<ConvenioModal bind:open={modalConvenioOpen} proyectoId={id} onCreated={onConvenioCreado} />

<style>
  .sec-note { font-size:.72rem; font-weight:600; color:var(--gris); }
  .loading-wrap { display:flex;align-items:center;gap:10px;color:var(--gris);font-weight:600;padding:40px;justify-content:center; }

  .stepper { display:flex; align-items:center; justify-content:space-between; margin:0 0 20px; width:100%; padding:0; box-sizing:border-box; }
  .stepper-divider { height:1px; background:#f0f0f0; margin-bottom:24px; width:100%; }
  .step { display:flex; flex-direction:column; align-items:center; gap:6px; flex-shrink:0; background:none; border:none; cursor:pointer; font-family:inherit; }
  .step-circle { width:34px; height:34px; border-radius:50%; background:#eee; color:#999; font-weight:800; font-size:.9rem;
    display:flex; align-items:center; justify-content:center; border:2px solid #e0e0e0; transition:all .2s; }
  .step-label { font-size:.72rem; font-weight:700; color:#aaa; text-align:center; max-width:96px; line-height:1.2; }
  .step.activo .step-circle { background:var(--verde); color:#fff; border-color:var(--verde); }
  .step.activo .step-label { color:var(--verde); }
  .step.hecho .step-circle { background:var(--verde-claro); color:var(--verde); border-color:var(--verde); }
  .step.hecho .step-label { color:var(--verde); }
  .step-line { flex:1; height:2px; background:#e0e0e0; margin:0 6px 22px; min-width:24px; }
  .step-line.hecho { background:var(--verde); }

  .form-actions.between { justify-content:space-between; }
  .form-actions.center { justify-content:center; gap:12px; }
  .btn-save i, .btn-cancel i { font-size:.9rem; }
  .paso-desc { font-size:.86rem; color:#666; line-height:1.5; margin:-4px 0 14px; }
  .drop-zone.doc { margin-top:12px; }

  .docs-list-box {
    display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px;
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px;
  }
  .docs-list-title {
    font-size: 0.76rem; font-weight: 800; color: #475569; margin-bottom: 4px;
    display: flex; align-items: center; gap: 6px;
  }

  .doc-existe { display:flex; align-items:center; gap:10px; background:#fff; border:1px solid #cfe6c2; border-radius:8px; padding:8px 12px; margin-bottom:4px; }
  .doc-existe > i { color:#c0392b; font-size:1.2rem; }
  .doc-existe a { flex:1; font-size:.84rem; font-weight:700; color:var(--verde); text-decoration:none; word-break:break-all; }
  .doc-existe a:hover { text-decoration:underline; }
  .doc-kb { font-size:.7rem; color:var(--gris); font-weight:700; }
  .doc-del { background:none; border:none; color:#bbb; font-size:.9rem; cursor:pointer; padding:4px; border-radius:6px; }
  .doc-del:hover { background:#fdecec; color:#dc3545; }

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

  @keyframes spin { to { transform:rotate(360deg); } }
  .spin { display:inline-block;animation:spin .7s linear infinite; }
</style>
