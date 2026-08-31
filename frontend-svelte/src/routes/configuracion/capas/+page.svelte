<script>
  import { onMount } from 'svelte';
  import { fetchAPI } from '$lib/stores';
  import { toast } from '$lib/toast';
  import { confirmDialog } from '$lib/confirm';

  let capas = $state([]);
  let cargando = $state(true);
  let subiendo = $state(false);
  let progreso = $state(0);
  let progresoInterval;

  let form = $state({
    tipo_indicador: 'NBI',
    anio: 2022,
    unidad: '%',
    fuente: 'INEC - Censo de Población y Vivienda 2022',
    archivo: null,
  });

  let preview = $state(null);
  let errores = $state([]);

  async function cargar() {
    cargando = true;
    try { 
      capas = await fetchAPI('/api/capas-indicador/'); 
    } catch (e) { 
      toast.error('No se pudieron cargar las capas'); 
    } finally { 
      cargando = false; 
    }
  }

  onMount(cargar);

  function onFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    form.archivo = f;
    const reader = new FileReader();
    reader.onload = () => parseCSV(reader.result);
    reader.readAsText(f, 'utf-8');
  }

  function parseCSV(txt) {
    errores = [];
    const lines = txt.split(/\r?\n/).filter(l => l.trim());
    if (!lines.length) { errores = ['Archivo vacío']; preview = null; return; }
    const header = lines[0].split(',').map(s => s.trim().toLowerCase());
    const iDpa = header.indexOf('dpa_canton');
    const iVal = header.indexOf('valor');
    if (iDpa < 0 || iVal < 0) {
      errores = ['Faltan columnas requeridas: dpa_canton, valor'];
      preview = null;
      return;
    }
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const c = lines[i].split(',').map(s => s.trim());
      const dpa = c[iDpa];
      const val = parseFloat(c[iVal]);
      if (!/^\d{4}$/.test(dpa)) { errores.push(`Fila ${i+1}: dpa_canton inválido "${dpa}"`); continue; }
      if (isNaN(val))           { errores.push(`Fila ${i+1}: valor inválido "${c[iVal]}"`);   continue; }
      rows.push({ dpa_canton: dpa, valor: val });
    }
    preview = rows;
  }

  async function subir() {
    if (!form.archivo)      { toast.error('Selecciona un archivo CSV'); return; }
    if (!preview?.length)   { toast.error('CSV sin filas válidas');     return; }
    if (!form.fuente.trim()){ toast.error('Indica la fuente');          return; }
    
    subiendo = true;
    progreso = 15;
    progresoInterval = setInterval(() => {
      if (progreso < 85) {
        progreso += Math.floor(Math.random() * 15) + 5;
      }
    }, 200);

    try {
      const fd = new FormData();
      fd.append('tipo_indicador', form.tipo_indicador);
      fd.append('anio', form.anio);
      fd.append('unidad', form.unidad);
      fd.append('fuente', form.fuente);
      fd.append('archivo', form.archivo);

      const r = await fetch('/api/capas-indicador/upload/', { 
        method: 'POST', 
        body: fd, 
        credentials: 'include' 
      });

      progreso = 100;
      clearInterval(progresoInterval);

      let data;
      const textResponse = await r.text();
      try {
        data = JSON.parse(textResponse);
      } catch (err) {
        throw new Error('Error en el servidor al procesar la capa');
      }

      if (!r.ok) throw new Error(data.error || 'Error al subir la capa');

      toast.success(`¡Capa guardada con éxito! ${data.insertados} registros (${data.tipo_indicador} ${data.anio})`);
      form = { tipo_indicador: 'NBI', anio: 2022, unidad: '%', fuente: 'INEC - Censo de Población y Vivienda 2022', archivo: null };
      preview = null; 
      errores = [];
      const fileInput = document.getElementById('csvinput');
      if (fileInput) fileInput.value = '';
      await cargar();
    } catch (e) {
      clearInterval(progresoInterval);
      toast.error(e.message || 'Error al procesar el archivo');
    } finally { 
      setTimeout(() => {
        subiendo = false;
        progreso = 0;
      }, 500);
    }
  }

  async function eliminar(c) {
    const ok = await confirmDialog({
      title: '¿Eliminar capa de indicadores territorial?',
      message: `Se eliminará la capa "${c.tipo_indicador} ${c.anio}" y sus ${c.total} registros de cantones asociados en la base de datos.`,
      confirmText: 'Sí, eliminar capa',
      type: 'danger',
      icon: 'bi-map-fill'
    });
    if (!ok) return;

    try {
      const r = await fetch(`/api/capas-indicador/${c.tipo_indicador}/${c.anio}/`, { 
        method: 'DELETE', 
        credentials: 'include' 
      });
      if (!r.ok) throw new Error('No se pudo eliminar la capa');
      toast.success('Capa territorial eliminada correctamente');
      await cargar();
    } catch (e) { 
      toast.error(e.message); 
    }
  }
</script>

<svelte:head><title>Capas del mapa — SGV UTEQ</title></svelte:head>

<div class="subbar">
  <nav class="breadcrumb">
    <a href="/dashboard">Inicio</a>
    <span class="sep">/</span>
    <a href="/configuracion">Configuración</a>
    <span class="sep">/</span>
    <span class="current">Capas del mapa</span>
  </nav>
</div>

<div class="cap-body">

  <!-- FORM DE CARGA -->
  <section class="cap-card">
    <header class="cap-h">
      <div class="cap-h-icon">
        <i class="bi bi-cloud-upload"></i>
      </div>
      <div>
        <h3>Cargar nueva capa</h3>
        <p>Sube un archivo CSV con los valores de un indicador por cantón para alimentar la visualización interactiva del mapa.</p>
      </div>
    </header>

    <div class="cap-form">
      <div class="fg">
        <label>Tipo de indicador</label>
        <input type="text" bind:value={form.tipo_indicador} maxlength="30" placeholder="NBI, IDH, POBLACION..." />
      </div>
      <div class="fg">
        <label>Año</label>
        <input type="number" bind:value={form.anio} min="1990" max="2100" />
      </div>
      <div class="fg">
        <label>Unidad</label>
        <input type="text" bind:value={form.unidad} maxlength="20" placeholder="%" />
      </div>
      <div class="fg wide">
        <label>Fuente</label>
        <input type="text" bind:value={form.fuente} maxlength="160" placeholder="Ej: INEC - Censo de Población y Vivienda 2022" />
      </div>
      <div class="fg wide">
        <label>Archivo CSV <span class="hint">(columnas: <code>dpa_canton</code>, <code>valor</code>)</span></label>
        <div class="file-uploader-box">
          <input id="csvinput" type="file" accept=".csv,text/csv" onchange={onFile} class="file-hidden-input" />
          <label for="csvinput" class="file-browse-btn">
            <i class="bi bi-folder2-open"></i> Seleccionar archivo
          </label>
          <span class="file-selected-name" title={form.archivo?.name || ''}>
            {#if form.archivo}
              <i class="bi bi-file-earmark-check-fill text-success"></i> {form.archivo.name}
            {:else}
              <span class="text-muted">Ningún archivo seleccionado</span>
            {/if}
          </span>
        </div>
      </div>
    </div>

    {#if errores.length}
      <div class="alert warn">
        <b>{errores.length} advertencias:</b>
        <ul>{#each errores.slice(0,10) as e}<li>{e}</li>{/each}</ul>
        {#if errores.length > 10}<small>...y {errores.length - 10} más</small>{/if}
      </div>
    {/if}

    {#if preview}
      <div class="alert ok">
        ✓ <b>{preview.length}</b> filas válidas listas para insertar.
      </div>
    {/if}

    <!-- PROGRESS BAR ELEGANTE -->
    {#if subiendo}
      <div class="progress-wrap">
        <div class="progress-header">
          <span class="progress-label"><i class="bi bi-arrow-repeat spin"></i> Procesando e indexando capa en la base de datos...</span>
          <span class="progress-pct">{progreso}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: {progreso}%;"></div>
        </div>
      </div>
    {/if}

    <div class="cap-actions">
      <button class="btn-primario" onclick={subir} disabled={subiendo || !preview?.length}>
        {#if subiendo}
          <i class="bi bi-arrow-repeat spin"></i> Guardando...
        {:else}
          <i class="bi bi-check-lg"></i> Guardar capa
        {/if}
      </button>
    </div>
  </section>

  <!-- LISTA DE CAPAS EXISTENTES CON ESTILO VERDE SGA -->
  <section class="cap-card table-card">
    <header class="cap-h">
      <div class="cap-h-icon">
        <i class="bi bi-database"></i>
      </div>
      <div>
        <h3>Capas cargadas en el sistema</h3>
        <p>Indicadores actualmente activos y disponibles para visualizar en el mapa.</p>
      </div>
    </header>

    {#if cargando}
      <div class="empty"><i class="bi bi-arrow-repeat spin"></i> Cargando capas...</div>
    {:else if !capas.length}
      <div class="empty">No hay capas cargadas todavía. Sube una con el formulario superior.</div>
    {:else}
      <div class="table-container">
        <table class="cap-tabla">
          <thead>
            <tr>
              <th>INDICADOR</th>
              <th>AÑO</th>
              <th>CANTONES</th>
              <th>RANGO (%)</th>
              <th>UNIDAD</th>
              <th>FUENTE</th>
              <th>ESTADO</th>
              <th class="text-center">ACCIONES</th>
            </tr>
          </thead>
          <tbody>
            {#each capas as c}
              <tr>
                <td>
                  <span class="indicador-badge">{c.tipo_indicador}</span>
                </td>
                <td class="fw-bold">{c.anio}</td>
                <td><span class="cantones-badge">{c.total} cantones</span></td>
                <td class="fw-semibold text-primary">{c.min?.toFixed?.(1) ?? '—'}% – {c.max?.toFixed?.(1) ?? '—'}%</td>
                <td class="text-muted">{c.unidad}</td>
                <td class="fuente-cell">{c.fuente}</td>
                <td>
                  <span class="estado-activa"><i class="bi bi-check-circle-fill"></i> Activa</span>
                </td>
                <td class="text-center">
                  <div class="actions-group">
                    <a href="/mapa" class="btn-action view" title="Ver en el mapa">
                      <i class="bi bi-map-fill"></i>
                    </a>
                    <button class="btn-action delete" onclick={() => eliminar(c)} title="Eliminar capa">
                      <i class="bi bi-trash-fill"></i>
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </section>

</div>

<style>
/* ── SUBBAR ── */
.subbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
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

/* ── BODY ── */
.cap-body {
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.cap-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid #eef2f6;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  padding: 24px 26px;
}

.cap-h {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.cap-h-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: #e8f5e9;
  color: #1b7a2b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.cap-h h3 {
  font-size: 1.05rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 4px;
}

.cap-h p {
  font-size: 0.78rem;
  color: #64748b;
  margin: 0;
}

/* ── FORMULARIO ── */
.cap-form {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px 18px;
}

.fg {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fg.wide {
  grid-column: span 2;
}

.fg label {
  font-size: 0.72rem;
  font-weight: 800;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.fg .hint {
  text-transform: none;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 0;
}

.fg .hint code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  color: #1e293b;
}

.fg input {
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 9px 14px;
  font-size: 0.86rem;
  font-family: inherit;
  font-weight: 600;
  color: #1e293b;
  background: #f8fafc;
  outline: none;
  transition: all 0.2s ease;
}

.fg input:focus {
  border-color: #1b7a2b;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(27, 122, 43, 0.1);
}

@media (max-width: 900px) {
  .cap-form { grid-template-columns: repeat(2, 1fr); }
  .fg.wide { grid-column: span 2; }
}

/* ── CUSTOM FILE UPLOADER BOX ── */
.file-uploader-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1.5px dashed #cbd5e1;
  border-radius: 10px;
  padding: 6px 10px;
  transition: all 0.2s ease;
}

.file-uploader-box:hover {
  border-color: #1b7a2b;
  background: #f0fdf4;
}

.file-hidden-input {
  display: none !important;
}

.file-browse-btn {
  background: #ffffff;
  border: 1.5px solid #cbd5e1;
  color: #334155;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.file-browse-btn:hover {
  background: #1b7a2b;
  border-color: #1b7a2b;
  color: #ffffff;
}

.file-selected-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-muted { color: #94a3b8; }
.text-success { color: #16a34a; }
.text-primary { color: #0284c7; }
.fw-bold { font-weight: 700; }
.fw-semibold { font-weight: 600; }
.text-center { text-align: center; }

/* ── ALERTAS ── */
.alert {
  margin-top: 16px;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 0.82rem;
  font-weight: 600;
}

.alert.warn {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

.alert.ok {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.alert ul { margin: 6px 0 0 20px; font-weight: 500; }

/* ── PROGRESS BAR ── */
.progress-wrap {
  margin-top: 16px;
  padding: 14px 18px;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
}

.progress-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1b7a2b;
}

.progress-pct {
  color: #1b7a2b;
  font-weight: 800;
}

.progress-bar-bg {
  width: 100%;
  height: 9px;
  background: #e2e8f0;
  border-radius: 20px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #1b7a2b 0%, #22c55e 100%);
  border-radius: 20px;
  transition: width 0.25s ease-in-out;
}

.cap-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.btn-primario {
  background: #1b7a2b;
  color: #ffffff;
  border: none;
  border-radius: 24px;
  padding: 9px 26px;
  font-size: 0.88rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: inherit;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(27, 122, 43, 0.25);
}

.btn-primario:hover:not(:disabled) {
  background: #155e04;
  transform: translateY(-1px);
}

.btn-primario:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

/* ── TABLA ESTILO SGA (VERDE INSTITUCIONAL) ── */
.table-container {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.cap-tabla {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.cap-tabla thead {
  background: #1b7a2b;
}

.cap-tabla th {
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

.cap-tabla td {
  padding: 14px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
  vertical-align: middle;
}

.cap-tabla tbody tr:hover {
  background: #f8fafc;
}

.indicador-badge {
  background: #e8f5e9;
  color: #1b7a2b;
  font-weight: 800;
  font-size: 0.78rem;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid #c8e6c9;
  display: inline-block;
}

.cantones-badge {
  background: #f1f5f9;
  color: #475569;
  font-weight: 700;
  font-size: 0.76rem;
  padding: 3px 10px;
  border-radius: 8px;
}

.fuente-cell {
  color: #475569;
  font-weight: 500;
  font-size: 0.8rem;
  max-width: 250px;
}

.estado-activa {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.74rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

/* Acciones */
.actions-group {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-action {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn-action.view {
  color: #0284c7;
  border-color: #bae6fd;
}
.btn-action.view:hover {
  background: #e0f2fe;
}

.btn-action.delete {
  color: #e11d48;
  border-color: #fecdd3;
}
.btn-action.delete:hover {
  background: #ffe4e6;
}

.empty {
  padding: 36px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 0.88rem;
  font-weight: 500;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin 0.7s linear infinite; }
</style>
