import { redirect } from '@sveltejs/kit';
import { isAdminRole } from '$lib/utils/roles.js';

export async function load() {
	if (typeof window !== 'undefined') {
		const token = localStorage.getItem('token');
		const userStr = localStorage.getItem('user');

		if (!token || !userStr) {
			throw redirect(302, '/login');
		}

		try {
			const user = JSON.parse(userStr);
			if (!isAdminRole(user)) {
				throw redirect(302, '/');
			}

			return { user };
		} catch (error) {
			localStorage.removeItem('token');
			localStorage.removeItem('user');
			throw redirect(302, '/login');
		}
	}

	return {};
}
