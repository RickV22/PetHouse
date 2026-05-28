<script>
	import { onMount, tick } from 'svelte';
	import Swal from 'sweetalert2';
	import { fly, fade } from 'svelte/transition';
	import AdminNavbar from '$lib/components/AdminNavbar.svelte';
	import { getAuditLogs, exportAuditLogsCSV } from '../../../api/audit_service.js';
	import API_URL, { getAuthHeaders } from '../../../api/api.js';

	let auditLogs = [];
	let filteredLogs = [];
	let loading = false;
	let showDetailModal = false;
	let selectedLog = null;

	// Filters
	let filterAction = '';
	let filterResource = '';
	let filterUser = '';
	let startDate = '';
	let endDate = '';
	let searchTerm = '';

	// Pagination
	let currentPage = 1;
	let pageSize = 20;
	let pageSizeOptions = [20, 50, 100];

	onMount(async () => {
		await fetchAuditLogs();
	});

	async function fetchAuditLogs() {
		loading = true;
		try {
			const params = {
				limit: pageSize,
				offset: (currentPage - 1) * pageSize
			};

			if (filterAction) params.action = filterAction;
			if (filterResource) params.resource = filterResource;
			if (filterUser) params.user_id = filterUser;
			if (startDate) params.start_date = new Date(startDate).toISOString();
			if (endDate) params.end_date = new Date(endDate).toISOString();

			const response = await getAuditLogs(params);
			auditLogs = Array.isArray(response) ? response : response.data || [];

			// Enriquecer con nombres de usuario para mejor lectura
			try {
				const headers = getAuthHeaders();
				const usersRes = await fetch(`${API_URL}/users/`, { headers });
				if (usersRes.ok) {
					const users = await usersRes.json();
					const userMap = {};
					users.forEach(u => { userMap[u.id] = `${u.name} ${u.last_name || ''}`.trim(); });
					auditLogs = auditLogs.map(l => ({ ...l, user_name: l.user_id ? userMap[l.user_id] || `Usuario #${l.user_id}` : 'Sistema' }));
				} else {
					console.warn('GET /users/ failed:', usersRes.status);
					// Fallback: fetch individual users by id
					const ids = Array.from(new Set(auditLogs.map(l => l.user_id).filter(Boolean)));
					const userMap = {};
					await Promise.all(ids.map(async (id) => {
						try {
							const r = await fetch(`${API_URL}/users/${id}`, { headers });
							if (r.ok) {
								const u = await r.json();
								userMap[u.id] = `${u.name} ${u.last_name || ''}`.trim();
							}
						} catch (err) {
							console.warn('Failed to fetch user', id, err);
						}
					}));
					auditLogs = auditLogs.map(l => ({ ...l, user_name: l.user_id ? userMap[l.user_id] || `Usuario #${l.user_id}` : 'Sistema' }));
				}
			} catch (e) {
				console.error('User enrichment failed:', e);
				auditLogs = auditLogs.map(l => ({ ...l, user_name: l.user_id ? `Usuario #${l.user_id}` : 'Sistema' }));
			}

			applySearch();
		} catch (error) {
			console.error('Error fetching audit logs:', error);
			Swal.fire({
				icon: 'error',
				title: 'Error de Carga',
				text: 'No se pudo obtener el historial. Verifica tu conexión.',
				confirmButtonColor: '#ff6b6b'
			});
		} finally {
			loading = false;
		}
	}

	function applySearch() {
		if (searchTerm.trim() === '') {
			filteredLogs = auditLogs;
		} else {
			const term = searchTerm.toLowerCase();
			filteredLogs = auditLogs.filter(
				(log) =>
					log.action.toLowerCase().includes(term) ||
					log.resource.toLowerCase().includes(term) ||
					(log.details && log.details.toLowerCase().includes(term))
			);
		}
	}

	async function exportToCSV() {
		try {
			const params = {};
			if (filterAction) params.action = filterAction;
			if (filterResource) params.resource = filterResource;
			if (filterUser) params.user_id = filterUser;
			if (startDate) params.start_date = new Date(startDate).toISOString();
			if (endDate) params.end_date = new Date(endDate).toISOString();

			const data = await exportAuditLogsCSV(params);

			const blob = new Blob([data.content], { type: 'text/csv;charset=utf-8;' });
			const url = URL.createObjectURL(blob);
			const element = document.createElement('a');
			element.setAttribute('href', url);
			element.setAttribute('download', data.filename);
			element.style.display = 'none';
			document.body.appendChild(element);
			element.click();
			document.body.removeChild(element);
			URL.revokeObjectURL(url);

			Swal.fire({
				icon: 'success',
				title: '¡Exportado!',
				text: 'El archivo CSV se ha descargado.',
				confirmButtonColor: '#4361ee'
			});
		} catch (error) {
			console.error('Error:', error);
			Swal.fire('Error', 'No se pudo exportar el historial.', 'error');
		}
	}

	async function resetFilters() {
		filterAction = '';
		filterResource = '';
		filterUser = '';
		startDate = '';
		endDate = '';
		searchTerm = '';
		currentPage = 1;
		await fetchAuditLogs();
	}

	function viewDetails(log) {
		selectedLog = log;
		showDetailModal = true;
	}

	function formatDate(dateString) {
		if (!dateString) return '-';
		return new Date(dateString).toLocaleString('es-CO', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getActionBadge(action) {
		const config = {
			create: { class: 'badge-create', label: 'Crear', icon: 'bi-plus-circle' },
			update: { class: 'badge-update', label: 'Editar', icon: 'bi-pencil' },
			delete: { class: 'badge-delete', label: 'Borrar', icon: 'bi-trash' },
			login: { class: 'badge-login', label: 'Login', icon: 'bi-box-arrow-in-right' },
			login_failed: { class: 'badge-failed', label: 'Fallo', icon: 'bi-exclamation-triangle' }
		};
		return config[action] || { class: 'bg-secondary', label: action, icon: 'bi-dot' };
	}
</script>

<AdminNavbar />

<main class="history-page py-5">
	<div class="container" in:fade>
		<header
			class="d-flex flex-column flex-md-row justify-content-between align-items-end mb-4 gap-3"
		>
			<div in:fly={{ x: -20, duration: 600 }}>
				<span class="history-badge mb-2">📋 Auditoría General</span>
				<h1 class="fw-bold display-6 mb-0">Historial de Actividad</h1>
				<p class="text-muted">Monitorea cada cambio y acción realizada en el sistema.</p>
			</div>

			<div class="d-flex gap-2">
				<button class="btn btn-export shadow-sm" on:click={exportToCSV}>
					<i class="bi bi-download me-2"></i> Exportar CSV
				</button>
			</div>
		</header>

		<!-- Filtros Premium -->
		<div class="card filter-card mb-4 p-4 shadow-sm" in:fly={{ y: 20, duration: 600, delay: 100 }}>
			<div class="row g-3">
				<div class="col-md-3">
					<label class="cartoon-label">Acción</label>
					<select class="form-select cartoon-input" bind:value={filterAction}>
						<option value="">Todas las acciones</option>
						<option value="create">Crear</option>
						<option value="update">Actualizar</option>
						<option value="delete">Eliminar</option>
						<option value="login">Inicio Sesión</option>
					</select>
				</div>
				<div class="col-md-3">
					<label class="cartoon-label">Recurso</label>
					<select class="form-select cartoon-input" bind:value={filterResource}>
						<option value="">Todos los recursos</option>
						<option value="user">Usuarios</option>
						<option value="pet">Mascotas</option>
						<option value="adoption">Adopciones</option>
					</select>
				</div>
				<div class="col-md-4">
					<label class="cartoon-label">Rango de Fechas</label>
					<div class="input-group">
						<input type="date" class="form-control cartoon-input" bind:value={startDate} />
						<span class="input-group-text bg-transparent border-0">al</span>
						<input type="date" class="form-control cartoon-input" bind:value={endDate} />
					</div>
				</div>
				<div class="col-md-2 d-flex align-items-end gap-2">
					<button class="btn btn-search w-100" on:click={fetchAuditLogs}>
						<i class="bi bi-search"></i>
					</button>
					<button class="btn btn-outline-secondary rounded-pill" on:click={resetFilters}>
						<i class="bi bi-arrow-counterclockwise"></i>
					</button>
				</div>
			</div>
		</div>

		<!-- Búsqueda rápida -->
		<div class="search-box mb-4" in:fly={{ y: 20, duration: 600, delay: 200 }}>
			<input
				type="text"
				class="form-control form-control-lg cartoon-input ps-4"
				placeholder="🔍 Buscar por detalles, recurso o usuario..."
				bind:value={searchTerm}
				on:input={applySearch}
			/>
		</div>

		<!-- Tabla Premium -->
		<div
			class="card border-0 shadow-sm rounded-4 overflow-hidden"
			in:fly={{ y: 20, duration: 600, delay: 300 }}
		>
			<div class="table-responsive">
				<table class="table table-hover align-middle mb-0">
					<thead class="table-ink text-white">
						<tr>
							<th class="ps-4">Usuario</th>
							<th>Acción</th>
							<th>Recurso</th>
							<th>Fecha y Hora</th>
							<th>Estado</th>
							<th class="text-center pe-4">Detalle</th>
						</tr>
					</thead>
					<tbody>
						{#if loading}
							<tr>
								<td colspan="6" class="text-center py-5">
									<div class="spinner-border text-mustard" role="status"></div>
									<p class="mt-2 fw-bold">Cargando bitácora...</p>
								</td>
							</tr>
						{:else if filteredLogs.length === 0}
							<tr>
								<td colspan="6" class="text-center py-5 text-muted">
									<i class="bi bi-journal-x display-4 d-block mb-3 opacity-20"></i>
									No se encontraron registros con esos filtros.
								</td>
							</tr>
						{:else}
							{#each filteredLogs as log (log.id)}
								<tr class="log-row">
									<td class="ps-4">
										<div class="d-flex align-items-center gap-2">
											<div class="user-avatar-small">
												{log.user_id ? 'U' : 'S'}
											</div>
											<div>
												<div class="fw-bold small">
													{log.user_name || (log.user_id ? `Usuario #${log.user_id}` : 'Sistema')}
												</div>
												<div class="text-muted x-small">{log.ip_address || 'Sin IP'}</div>
											</div>
										</div>
									</td>
									<td>
										<span class="badge-cartoon {getActionBadge(log.action).class}">
											<i class="bi {getActionBadge(log.action).icon} me-1"></i>
											{getActionBadge(log.action).label}
										</span>
									</td>
									<td>
										<span class="fw-bold text-dark">{log.resource}</span>
										<span class="text-muted small">#{log.resource_id || '-'}</span>
									</td>
									<td class="text-muted small">{formatDate(log.timestamp)}</td>
									<td>
										{#if log.status === 'success'}
											<span class="text-success small fw-bold"
												><i class="bi bi-check-circle-fill"></i> Ok</span
											>
										{:else}
											<span class="text-danger small fw-bold"
												><i class="bi bi-x-circle-fill"></i> Error</span
											>
										{/if}
									</td>
									<td class="text-center pe-4">
										<button class="btn btn-detail-circle" on:click={() => viewDetails(log)}>
											<i class="bi bi-eye"></i>
										</button>
									</td>
								</tr>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</main>

<!-- Modal Detalle Cartoon -->
{#if showDetailModal && selectedLog}
	<div class="modal d-block" tabindex="-1" in:fade>
		<div class="modal-dialog modal-dialog-centered modal-lg">
			<div class="modal-content cartoon-modal">
				<div class="modal-header border-0 pb-0">
					<h5 class="fw-bold mb-0">Detalle del Registro #{selectedLog.id}</h5>
					<button type="button" class="btn-close" on:click={() => (showDetailModal = false)}
					></button>
				</div>
				<div class="modal-body">
					<div class="row g-4">
						<div class="col-md-6">
							<div class="detail-item p-3 rounded-4">
								<label class="x-small text-muted text-uppercase fw-bold">Actor</label>
								<div class="fw-bold">
									{selectedLog.user_name || (selectedLog.user_id ? `Usuario ID #${selectedLog.user_id}` : 'Proceso del Sistema')}
								</div>
							</div>
						</div>
						<div class="col-md-6">
							<div class="detail-item p-3 rounded-4">
								<label class="x-small text-muted text-uppercase fw-bold">Fecha Exacta</label>
								<div class="fw-bold">{formatDate(selectedLog.timestamp)}</div>
							</div>
						</div>
						<div class="col-12">
							<div class="detail-item p-3 rounded-4">
								<label class="x-small text-muted text-uppercase fw-bold">Cambios / Datos</label>
								<pre class="changes-pre mt-2">{JSON.stringify(
										selectedLog.changes || selectedLog.details,
										null,
										2
									)}</pre>
							</div>
						</div>
					</div>
				</div>
				<div class="modal-footer border-0">
					<button
						type="button"
						class="btn btn-ink text-white px-4 rounded-pill"
						on:click={() => (showDetailModal = false)}>Cerrar</button
					>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<style>
	.history-page {
		background: var(--cream);
		min-height: 100vh;
		font-family: var(--font-body);
	}

	.history-badge {
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		padding: 4px 16px;
		border-radius: 50px;
		display: inline-block;
		border: 2px solid var(--ink);
		font-size: 0.85rem;
	}

	.filter-card {
		border: 3px solid var(--ink);
		border-radius: 20px;
		box-shadow: 6px 6px 0 var(--ink);
	}

	.cartoon-label {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 0.9rem;
		color: var(--ink);
		margin-bottom: 5px;
	}

	.cartoon-input {
		border: 2.5px solid var(--ink) !important;
		border-radius: 12px !important;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.btn-search {
		background: var(--coral);
		color: white;
		border: 2.5px solid var(--ink);
		border-radius: 12px;
		height: 45px;
		box-shadow: 3px 3px 0 var(--ink);
		transition: all 0.2s;
	}

	.btn-search:hover {
		transform: translate(-2px, -2px);
		box-shadow: 5px 5px 0 var(--ink);
	}

	.btn-export {
		background: white;
		border: 2.5px solid var(--ink);
		border-radius: 50px;
		font-weight: 700;
		padding: 8px 20px;
		box-shadow: 4px 4px 0 var(--ink);
		transition: all 0.2s;
	}

	.btn-export:hover {
		background: var(--mustard);
		transform: translateY(-2px);
	}

	.table-ink {
		background: var(--ink);
	}

	.table-ink th {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 0.8rem;
		letter-spacing: 1px;
		border: none;
		padding: 15px;
	}

	.log-row:hover {
		background-color: rgba(245, 183, 49, 0.05);
	}

	.user-avatar-small {
		width: 32px;
		height: 32px;
		background: var(--mustard);
		border: 2px solid var(--ink);
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 900;
		font-size: 0.8rem;
	}

	.badge-cartoon {
		padding: 4px 12px;
		border-radius: 8px;
		font-size: 0.75rem;
		font-weight: 800;
		border: 2px solid var(--ink);
		display: inline-flex;
		align-items: center;
	}

	.badge-create {
		background: #c8e6c9;
		color: #2e7d32;
	}
	.badge-update {
		background: #bbdefb;
		color: #1565c0;
	}
	.badge-delete {
		background: #ffcdd2;
		color: #c62828;
	}
	.badge-login {
		background: #e1bee7;
		color: #6a1b9a;
	}
	.badge-failed {
		background: #fff9c4;
		color: #f9a825;
	}

	.btn-detail-circle {
		width: 35px;
		height: 35px;
		border-radius: 50%;
		border: 2px solid var(--ink);
		background: white;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.btn-detail-circle:hover {
		background: var(--mustard);
		transform: scale(1.1);
	}

	.cartoon-modal {
		border: 4px solid var(--ink);
		border-radius: 30px;
		box-shadow: 10px 10px 0 var(--ink);
	}

	.detail-item {
		background: #f8f9fa;
		border: 2px solid #eee;
	}

	.changes-pre {
		background: #222;
		color: #00ff00;
		padding: 15px;
		border-radius: 10px;
		max-height: 300px;
		overflow-y: auto;
		font-size: 0.8rem;
	}

	.btn-ink {
		background: var(--ink);
		color: white;
	}

	.x-small {
		font-size: 0.7rem;
	}
	.opacity-20 {
		opacity: 0.2;
	}
</style>
