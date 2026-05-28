<script>
	import { goto } from '$app/navigation';
	import { clearAuth } from '$lib/stores/auth.js';
	import Swal from 'sweetalert2';

	async function logout() {
		const result = await Swal.fire({
			title: '¿Cerrar sesión?',
			text: '¿Estás seguro de que deseas salir del panel administrativo?',
			icon: 'question',
			showCancelButton: true,
			confirmButtonColor: '#F5B731',
			cancelButtonColor: '#FF6B6B',
			confirmButtonText: 'Sí, salir',
			cancelButtonText: 'Cancelar',
			background: '#FFF8F0',
			customClass: {
				confirmButton: 'swal-btn-confirm',
				cancelButton: 'swal-btn-cancel',
				popup: 'swal-cartoon-popup'
			},
			buttonsStyling: false
		});

		if (result.isConfirmed) {
			clearAuth();
			goto('/login');
		}
	}
</script>

<nav class="navbar navbar-expand-lg admin-navbar-cartoon py-3">
	<div class="container-fluid px-lg-4">
		<a class="navbar-brand admin-brand" href="/admin">
			<span class="admin-icon">🛡️</span>
			<span class="admin-text">Panel Admin</span>
		</a>

		<button
			class="navbar-toggler cartoon-toggler-admin"
			type="button"
			data-bs-toggle="collapse"
			data-bs-target="#adminNavbarNav"
		>
			<span class="bi bi-list"></span>
		</button>

		<div class="collapse navbar-collapse" id="adminNavbarNav">
			<ul class="navbar-nav me-auto align-items-center">
				<li class="nav-item">
					<a class="nav-link admin-nav-link" href="/admin">
						<i class="bi bi-people-fill"></i> Usuarios
					</a>
				</li>
				<li class="nav-item">
					<a class="nav-link admin-nav-link" href="/admin/dashboard">
						<i class="bi bi-graph-up-arrow"></i> Dashboard
					</a>
				</li>
				<li class="nav-item">
					<a class="nav-link admin-nav-link" href="/admin/mascotas">
						<i class="bi bi-dog"></i> Mascotas
					</a>
				</li><li class="nav-item">
					<a class="nav-link admin-nav-link" href="/admin/adopcion">
						<i class="bi bi-heart-fill"></i> Adopción
					</a>
				</li>
				<li class="nav-item">
					<a class="nav-link admin-nav-link" href="/admin/historial">
						<i class="bi bi-journal-text"></i> Historial
					</a>
				</li>
			</ul>

			<div class="d-flex align-items-center gap-3">
				<div class="dropdown">
					<button
						class="btn btn-view-site dropdown-toggle shadow-sm"
						type="button"
						data-bs-toggle="dropdown"
						aria-expanded="false"
					>
						<i class="bi bi-eye-fill me-1"></i> Ver Sitio
					</button>
					<ul class="dropdown-menu dropdown-menu-end cartoon-dropdown p-2 mt-2">
						<li>
							<a class="dropdown-item cartoon-dropdown-item py-2" href="/">
								<i class="bi bi-house-door me-2"></i> Inicio
							</a>
						</li>
						<li>
							<a class="dropdown-item cartoon-dropdown-item py-2" href="/usuarios/mascotas">
								<i class="bi bi-paw me-2"></i> Ver Mascotas
							</a>
						</li>
						<li>
							<a class="dropdown-item cartoon-dropdown-item py-2" href="/usuarios/publicar">
								<i class="bi bi-plus-circle me-2"></i> Publicar Mascota
							</a>
						</li></ul>
				</div>
				<button class="btn btn-logout-admin shadow-sm" on:click={logout}>
					<i class="bi bi-box-arrow-right"></i>
				</button>
			</div>
		</div>
	</div>
</nav>

<style>
	.admin-navbar-cartoon {
		background: var(--ink);
		border-bottom: 4px solid var(--ink);
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
	}

	.admin-brand {
		font-family: var(--font-display);
		font-weight: 800;
		color: white !important;
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 1.4rem;
	}

	.admin-icon {
		font-size: 1.5rem;
		filter: drop-shadow(2px 2px 0 rgba(0, 0, 0, 0.5));
	}

	.admin-text {
		background: linear-gradient(135deg, var(--mustard) 0%, #fff 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.admin-nav-link {
		color: rgba(255, 255, 255, 0.8) !important;
		font-weight: 600;
		font-family: var(--font-display);
		padding: 0.5rem 1rem !important;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.admin-nav-link:hover {
		color: var(--mustard) !important;
		transform: translateY(-2px);
	}

	.admin-nav-link i {
		font-size: 1.1rem;
		opacity: 0.7;
	}

	.btn-view-site {
		background: var(--mustard);
		color: var(--ink);
		font-weight: 700;
		font-family: var(--font-display);
		border: 2px solid var(--ink);
		border-radius: 12px;
		padding: 6px 16px;
		transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		box-shadow: 3px 3px 0 var(--ink);
	}

	.btn-view-site:hover {
		transform: translateY(-3px);
		box-shadow: 5px 5px 0 var(--ink);
		background: var(--coral);
		color: white;
	}

	.btn-logout-admin {
		background: #ff6b6b;
		color: white;
		border: 2px solid var(--ink);
		border-radius: 12px;
		padding: 6px 12px;
		box-shadow: 3px 3px 0 var(--ink);
		transition: all 0.3s ease;
	}

	.btn-logout-admin:hover {
		background: #ff4747;
		transform: scale(1.1) rotate(5deg);
		box-shadow: 4px 4px 0 var(--ink);
	}

	.cartoon-toggler-admin {
		border: 2px solid white;
		color: white;
		padding: 4px 8px;
		border-radius: 8px;
	}

	/* SweetAlert custom (Copy from main navbar for consistency) */
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

