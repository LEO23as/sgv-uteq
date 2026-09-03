import { writable } from 'svelte/store';

export const user = writable(null);
export const loading = writable(false);
export const capaNBIActiva = writable(false);
export const capaODSActiva = writable(false);
export const odsSeleccionadoMapa = writable(null);
export const periodoSeleccionadoGlobal = writable(null);

/**
 * Petición directa a la API (SIEMPRE DATOS FRESCOS DEL SERVIDOR).
 * Se utiliza para proyectos, convenios, notas, documentos y cualquier dato que cambie.
 */
export async function fetchAPI(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

/**
 * Petición con Caché Inteligente en sessionStorage (SOLO para catálogos estáticos y mapas).
 * Garantía antifraude: Solo almacena datos de solo-lectura (Facultades, Carreras, GeoJSON)
 * y expira automáticamente o se invalida al detectar cambios.
 */
export async function fetchAPICached(path, options = {}, ttlMinutos = 15) {
  if (typeof window === 'undefined') return fetchAPI(path, options);

  const cacheKey = `sgv_cache_${path}`;
  try {
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      const edadMs = Date.now() - timestamp;
      // Si el dato tiene menos del tiempo de vida permitido, usarlo inmediatamente (0 ms)
      if (edadMs < ttlMinutos * 60 * 1000) {
        return data;
      }
    }
  } catch (e) {
    // Si falla la lectura de sesión, continuar normalmente con fetch
  }

  // Si no está en caché o expiró, consultar el dato fresco al servidor
  const data = await fetchAPI(path, options);
  try {
    sessionStorage.setItem(cacheKey, JSON.stringify({ data, timestamp: Date.now() }));
  } catch (e) {
    // Manejar límite de memoria de sesión
  }
  return data;
}

/**
 * Invalida la caché del navegador para asegurar que los cambios se reflejen al 100% de inmediato.
 */
export function invalidarCache(patron = '') {
  if (typeof window === 'undefined') return;
  try {
    if (!patron) {
      // Limpiar toda la caché del sistema
      Object.keys(sessionStorage).forEach(k => {
        if (k.startsWith('sgv_cache_')) sessionStorage.removeItem(k);
      });
    } else {
      // Limpiar solo los endpoints que coincidan
      Object.keys(sessionStorage).forEach(k => {
        if (k.startsWith('sgv_cache_') && k.includes(patron)) sessionStorage.removeItem(k);
      });
    }
  } catch (e) {}
}

export async function checkAuth() {
  try {
    const data = await fetchAPI('/api/auth/me/');
    user.set(data);
    return data;
  } catch {
    user.set(null);
    return null;
  }
}

export async function login(username, password) {
  const data = await fetchAPI('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  invalidarCache(); // Limpiar cualquier residuo de sesiones anteriores
  user.set(data);
  return data;
}

export async function logout() {
  await fetchAPI('/api/auth/logout/');
  invalidarCache(); // Limpiar caché al cerrar sesión
  user.set(null);
}
