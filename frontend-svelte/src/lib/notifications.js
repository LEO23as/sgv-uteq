import { writable, derived } from 'svelte/store';
import { fetchAPI } from '$lib/stores';

/**
 * @typedef {Object} Notificacion
 * @property {string} id
 * @property {'convenio' | 'proyecto' | 'periodo' | 'sistema'} tipo
 * @property {'danger' | 'warning' | 'info' | 'success'} prioridad
 * @property {string} titulo
 * @property {string} mensaje
 * @property {string} [fecha]
 * @property {string} [link]
 * @property {number} [targetId]
 * @property {string} icono
 * @property {boolean} leida
 */

export const notificaciones = writable([]);
export const notificacionesLoading = writable(false);

function parsearFecha(f) {
  if (!f) return null;
  if (typeof f !== 'string') return new Date(f);
  if (/^\d{4}-\d{2}-\d{2}/.test(f)) {
    const [y, m, d] = f.split('T')[0].split('-').map(Number);
    return new Date(y, m - 1, d);
  }
  if (/^\d{1,2}\/\d{1,2}\/\d{4}/.test(f)) {
    const [d, m, y] = f.split('/').map(Number);
    return new Date(y, m - 1, d);
  }
  const dt = new Date(f);
  return isNaN(dt.getTime()) ? null : dt;
}

export async function cargarNotificaciones() {
  notificacionesLoading.set(true);
  try {
    const [conveniosRes, proyectosRes, periodosRes] = await Promise.all([
      fetch('/api/convenios/list/', { credentials: 'include' }).then(r => r.json()).catch(() => ({ results: [] })),
      fetchAPI('/api/proyectos/').catch(() => []),
      fetchAPI('/api/periodos/').catch(() => [])
    ]);

    const convenios = conveniosRes.results || [];
    const proyectos = Array.isArray(proyectosRes) ? proyectosRes : [];
    const periodos = Array.isArray(periodosRes) ? periodosRes : [];

    const lista = [];
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    // 1. Analizar Convenios por vencer o vencidos
    for (const c of convenios) {
      let fin = parsearFecha(c.fecha_fin);
      const ini = parsearFecha(c.fecha_inicio || c.fecha_firma);
      if (!fin && ini && c.duracion_anios) {
        fin = new Date(ini);
        fin.setFullYear(fin.getFullYear() + Number(c.duracion_anios));
      }

      if (fin) {
        fin.setHours(0, 0, 0, 0);
        const restDias = Math.ceil((fin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));

        if (restDias <= 0) {
          lista.push({
            id: `conv-vencido-${c.id_convenio}`,
            tipo: 'convenio',
            prioridad: 'danger',
            titulo: `Convenio Vencido (${c.numero_memorando || 'Sin Nro.'})`,
            mensaje: `El acuerdo con "${c.entidad_nombre}" finalizó su vigencia el ${fin.toLocaleDateString('es-EC')}.`,
            link: `/convenios`,
            targetId: c.id_convenio,
            icono: 'bi-exclamation-octagon-fill',
            leida: false,
          });
        } else if (restDias <= 60) {
          lista.push({
            id: `conv-por-vencer-${c.id_convenio}`,
            tipo: 'convenio',
            prioridad: 'warning',
            titulo: `Convenio por Caducar (${c.numero_memorando || 'Sin Nro.'})`,
            mensaje: `El convenio con "${c.entidad_nombre}" vencerá en ${restDias} días (${fin.toLocaleDateString('es-EC')}).`,
            link: `/convenios`,
            targetId: c.id_convenio,
            icono: 'bi-hourglass-split',
            leida: false,
          });
        }
      }
    }

    // 2. Analizar Proyectos en ejecución o por culminar
    for (const p of proyectos) {
      const fin = parsearFecha(p.fecha_fin_planificada || p.fecha_fin_real);
      if (fin && p.estado === 'EN_EJECUCION') {
        fin.setHours(0, 0, 0, 0);
        const restDias = Math.ceil((fin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
        if (restDias <= 30 && restDias > 0) {
          lista.push({
            id: `proy-cierre-${p.id_proyecto}`,
            tipo: 'proyecto',
            prioridad: 'warning',
            titulo: `Proyecto Próximo a Cierre (${p.codigo})`,
            mensaje: `"${p.nombre_corto || p.nombre}" tiene programado su fin en ${restDias} días.`,
            link: `/proyectos`,
            targetId: p.id_proyecto,
            icono: 'bi-calendar-check',
            leida: false,
          });
        }
      }
      if (p.estado === 'PROPUESTO') {
        lista.push({
          id: `proy-propuesto-${p.id_proyecto}`,
          tipo: 'proyecto',
          prioridad: 'info',
          titulo: `Proyecto Propuesto (${p.codigo})`,
          mensaje: `"${p.nombre_corto || p.nombre}" registrado, pendiente de aprobación y resolución.`,
          link: `/proyectos`,
          targetId: p.id_proyecto,
          icono: 'bi-file-earmark-plus',
          leida: false,
        });
      }
    }

    // 3. Período Académico Activo
    const periodoActivo = periodos.find(p => p.activo);
    if (periodoActivo) {
      lista.push({
        id: `per-activo-${periodoActivo.id_periodo}`,
        tipo: 'periodo',
        prioridad: 'success',
        titulo: `Período Académico Activo`,
        mensaje: `Ciclo ${periodoActivo.nombre} (${periodoActivo.codigo}) en curso.`,
        link: `/periodos`,
        targetId: periodoActivo.id_periodo,
        icono: 'bi-calendar-event-fill',
        leida: false,
      });
    }

    // 4. Capas e Indicadores
    lista.push({
      id: 'capas-inec',
      tipo: 'sistema',
      prioridad: 'info',
      titulo: 'Datos INEC NBI 2022',
      mensaje: 'Capas de necesidades básicas insatisfechas activas en el mapa territorial.',
      link: '/mapa',
      icono: 'bi-map-fill',
      leida: false,
    });

    notificaciones.set(lista);
    emitirAlertaCaducidadNativa(lista);
  } catch (e) {
    console.error('Error cargando notificaciones:', e);
  } finally {
    notificacionesLoading.set(false);
  }
}

export const totalNoLeidas = derived(notificaciones, ($list) => {
  return $list.filter(n => !n.leida).length;
});

export function marcarTodasLeidas() {
  notificaciones.update(list => list.map(n => ({ ...n, leida: true })));
}

export function marcarLeida(id) {
  notificaciones.update(list => list.map(n => n.id === id ? { ...n, leida: true } : n));
}

export async function solicitarPermisoNotificaciones() {
  if (typeof window === 'undefined' || !('Notification' in window)) {
    return false;
  }
  if (Notification.permission === 'granted') {
    return true;
  }
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  return false;
}

export function emitirAlertaCaducidadNativa(lista) {
  if (typeof window === 'undefined' || !('Notification' in window)) return;
  if (Notification.permission !== 'granted') return;

  const criticas = lista.filter(n => n.tipo === 'convenio' || n.id.startsWith('proy-cierre'));
  if (criticas.length === 0) return;

  const ultimoAviso = sessionStorage.getItem('sgv_ultimo_aviso_caducidad');
  if (ultimoAviso && Date.now() - Number(ultimoAviso) < 3600000) return;
  sessionStorage.setItem('sgv_ultimo_aviso_caducidad', String(Date.now()));

  const primera = criticas[0];
  const total = criticas.length;
  const titulo = total === 1 ? primera.titulo : `SGV UTEQ: ${total} Alertas de Caducidad`;
  const cuerpo = total === 1 ? primera.mensaje : `Hay ${total} convenios y proyectos próximos a caducar o finalizar vigencia.`;

  try {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.ready.then(reg => {
        reg.showNotification(titulo, {
          body: cuerpo,
          icon: '/icons/icon-192.png',
          badge: '/icons/icon-192.png',
          data: { url: primera.link || '/convenios' }
        });
      });
    } else {
      new Notification(titulo, {
        body: cuerpo,
        icon: '/icons/icon-192.png'
      });
    }
  } catch (e) {
    console.log('Aviso nativo omitido:', e);
  }
}
