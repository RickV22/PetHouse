import { redirect } from '@sveltejs/kit';

export async function load({ url, depends, fetch: kitFetch }) {
	// Mark this load function as depending on auth
	depends('app:auth');

	// Check if we're on the client side
	if (typeof window !== 'undefined') {
		const token = localStorage.getItem('token');
		const userStr = localStorage.getItem('user');

		// If not authenticated, save the URL and redirect to login
		if (!token || !userStr) {
			localStorage.setItem('redirectAfterLogin', url.pathname + url.search);
			throw redirect(302, '/login?message=Para solicitar adopción debe iniciar sesión');
		}

		try {
			const user = JSON.parse(userStr);
		} catch (error) {
			localStorage.removeItem('token');
			localStorage.removeItem('user');
			localStorage.setItem('redirectAfterLogin', url.pathname + url.search);
			throw redirect(302, '/login?message=Para solicitar adopción debe iniciar sesión');
		}
	}

	// Load the pet
	const petId = url.searchParams.get('pet_id');

	console.log('pet_id recibido:', petId);

	if (!petId) {
		return { pet: null };
	}

	try {
		const res = await kitFetch(`http://localhost:8000/pets/${petId}`);

		if (!res.ok) {
			console.error('Error fetching pet:', res.status);
			return { pet: null };
		}

		const pet = await res.json();
		console.log('pet recibido:', pet);
		return { pet };
	} catch (error) {
		console.error('Error fetching pet:', error);
		// If SSR fetch fails, return null and let the client-side onMount handle it
		return { pet: null };
	}
}
