/**
 * Utilidades para manejo de autenticación y redirección
 */

/**
 * Verifica si el usuario está autenticado
 * @returns {Object|null} Usuario autenticado o null si no está autenticado
 */
export function getCurrentUser() {
	if (typeof window === 'undefined') return null;

	const token = localStorage.getItem('token');
	const userStr = localStorage.getItem('user');

	if (!token || !userStr) return null;

	try {
		return JSON.parse(userStr);
	} catch (error) {
		// Limpiar datos corruptos
		localStorage.removeItem('token');
		localStorage.removeItem('user');
		return null;
	}
}

/**
 * Guarda la URL de destino antes de redirigir al login
 * @param {string} redirectUrl - URL a la que redirigir después del login
 */
export function saveRedirectUrl(redirectUrl) {
	if (typeof window !== 'undefined') {
		localStorage.setItem('redirectAfterLogin', redirectUrl);
	}
}

/**
 * Obtiene y limpia la URL de redirección guardada
 * @returns {string|null} URL guardada o null
 */
export function getAndClearRedirectUrl() {
	if (typeof window === 'undefined') return null;

	const redirectUrl = localStorage.getItem('redirectAfterLogin');
	if (redirectUrl) {
		localStorage.removeItem('redirectAfterLogin');
		return redirectUrl;
	}
	return null;
}

/**
 * Verifica autenticación y maneja redirección con mensaje
 * @param {string} currentUrl - URL actual para guardar como destino
 * @param {string} message - Mensaje a mostrar si no está autenticado
 * @returns {Object} Resultado con user o error
 */
export function requireAuth(currentUrl, message = 'Para realizar esta acción debe iniciar sesión') {
	const user = getCurrentUser();

	if (!user) {
		// Guardar URL de destino
		saveRedirectUrl(currentUrl);

		// Mostrar mensaje de error
		if (typeof window !== 'undefined') {
			import('sweetalert2').then(Swal => {
				Swal.default.fire({
					title: 'Acceso requerido',
					text: message,
					icon: 'info',
					confirmButtonText: 'Iniciar Sesión'
				}).then(() => {
								// Redirigir al login después de cerrar el modal (navegación cliente)
								import('$app/navigation').then(({ goto }) => goto('/login'));
				});
			});
		}

		throw new Error('AUTH_REQUIRED');
	}

	return { user };
}