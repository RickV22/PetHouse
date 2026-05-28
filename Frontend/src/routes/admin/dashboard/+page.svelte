<script>
	import PowerBIReport from '$lib/components/PowerBIReport.svelte';
	import AdminNavbar from '$lib/components/AdminNavbar.svelte';
</script>

<AdminNavbar />

<main class="dashboard-container py-5">
	<div class="container">
		<!-- Header -->
		<header class="row align-items-center mb-5">
			<div class="col-md-8 text-center text-md-start">
				<h1 class="display-5 fw-bold text-dark mb-2">Graficas<span class="text-primary">PowerBI</span></h1>
				<h1 class="display-5 fw-bold text-dark mb-2">Armando pon mas graficas compae</h1>
				<p class="lead text-muted">Panel de control con métricas estratégicas y visualización de datos.</p>
			</div>
			<div class="col-md-4 mt-4 mt-md-0">
				<div class="stats-overview-card p-3 bg-white shadow-sm rounded-4 border-0 d-flex align-items-center">
					<div class="icon-circle bg-primary-subtle text-primary me-3">
						<i class="bi bi-cloud-check-fill"></i>
					</div>
					<div>
						<small class="text-muted d-block fw-bold text-uppercase" style="font-size: 0.7rem;">Sincronización</small>
						<span class="fw-bold">Base de Datos Activa</span>
					</div>
				</div>
			</div>
		</header>

		<!-- Main Report Section -->
		<div class="row g-4">
			<div class="col-12">
				<div class="analytics-card bg-white shadow-lg rounded-4 overflow-hidden border-0">
					<div class="analytics-header p-4 d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3">
						<div class="d-flex align-items-center">
							<div class="bg-warning-subtle p-3 rounded-3 me-3 text-warning">
								<i class="bi bi-pie-chart-fill fs-3"></i>
							</div>
							<div>
								<h3 class="mb-0 fw-bold">Reporte General de Mascotas</h3>
								<p class="text-muted mb-0 small">Análisis detallado de adopciones, especies y tendencias anuales.</p>
							</div>
						</div>
						<div class="d-flex gap-2">
							<button class="btn btn-outline-secondary btn-sm rounded-pill px-3">
								<i class="bi bi-arrow-clockwise"></i> Actualizar
							</button>
							<a href="https://app.powerbi.com/view?r=eyJrIjoiZjU0ZWNhMjEtYjIyMy00MTllLTlmZmYtOTNhZjI0ZjA4MjY0IiwidCI6IjFlOWFhYmU4LTY3ZjgtNGYxYy1hMzI5LWE3NTRlOTI0OTlhZSIsImMiOjR9" 
							   target="_blank" class="btn btn-primary btn-sm rounded-pill px-3">
								<i class="bi bi-fullscreen"></i> Pantalla Completa
							</a>
						</div>
					</div>
					
					<div class="analytics-body p-2 p-lg-3 bg-light bg-opacity-50">
						<div class="report-wrapper rounded-3 overflow-hidden shadow-sm bg-white">
							<PowerBIReport
								title="Reporte de Mascotas"
								src="https://app.powerbi.com/view?r=eyJrIjoiZjU0ZWNhMjEtYjIyMy00MTllLTlmZmYtOTNhZjI0ZjA4MjY0IiwidCI6IjFlOWFhYmU4LTY3ZjgtNGYxYy1hMzI5LWE3NTRlOTI0OTlhZSIsImMiOjR9"
								height="750px"
								width="100%"
							/>
						</div>
					</div>
					
					<div class="analytics-footer p-3 bg-white border-top text-center">
						<small class="text-muted">
							<i class="bi bi-info-circle me-1"></i> Estos datos se obtienen directamente de la plataforma PowerBI.
						</small>
					</div>
				</div>
			</div>

			<!-- Secondary Section (Optional/Future) -->
			<div class="col-12 mt-5">
				<div class="row g-4">
					<div class="col-md-4">
						<div class="card p-4 border-0 shadow-sm rounded-4 h-100 text-center">
							<i class="bi bi-people fs-1 text-primary mb-3"></i>
							<h5 class="fw-bold">Gestión de Usuarios</h5>
							<p class="text-muted small">Métricas de crecimiento y actividad de la comunidad.</p>
							<button class="btn btn-sm btn-light mt-auto">Ver detalles</button>
						</div>
					</div>
					<div class="col-md-4">
						<div class="card p-4 border-0 shadow-sm rounded-4 h-100 text-center">
							<i class="bi bi-heart-pulse fs-1 text-danger mb-3"></i>
							<h5 class="fw-bold">Salud Animal</h5>
							<p class="text-muted small">Seguimiento de vacunas y estados médicos generales.</p>
							<button class="btn btn-sm btn-light mt-auto">Ver detalles</button>
						</div>
					</div>
					<div class="col-md-4">
						<div class="card p-4 border-0 shadow-sm rounded-4 h-100 text-center">
							<i class="bi bi-geo-fill fs-1 text-success mb-3"></i>
							<h5 class="fw-bold">Cobertura Geográfica</h5>
							<p class="text-muted small">Distribución geográfica de los rastreadores activos.</p>
							<button class="btn btn-sm btn-light mt-auto">Ver detalles</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</main>

<style>
	:global(body) {
		background-color: #f8f9fa;
	}

	.dashboard-container {
		min-height: 100vh;
	}

	.icon-circle {
		width: 45px;
		height: 45px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		font-size: 1.2rem;
	}

	.analytics-card {
		transition: transform 0.3s ease, box-shadow 0.3s ease;
	}

	.report-wrapper {
		border: 1px solid rgba(0,0,0,0.05);
	}

	/* Overriding internal component margin */
	:global(.report-wrapper .card) {
		margin-top: 0 !important;
		padding: 0 !important;
		border: none !important;
		background: transparent !important;
	}

	.bg-primary-subtle { background-color: #e7f0ff; }
	.bg-warning-subtle { background-color: #fff8e1; }
	.text-primary { color: #0d6efd !important; }
</style>
