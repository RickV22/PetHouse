<script>
	import { createUser, loginUser, registerUser } from '../../api/user_service.js';
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
	import API_URL from '../../api/api.js';
	import Navbar from '$lib/components/Navbar.svelte';
	import { setAuth } from '$lib/stores/auth.js';
	import { getAndClearRedirectUrl } from '$lib/utils/auth.js';
	import { isAdminRole } from '$lib/utils/roles.js';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Swal from 'sweetalert2';

	// Google client id desde env (asegurar variable existe en runtime)
	const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

	// Google Identity Helpers
	function loadGoogleScript() {
		return new Promise((resolve, reject) => {
			if (typeof window === 'undefined') return resolve();
			if (window.google && window.google.accounts && window.google.accounts.id) return resolve();
			const script = document.createElement('script');
			script.src = 'https://accounts.google.com/gsi/client';
			script.async = true;
			script.defer = true;
			script.onload = () => resolve();
			script.onerror = () => reject(new Error('Failed to load Google Identity Services'));
			document.head.appendChild(script);
		});
	}

	async function handleCredentialResponse(response) {
		if (!response || !response.credential) return;
		const id_token = response.credential;
		try {
			const res = await fetch(`${API_URL}/users/google-login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ id_token })
			});
			if (!res.ok) {
				const err = await res.text().catch(() => '');
				throw new Error(`Google login failed: ${res.status} ${err}`);
			}
			const data = await res.json();
			setAuth(data.access_token, data.user);
			Swal.fire({ title: 'Bienvenido', text: `Hola ${data.user.name}`, icon: 'success' });
			const redirectUrl = getAndClearRedirectUrl();
			if (redirectUrl) goto(redirectUrl);
			else goto(isAdminRole(data.user) ? '/admin' : '/');
		} catch (e) {
			console.error('Google login error', e);
			Swal.fire('Error', 'No se pudo iniciar sesión con Google.', 'error');
		}
	}

	onMount(async () => {
		try {
			if (!GOOGLE_CLIENT_ID) {
				console.warn('VITE_GOOGLE_CLIENT_ID is not set. Google Sign-In will not initialize.');
				return;
			}
			await loadGoogleScript();
			// Initialize once, but always render the button for this mount
			// @ts-ignore
			if (!window.__pethouse_google_initialized) {
				// @ts-ignore
				google.accounts.id.initialize({
					client_id: GOOGLE_CLIENT_ID,
					callback: handleCredentialResponse
				});
				window.__pethouse_google_initialized = true;
			}
			// Ensure the SDK injects the button into the freshly mounted container
			try {
				// @ts-ignore
				google.accounts.id.renderButton(document.getElementById('googleSignInDiv'), { theme: 'outline', size: 'large', width: '280' });
			} catch (e) {
				// ignore render errors
			}
		} catch (e) {
			console.warn('Google Identity could not be initialized', e);
		}
	});

	async function handleGoogleClick() {
		try {
			if (!window.google || !window.google.accounts || !window.google.accounts.id) {
				await loadGoogleScript();
			}

			if (!window.__pethouse_google_initialized) {
				// initialize if not already
				// @ts-ignore
				google.accounts.id.initialize({
					client_id: GOOGLE_CLIENT_ID,
					callback: handleCredentialResponse
				});
				window.__pethouse_google_initialized = true;
			}
			// Always try to render the button into the current DOM container
			try {
				// @ts-ignore
				google.accounts.id.renderButton(document.getElementById('googleSignInDiv'), { theme: 'outline', size: 'large', width: '280' });
			} catch (e) {
				// ignore
			}

			// Prefer clicking the SDK-inserted button so Google handles the flow exactly as before
			const sdkBtn = document.querySelector('#googleSignInDiv button');
			if (sdkBtn) {
				try { sdkBtn.click(); return; } catch(e) { console.warn('SDK button click failed', e); }
			}

			// fallback to prompt
			// @ts-ignore
			google.accounts.id.prompt();
		} catch (e) {
			console.error('Error triggering Google Sign-In prompt', e);
		}
	}
	// svelte-ignore export_let_unused
		export let data;

	let isRegister = false;

	let nombre = '';
	let apellido = '';
	let email = '';
	let password = '';
	let showPassword = false;
	let authMessage = '';
	let passwordError = '';

	// Reglas de validación reactivas
	$: pwdRules = {
		length: password.length >= 8,
		upper: /[A-Z]/.test(password),
		lower: /[a-z]/.test(password),
		number: /\d/.test(password),
		special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
	};

	$: isPasswordValid = Object.values(pwdRules).every(Boolean);

	// Get message from URL if present
	$: if ($page.url.searchParams.has('message')) {
		authMessage = $page.url.searchParams.get('message');
		// Show the message in a toast or alert
		if (authMessage) {
			Swal.fire({
				title: 'Acceso requerido',
				text: authMessage,
				icon: 'info',
				toast: true,
				position: 'top-end',
				showConfirmButton: false,
				timer: 3000
			});
		}
	}

	async function handleSubmit() {
		if (isRegister) {
			// =========================
			// REGISTRO
			// =========================
			const userData = {
				role_id: 2,  // Usuario normal por defecto
				name: nombre,
				last_name: apellido,
				email: email,
				password: password
			};

			try {
				const result = await registerUser(userData);

				Swal.fire({
					title: 'Éxito',
					text: 'Usuario registrado correctamente. Ahora puedes iniciar sesión.',
					icon: 'success'
				});

				// limpiar campos
				nombre = '';
				apellido = '';
				email = '';
				password = '';

				isRegister = false;

			} catch (error) {
				passwordError = error.message;
				// Si el error es de la contraseña, no mostramos modal, solo el texto abajo
				if (!error.message.includes('contraseña') && !error.message.includes('caracter')) {
					Swal.fire({
						title: 'Error',
						text: error.message || 'Error registrando usuario',
						icon: 'error'
					});
				}

                
			}

		} else {
		
			try {
				const result = await loginUser(email, password);
				
				console.log('Login result:', result);

				// guardar token y usuario
			setAuth(result.access_token, result.user);
           
				Swal.fire({
					title: 'Bienvenido',
					text: `Hola ${result.user.name}`,
					icon: 'success'
				});

				// Verificar si hay una URL de redirección guardada
				const redirectUrl = getAndClearRedirectUrl();

				if (redirectUrl) {
					// Redirigir a la URL guardada
					goto(redirectUrl);
				} else {
					goto(isAdminRole(result.user) ? '/admin' : '/');
				}
			} catch (error) {
				Swal.fire({
					title: 'Error',
					text: error.message || 'Credenciales incorrectas',
					icon: 'error'
				});
			}
		}
	}
</script>

<Navbar />
<section class="login-wrapper" in:fade>
	<div class="login-deco deco-1"></div>
	<div class="login-deco deco-2"></div>
	<div class="login-card px-4" in:fly={{ y: 30, duration: 400, opacity: 0 }}>
		<div class="card-badge">🐾 PET HOUSE</div>
		<h2>{isRegister ? 'Crear cuenta' : 'Bienvenido'}</h2>
		<p class="subtitle">
			{isRegister ? 'Regístrate para comenzar una nueva historia' : 'Inicia sesión para continuar con tu búsqueda'}
		</p>

		<form on:submit|preventDefault={handleSubmit}>
			{#if isRegister}
				<div class="row g-2 mb-3" in:fly={{ y: -15, duration: 500 }}>
					<div class="col-md-6 text-start">
						<label for="nombre" class="small fw-bold">Nombre</label>
						<input id="nombre" class="form-control form-control-sm" type="text" bind:value={nombre} required />
					</div>
					<div class="col-md-6 text-start">
						<label for="apellido" class="small fw-bold">Apellido</label>
						<input id="apellido" class="form-control form-control-sm" type="text" bind:value={apellido} required />
					</div>
				</div>
			{/if}

			<div class="input-group mb-3">
				<label class="small fw-bold">Correo electrónico</label>
				<input class="form-control form-control-sm" type="email" bind:value={email} placeholder="ejemplo@email.com" required />
			</div>

			<div class="input-group mb-3">
				<label class="small fw-bold">Contraseña</label>
				<div class="password-wrapper">
					<input
						class="form-control form-control-sm"
						type={showPassword ? 'text' : 'password'}
						bind:value={password}
						placeholder="••••••••"
						required
					/>
					<span class="toggle-password" on:click={() => (showPassword = !showPassword)}>
						{showPassword ? '👁' : '👁‍🗨'}
					</span>
				</div>

				{#if isRegister}
					<div class="password-guidelines mt-3 p-3 rounded-3 bg-cream border-2 border-dark">
						<div class="row g-1">
							<div class="col-6 {pwdRules.length ? 'text-success' : 'text-muted'} x-small">
								<i class="bi {pwdRules.length ? 'bi-check-circle-fill' : 'bi-circle'}"></i> 8+ caracteres
							</div>
							<div class="col-6 {pwdRules.upper && pwdRules.lower ? 'text-success' : 'text-muted'} x-small">
								<i class="bi {pwdRules.upper && pwdRules.lower ? 'bi-check-circle-fill' : 'bi-circle'}"></i> Mayúsculas y minúsculas
							</div>
							<div class="col-6 {pwdRules.number ? 'text-success' : 'text-muted'} x-small">
								<i class="bi {pwdRules.number ? 'bi-check-circle-fill' : 'bi-circle'}"></i> Número
							</div>
							<div class="col-6 {pwdRules.special ? 'text-success' : 'text-muted'} x-small">
								<i class="bi {pwdRules.special ? 'bi-check-circle-fill' : 'bi-circle'}"></i> Símbolo
							</div>
						</div>
					</div>
					{#if passwordError}
						<div class="error-text text-danger x-small mt-2 fw-bold">
							{passwordError}
						</div>
					{/if}
				{/if}
			</div>

			<button class="btn-login py-2 mt-3" disabled={isRegister && !isPasswordValid}>
				{isRegister ? 'Registrarse' : 'Iniciar Sesión'}
			</button>
		</form>

		<!-- Google Sign-In -->
		<div class="mt-3 d-flex justify-content-center google-signin-wrapper">
			{#if GOOGLE_CLIENT_ID}
				<!-- Show the SDK-inserted button (we style it via CSS) -->
				<div id="googleSignInDiv"></div>
			{:else}
				<div class="google-missing text-center p-3">
					<p class="mb-1">Google Sign-In no está configurado.</p>
					<small class="text-muted">Agrega <strong>VITE_GOOGLE_CLIENT_ID</strong> en <em>.env</em> y reinicia el servidor de desarrollo.</small>
				</div>
			{/if}
		</div>

		<p class="footer-text">
			{#if !isRegister}
				¿No tienes cuenta?
				<a href="..." on:click|preventDefault={() => (isRegister = true)}> Regístrate </a>
			{:else}
				¿Ya tienes cuenta?
				<a href="..." on:click|preventDefault={() => (isRegister = false)}> Inicia sesión </a>
			{/if}
		</p>
	</div>
</section>

<style>
	.login-wrapper {
		min-height: 100vh;
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 3rem 1rem;
		background: radial-gradient(circle at top left, rgba(245, 183, 49, 0.18), transparent 28%),
			linear-gradient(180deg, var(--cream) 0%, var(--cream-dark) 100%);
		position: relative;
	}

	.login-deco {
		position: absolute;
		border-radius: 50%;
		pointer-events: none;
		opacity: 0.35;
	}

	.login-deco.deco-1 {
		width: 160px;
		height: 160px;
		background: var(--peach);
		top: 2rem;
		left: 1rem;
	}

	.login-deco.deco-2 {
		width: 120px;
	height: 120px;
		background: var(--sky);
		right: 2rem;
		top: 4rem;
	}

	.login-card {
		position: relative;
		background: white;
		padding: 2.5rem 2rem;
		border-radius: 2rem;
		width: 100%;
		max-width: 460px;
		box-shadow: var(--shadow-cartoon-lg);
		border: var(--border-thick);
		text-align: center;
		margin: 1rem;
	}

	.card-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.55rem 1rem;
		border-radius: 999px;
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		font-size: 0.9rem;
		border: var(--border-thin);
		position: absolute;
		top: -16px;
		left: 50%;
		transform: translateX(-50%);
		box-shadow: var(--shadow-cartoon-sm);
	}

	.login-card h2 {
		font-family: var(--font-display);
		font-size: 2rem;
		margin: 0.75rem 0 0.35rem;
		color: var(--ink);
	}

	.subtitle {
		color: var(--warm-gray);
		margin-bottom: 1.6rem;
		line-height: 1.5;
	}

	.input-group {
		display: flex;
		flex-direction: column;
		margin-bottom: 1.2rem;
		text-align: left;
		gap: 0.35rem;
	}

	.input-group label {
		font-size: 0.98rem;
		font-weight: 700;
		color: var(--ink);
	}

	.input-group input {
		width: 100%;
		padding: 0.95rem 1rem;
		border-radius: 1.25rem;
		border: var(--border-medium);
		border-color: var(--light-gray);
		background: #fff;
		transition: border-color 0.2s ease, box-shadow 0.2s ease;
	}

	.input-group input:focus {
		border-color: var(--mustard-dark);
		box-shadow: 0 0 0 3px rgba(245, 183, 49, 0.16);
		outline: none;
	}

	.password-wrapper {
		position: relative;
	}

	.password-wrapper input {
		padding-right: 3.5rem;
	}

	.toggle-password {
		position: absolute;
		right: 0.9rem;
		top: 50%;
		transform: translateY(-50%);
		cursor: pointer;
		font-size: 1.1rem;
		user-select: none;
		color: var(--warm-gray);
		transition: color 0.2s ease;
	}

	.toggle-password:hover {
		color: var(--mustard-dark);
	}

	.password-guidelines {
		text-align: left;
		background: var(--cream);
		border-radius: 1.25rem;
		border: var(--border-medium);
		border-color: var(--light-gray);
	}

	.password-guidelines .row > div {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		font-size: 0.82rem;
	}

	.x-small {
		font-size: 0.78rem;
	}

	.btn-login {
		width: 100%;
		padding: 1rem 1.2rem;
		border-radius: var(--radius-pill);
		border: var(--border-thick);
		background: linear-gradient(135deg, var(--mustard), var(--mustard-dark));
		color: var(--ink);
		font-weight: 800;
		cursor: pointer;
		transition: transform 0.2s var(--bounce), box-shadow 0.2s ease, background 0.2s ease;
		box-shadow: var(--shadow-cartoon-sm);
		margin-top: 0.5rem;
	}

	.btn-login:hover:not(:disabled) {
		background: linear-gradient(135deg, var(--coral), var(--coral-dark));
		color: white;
		transform: translateY(-2px);
		box-shadow: var(--shadow-hover);
	}

	.footer-text {
		margin-top: 1.6rem;
		font-size: 0.95rem;
		color: var(--warm-gray);
	}

	.footer-text a {
		color: var(--teal-dark);
		font-weight: 700;
	}

	.footer-text a:hover {
		text-decoration: underline;
	}

	.error-text {
		text-align: left;
	}

	.btn-login:disabled {
		background: var(--light-gray);
		color: var(--warm-gray);
		cursor: not-allowed;
		box-shadow: none;
		transform: none;
	}

	@media (max-width: 620px) {
		.login-card {
			padding: 2rem 1.5rem;
		}

		.login-deco.deco-1,
		.login-deco.deco-2 {
			opacity: 0.18;
		}
	}

	.btn-login:hover {
		transform: translateY(-3px);
		box-shadow: 0 12px 30px rgba(13, 110, 253, 0.4);
	}

	.footer-text {
		margin-top: 1.5rem;
		font-size: 0.9rem;
		color: #6c757d;
	}

	.footer-text a {
		color: #0d6efd;
		text-decoration: none;
		font-weight: 600;
	}

	.footer-text a:hover {
		text-decoration: underline;
	}

	@media (max-width: 480px) {
		.login-card {
			padding: 2rem;
		}
	}
	#admin-login {
		background: linear-gradient(135deg, #b89a14, #ecd75f);
		color: #333;
		box-shadow: 0 8px 20px rgba(184, 154, 20, 0.3);
	}

	.password-guidelines {
		text-align: left;
		background-color: #f8f9fa !important;
	}

	.x-small {
		font-size: 0.75rem;
	}

	.password-guidelines .row > div {
		display: flex;
		align-items: center;
		gap: 5px;
		transition: all 0.3s ease;
	}

	.error-text {
		text-align: left;
	}

	.btn-login:disabled {
		background: #e9ecef;
		color: #adb5bd;
		cursor: not-allowed;
		box-shadow: none;
		transform: none;
	}

	/* Google button styles */
	.google-signin-wrapper {
		position: relative;
	}

	/* Show and style the SDK-inserted Google button */
	#googleSignInDiv {
		display: inline-block;
		position: static;
	}

	/* Ensure wrapper children display so the SDK button is visible */
	#googleSignInDiv > div,
	#googleSignInDiv > div > div {
		display: inline-block !important;
	}

	#googleSignInDiv button,
	#googleSignInDiv div[role="button"] {
		display: inline-flex !important;
		align-items: center !important;
		gap: .6rem !important;
		border: 1px solid #e6edf3 !important;
		padding: 10px 16px !important;
		border-radius: 12px !important;
		background: linear-gradient(90deg, #ffffff 0%, #fbfdff 100%) !important;
		color: #202124 !important;
		font-weight: 700 !important;
		font-size: 0.95rem !important;
		cursor: pointer !important;
		box-shadow: 0 8px 22px rgba(16,24,40,0.06) !important;
		transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease !important;
	}

	#googleSignInDiv button:hover,
	#googleSignInDiv div[role="button"]:hover {
		transform: translateY(-3px) !important;
		box-shadow: 0 12px 30px rgba(16,24,40,0.10) !important;
	}

	#googleSignInDiv button:active,
	#googleSignInDiv div[role="button"]:active {
		transform: translateY(-1px) !important;
	}

	#googleSignInDiv button:focus,
	#googleSignInDiv div[role="button"]:focus {
		outline: 3px solid rgba(66,133,244,0.15) !important;
		outline-offset: 2px !important;
	}

	#googleSignInDiv img { height: 18px; width: 18px; }

	.google-missing { font-size: 0.92rem; }
</style>