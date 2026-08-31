import { writable } from 'svelte/store';

/**
 * Estado global del diálogo de confirmación.
 * @typedef {Object} ConfirmOptions
 * @property {string} title - Título del diálogo
 * @property {string} message - Mensaje o descripción
 * @property {string} [confirmText='Confirmar'] - Texto del botón de confirmación
 * @property {string} [cancelText='Cancelar'] - Texto del botón de cancelar
 * @property {'danger' | 'warning' | 'info' | 'primary'} [type='danger'] - Tipo de acción / color
 * @property {string} [icon] - Icono Bootstrap opcional
 */

export const confirmState = writable({
  isOpen: false,
  title: '',
  message: '',
  confirmText: 'Confirmar',
  cancelText: 'Cancelar',
  type: 'danger',
  icon: '',
  resolve: null,
});

/**
 * Muestra un diálogo de confirmación modal institucional y retorna una Promesa booleana.
 * @param {ConfirmOptions} options
 * @returns {Promise<boolean>}
 */
export function confirmDialog(options) {
  return new Promise((resolve) => {
    confirmState.set({
      isOpen: true,
      title: options.title || '¿Estás seguro?',
      message: options.message || '',
      confirmText: options.confirmText || 'Confirmar',
      cancelText: options.cancelText || 'Cancelar',
      type: options.type || 'danger',
      icon: options.icon || (options.type === 'warning' ? 'bi-exclamation-triangle' : options.type === 'info' ? 'bi-info-circle' : 'bi-trash3'),
      resolve,
    });
  });
}

export function closeConfirm(result) {
  confirmState.update((s) => {
    if (s.resolve) s.resolve(result);
    return { ...s, isOpen: false, resolve: null };
  });
}
