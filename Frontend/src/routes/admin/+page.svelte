<script>
	import { onMount, tick } from 'svelte';
	import { Grid, h } from 'gridjs';
	import 'gridjs/dist/theme/mermaid.css';
	import Swal from 'sweetalert2';

	import { getUsers, createUser, updateUser, deleteUser } from '../../api/user_service.js';
	import AdminNavbar from '$lib/components/AdminNavbar.svelte';
	import { getUserRoleLabel, roleLabelToId } from '$lib/utils/roles.js';

	let users = [];
	let editUserId = null;
	let grid;
	let sortOrder = 'recent'; // 'recent' or 'alphabetical'

	let newUser = {
		name: '',
		last_name: '',
		email: '',
		password: '',
		role: 'Usuario',
		status: 'Activo'
	};

	// =========================
	// LOAD USERS
	// =========================
	onMount(async () => {
		await loadUsers();
	});

	async function loadUsers() {
		try {
			const response = await getUsers();
			users = response.data ?? response;

			await tick();
			renderGrid();
		} catch (error) {
			console.error('Error cargando usuarios:', error);
		}
	}

	// =========================
	// GRID (FORMA CORRECTA)
	// =========================
	function renderGrid() {
		if (grid) grid.destroy();

		grid = new Grid({
			columns: [
				'Nombre',
				'Apellido',
				'Correo',
				'Rol',
				{ name: 'Fecha Registro', sort: true },
				{
					name: 'Acciones',
					formatter: (_, row) => {
						const user = row.cells[5]?.data;

						if (!user) return '';

						return h('div', {}, [
							h(
								'button',
								{
									className: 'btn btn-sm btn-warning me-1',
									onClick: () => startEdit(user)
								},
								'Editar'
							),
							h(
								'button',
								{
									className: 'btn btn-sm btn-danger',
									onClick: () => removeUser(user.id)
								},
								'Eliminar'
							)
						]);
					}
				}
			],
			data: [...users]
				.sort((a, b) => {
					if (sortOrder === 'recent') {
						return new Date(b.created_at) - new Date(a.created_at);
					}
					return a.name.localeCompare(b.name);
				})
				.map((u) => [
					u.name,
					u.last_name,
					u.email,
					getUserRoleLabel(u),
					u.created_at ? new Date(u.created_at).toLocaleDateString('es-CO') : '—',
					u
				]),
			search: true,
			sort: true,
			pagination: { limit: 5 }
		});

		grid.render(document.getElementById('table-wrapper'));
	}

	// =========================
	// CRUD
	// =========================
	async function addUser() {
		// Validar campos obligatorios
		if (!newUser.name || !newUser.last_name || !newUser.email || !newUser.password) {
			Swal.fire({
				title: 'Campos incompletos',
				text: 'Por favor, rellena todos los campos, incluyendo la contraseña.',
				icon: 'warning'
			});
			return;
		}

		const userData = {
			name: newUser.name,
			last_name: newUser.last_name,
			email: newUser.email,
			password: newUser.password,
			role_id: roleLabelToId(newUser.role)
		};

		try {
			await createUser(userData);
			
			await Swal.fire({
				title: '¡Usuario Creado!',
				text: `El usuario ${userData.name} ha sido registrado correctamente.`,
				icon: 'success',
				timer: 2000,
				showConfirmButton: false
			});

			await loadUsers();
			resetForm();
		} catch (error) {
			console.error('Error creando usuario:', error);
			Swal.fire({
				title: 'Error',
				text: error.message || 'No se pudo crear el usuario. Verifica si el correo ya existe.',
				icon: 'error'
			});
		}
	}

	async function removeUser(id) {
		const result = await Swal.fire({
			title: '¿Eliminar usuario?',
			text: 'Esta acción no se puede deshacer',
			icon: 'warning',
			showCancelButton: true,
			confirmButtonText: 'Sí, eliminar',
			cancelButtonText: 'Cancelar'
		});

		if (!result.isConfirmed) return;

		try {
			await deleteUser(id);

			await Swal.fire({
				title: 'Eliminado',
				text: 'El usuario fue eliminado correctamente',
				icon: 'success'
			});

			await loadUsers();
		} catch (error) {
			console.error('Error eliminando usuario:', error);

			Swal.fire({
				title: 'Error',
				text: 'No se pudo eliminar el usuario',
				icon: 'error'
			});
		}
	}

	function startEdit(user) {
		editUserId = user.id;

		newUser = {
			name: user.name,
			last_name: user.last_name,
			email: user.email,
			password: '',
			role: getUserRoleLabel(user),
			status: user.status ?? 'Activo'
		};
	}

	async function saveEdit() {
		const userData = {
			name: newUser.name,
			last_name: newUser.last_name,
			email: newUser.email,
			role_id: roleLabelToId(newUser.role)
		};

		if (newUser.password && newUser.password.length > 0) {
			userData.password = newUser.password;
		}

		try {
			await updateUser(editUserId, userData);
			await loadUsers();
			resetForm();
			editUserId = null;
		} catch (error) {
			console.error('Error actualizando usuario:', error);
		}
	}

	function cancelEdit() {
		editUserId = null;
		resetForm();
	}

	function resetForm() {
		newUser = {
			name: '',
			last_name: '',
			email: '',
			password: '',
			role: 'Usuario',
			status: 'Activo'
		};
	}
</script>

<AdminNavbar />

<section class="container my-4">
	<div class="d-flex justify-content-between align-items-center mb-4">
		<h2 class="mb-0">Gestión de Usuarios</h2>
		<div class="d-flex align-items-center gap-2">
			<span class="text-muted small">Ordenar por:</span>
			<select class="form-select form-select-sm w-auto" bind:value={sortOrder} on:change={renderGrid}>
				<option value="recent">Más recientes</option>
				<option value="alphabetical">Nombre (A-Z)</option>
			</select>
		</div>
	</div>

	<!-- FORMULARIO -->
	<div class="card mb-4 p-3">
		<h5>{editUserId ? 'Editar Usuario' : 'Agregar Usuario'}</h5>

		<div class="row g-2">
			<div class="col-md-2">
				<input class="form-control" placeholder="Nombre" bind:value={newUser.name} />
			</div>

			<div class="col-md-2">
				<input class="form-control" placeholder="Apellido" bind:value={newUser.last_name} />
			</div>

			<div class="col-md-3">
				<input class="form-control" type="email" placeholder="Correo" bind:value={newUser.email} />
			</div>

			<div class="col-md-2">
				<input
					class="form-control"
					type="password"
					placeholder="Contraseña"
					bind:value={newUser.password}
				/>
			</div>

			<div class="col-md-2">
				<select class="form-select" bind:value={newUser.role}>
					<option>Admin</option>
					<option>Usuario</option>						<option>SUPERADMIN</option>				</select>
			</div>
		</div>

		<div class="mt-3">
			{#if editUserId}
				<button class="btn btn-success me-2 px-4 shadow-sm" on:click={saveEdit}>
					<i class="bi bi-save me-1"></i> Guardar Cambios
				</button>
				<button class="btn btn-light border px-4" on:click={cancelEdit}>Cancelar</button>
			{:else}
				<button class="btn btn-primary px-4 shadow-sm" on:click={addUser}>
					<i class="bi bi-person-plus-fill me-1"></i> Agregar Usuario
				</button>
			{/if}
		</div>
	</div>

	<!-- DATATABLE -->
	<div id="table-wrapper"></div>
</section>
