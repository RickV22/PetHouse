import { redirect } from '@sveltejs/kit';
import { isAdminRole } from '$lib/utils/roles.js';

export async function load({ url }) {
	// Verificar si estamos en el cliente
	if (typeof window !== 'undefined') {
		const token = localStorage.getItem('token');
		const userStr = localStorage.getItem('user');

		// Si no hay token o usuario, redirigir al login
		if (!token || !userStr) {
			throw redirect(302, '/login');
		}

		try {
			const user = JSON.parse(userStr);

			// Verificar si el usuario tiene permisos de admin (role_id 1)
			if (!isAdminRole(user)) {
				// Usuario normal, redirigir a la página principal
				throw redirect(302, '/');
			}

			// Usuario admin autorizado
			return { user };
		} catch (error) {
			// Error al parsear usuario, limpiar y redirigir
			localStorage.removeItem('token');
			localStorage.removeItem('user');
			throw redirect(302, '/login');
		}
	}

	// En el servidor, no hacer nada (SSR)
	return {};
}