<script>
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { auth, clearAuth } from '$lib/stores/auth.js';
	import Swal from 'sweetalert2';
	export let showLogin = true;
	export let variant = 'default';

	let scrolled = false;
	let user = null;

	$: user = $auth?.user;

	onMount(() => {
		const handleScroll = () => {
			scrolled = window.scrollY > 30;
		};

		window.addEventListener('scroll', handleScroll);
		return () => window.removeEventListener('scroll', handleScroll);
	});

	async function logout() {
		const result = await Swal.fire({
			title: '¿Cerrar sesión?',
			text: '¿Estás seguro de que deseas salir de tu cuenta?',
			icon: 'question',
			showCancelButton: true,
			confirmButtonColor: '#F5B731',
			cancelButtonColor: '#FF6B6B',
			confirmButtonText: 'Sí, ¡nos vemos! 👋',
			cancelButtonText: 'Me quedo',
			background: '#FFF8F0',
			customClass: {
				confirmButton: 'swal-btn-confirm',
				cancelButton: 'swal-btn-cancel',
				popup: 'swal-cartoon-popup'
			},
			buttonsStyling: false
		});

		if (result.isConfirmed) {
			await Swal.fire({
				title: '¡Hasta pronto! 🐾',
				text: 'Cerrando tu sesión...',
				timer: 1200,
				timerProgressBar: true,
				showConfirmButton: false,
				background: '#FFF8F0',
				didOpen: () => {
					Swal.showLoading();
				}
			});

			clearAuth();
			goto('/');
		}
	}
</script>

<nav
	in:fly={{ y: -60, duration: 600 }}
	class="navbar navbar-expand-lg {scrolled ? 'navbar-scrolled' : 'navbar-top'}"
	class:login-navbar={variant === 'login'}
>
	<div class="container-fluid px-lg-5">
		<a class="navbar-brand brand-logo" href="/">
			<span class="logo-icon">🏠</span>
			<span class="logo-text">PetHouse</span>
		</a>

		<!-- svelte-ignore a11y_consider_explicit_label -->
		<button
			class="navbar-toggler cartoon-toggler"
			type="button"
			data-bs-toggle="collapse"
			data-bs-target="#navbarNav"
		>
			<span class="toggler-bar"></span>
			<span class="toggler-bar"></span>
			<span class="toggler-bar"></span>
		</button>

		<div class="collapse navbar-collapse" id="navbarNav">
			<ul class="navbar-nav ms-auto align-items-center me-0">
				<li class="nav-item">
					<a class="nav-link nav-custom px-3" href="/">
						<span class="nav-emoji">🏡</span> Inicio
					</a>
				</li>

				<li class="nav-item">
					<a class="nav-link nav-custom px-3" href="/usuarios/mascotas">
						<span class="nav-emoji">🐾</span> Mascotas
					</a>
				</li>

				<li class="nav-item">
					<a class="nav-link nav-custom px-3" href="/usuarios/publicar">
						<span class="nav-emoji">📝</span> Publicar
					</a>
				</li><li class="nav-item user-menu-item ms-lg-3 mt-3 mt-lg-0 pe-0">
					{#if user}
						<div class="dropdown">
							<button
								class="btn profile-trigger d-flex align-items-center gap-2"
								type="button"
								data-bs-toggle="dropdown"
								aria-expanded="false"
							>
								<div class="avatar-circle">
									{user.name.charAt(0).toUpperCase()}
								</div>
								<span class="user-name-label d-none d-xl-inline">{user.name}</span>
								<i class="bi bi-chevron-down small opacity-50"></i>
							</button>

							<ul class="dropdown-menu dropdown-menu-end cartoon-dropdown p-2 mt-2">
								<li class="px-3 py-2 border-bottom mb-2 user-info-header">
									<div class="fw-bold">{user.name} {user.last_name || ''}</div>
									<div class="text-muted small">{user.email}</div>
								</li>

								{#if user.role_id === 1}
									<li>
										<a class="dropdown-item cartoon-dropdown-item py-2" href="/admin">
											<i class="bi bi-speedometer2 me-2"></i> Panel Admin
										</a>
									</li>
								{/if}

								<li>
									<button
										class="dropdown-item cartoon-dropdown-item py-2 text-danger"
										on:click={logout}
									>
										<i class="bi bi-box-arrow-right me-2"></i> Cerrar Sesión
									</button>
								</li>
							</ul>
						</div>
					{:else if showLogin}
						<a href="/login" class="btn btn-login-cartoon px-4"> ¡Entrar! 🐶 </a>
					{/if}
				</li>
			</ul>
		</div>
	</div>
</nav>

<style>
	/* Logo cartoon */
	.logo-icon {
		font-size: 1.6rem;
		margin-right: 4px;
		display: inline-block;
		animation: wiggle 3s ease-in-out infinite;
	}

	.logo-text {
		background: linear-gradient(135deg, var(--coral) 0%, var(--mustard) 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	@keyframes wiggle {
		0%,
		100% {
			transform: rotate(0deg);
		}
		25% {
			transform: rotate(-5deg);
		}
		75% {
			transform: rotate(5deg);
		}
	}

	/* Toggler hamburger cartoon */
	.cartoon-toggler {
		display: none;
		border: 2.5px solid var(--ink);
		border-radius: 12px;
		padding: 6px 10px;
		background: var(--mustard);
		box-shadow: 3px 3px 0 var(--ink);
		transition: all 0.3s ease;
	}

	@media (max-width: 991.98px) {
		.cartoon-toggler {
			display: flex;
			flex-direction: column;
			gap: 4px;
		}
	}

	.cartoon-toggler:hover {
		transform: rotate(-5deg);
		background: var(--coral);
	}

	.toggler-bar {
		display: block;
		width: 22px;
		height: 3px;
		background: var(--ink);
		border-radius: 3px;
		transition: all 0.3s ease;
	}

	/* Nav emojis */
	.nav-emoji {
		font-size: 1.1rem;
		display: inline-block;
		transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
	}

	.nav-custom:hover .nav-emoji {
		transform: scale(1.3) rotate(-10deg);
	}

	/* Avatar cartoon */
	.avatar-circle {
		width: 40px;
		height: 40px;
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		font-family: var(--font-display);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1rem;
		border: 2.5px solid var(--ink);
		transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		box-shadow: 2px 2px 0 var(--ink);
	}

	.profile-trigger {
		background: var(--cream-dark);
		border: 2.5px solid var(--ink);
		padding: 4px 14px 4px 4px;
		border-radius: 50px;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
		box-shadow: 3px 3px 0 var(--ink);
		color: var(--ink);
		font-family: var(--font-display);
		font-weight: 700;
	}

	.profile-trigger:hover {
		background: var(--mustard);
		transform: translateY(-3px);
		box-shadow: 4px 4px 0 var(--ink);
	}

	.profile-trigger:hover .avatar-circle {
		transform: rotate(10deg) scale(1.1);
		background: var(--coral);
		color: white;
	}

	.user-name-label {
		color: var(--ink);
	}

	/* Dropdown cartoon */
	.cartoon-dropdown {
		border: 2.5px solid var(--ink) !important;
		border-radius: 16px !important;
		box-shadow: 5px 5px 0 var(--ink) !important;
		background: var(--cream) !important;
		animation: dropIn 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
		transform-origin: top right;
	}

	@keyframes dropIn {
		from {
			opacity: 0;
			transform: translateY(-10px) scale(0.9) rotate(3deg);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1) rotate(0deg);
		}
	}

	.user-info-header {
		border-color: var(--light-gray) !important;
	}

	.cartoon-dropdown-item {
		font-family: var(--font-display);
		font-weight: 600;
		border-radius: 10px !important;
		transition: all 0.2s ease;
		font-size: 0.95rem;
	}

	.cartoon-dropdown-item:hover {
		background-color: var(--mustard) !important;
		transform: translateX(6px);
		color: var(--ink) !important;
	}

	.cartoon-dropdown-item.text-danger:hover {
		background-color: #ffcdd2 !important;
		color: #b71c1c !important;
	}

	/* Botón login cartoon */
	.btn-login-cartoon {
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		font-family: var(--font-display);
		font-size: 1rem;
		border-radius: var(--radius-pill);
		border: 2.5px solid var(--ink);
		box-shadow: 3px 3px 0 var(--ink);
		transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
		position: relative;
	}

	.btn-login-cartoon:hover {
		transform: translateY(-3px) rotate(-2deg);
		box-shadow: 5px 5px 0 var(--ink);
		background: var(--coral);
		color: white;
	}

	.btn-login-cartoon:active {
		transform: translateY(1px);
		box-shadow: 1px 1px 0 var(--ink);
	}

	@media (max-width: 991.98px) {
		.user-menu-item {
			border-top: 2px dashed var(--light-gray);
			padding-top: 1.5rem;
			margin-top: 1rem;
		}
		.profile-trigger {
			width: 100%;
			justify-content: center;
			padding: 8px;
		}
	}

	/* SweetAlert custom */
	:global(.swal-cartoon-popup) {
		border-radius: 20px !important;
		border: 3px solid var(--ink) !important;
		box-shadow: 6px 6px 0 var(--ink) !important;
		font-family: var(--font-display) !important;
	}
	:global(.swal-btn-confirm) {
		background: var(--mustard) !important;
		color: var(--ink) !important;
		border: 2.5px solid var(--ink) !important;
		border-radius: 50px !important;
		padding: 10px 24px !important;
		font-weight: 700 !important;
		font-family: var(--font-display) !important;
		box-shadow: 3px 3px 0 var(--ink) !important;
		margin-right: 10px !important;
	}
	:global(.swal-btn-cancel) {
		background: white !important;
		color: var(--coral) !important;
		border: 2.5px solid var(--ink) !important;
		border-radius: 50px !important;
		padding: 10px 24px !important;
		font-weight: 700 !important;
		font-family: var(--font-display) !important;
		box-shadow: 3px 3px 0 var(--ink) !important;
	}
</style>

