<script>
	import { onMount } from 'svelte';
	import Navbar from '$lib/components/Navbar.svelte';
	import { goto } from '$app/navigation';
	import { formatAge } from '$lib/utils/formatAge.js';

	export let data;

	let pet = data?.pet || null;
	let loading = !pet;
	let cedulaFile = null;
	let reciboFile = null;

	let acceptedTerms = false;
	let message = '';
	let success = false;

	$: ageText = pet ? formatAge(pet.birth_date) : 'Desconocida';

	const API = 'http://localhost:8000';

	onMount(async () => {
		if (!pet) {
			// Intentar obtener del localStorage primero
			const stored = localStorage.getItem('selectedPet');
			if (stored) {
				pet = JSON.parse(stored);
			} else {
				// Intentar obtener del API usando el query param
				const urlParams = new URLSearchParams(window.location.search);
				const petId = urlParams.get('pet_id');
				if (petId) {
					try {
						const res = await fetch(`${API}/pets/${petId}`);
						if (res.ok) {
							pet = await res.json();
						}
					} catch (e) {
						console.error('Error fetching pet:', e);
					}
				}
			}
		}
		loading = false;
	});

	function handleCedula(e) { cedulaFile = e.target.files[0]; }
	function handleRecibo(e) { reciboFile = e.target.files[0]; }

	async function submitSolicitud() {
		message = '';

		if (!cedulaFile || !reciboFile) {
			message = 'Debes subir tu cédula y recibo de servicios';
			success = false;
			return;
		}

		if (!acceptedTerms) {
			message = 'Debes aceptar los términos y el compromiso de adopción responsable';
			success = false;
			return;
		}

		const token = localStorage.getItem('token');
		const userStr = localStorage.getItem('user') || localStorage.getItem('pethouse_user');
		if (!token || !userStr) {
			message = 'Debes iniciar sesión para adoptar';
			success = false;
			return;
		}

		try {
			loading = true;

			const fd = new FormData();
			fd.append('pet_id', pet.id);
			fd.append('cedula', cedulaFile);
			fd.append('recibo', reciboFile);

			const res = await fetch(`${API}/adoptions/`, {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${token}`
				},
				body: fd
			});

			const dataRes = await res.json();

				if (res.ok) {
				message = 'Solicitud enviada correctamente';
				success = true;
				cedulaFile = null;
				reciboFile = null;
				localStorage.removeItem('selectedPet');
				// Opcional: redirigir a la pagina principal después de un tiempo (navegación cliente)
				setTimeout(() => {
					goto('/usuarios/mascotas');
				}, 2000);
				
			} else {
				message = dataRes.detail || dataRes.message || 'No se pudo enviar la solicitud';
				success = false;
			}
		} catch (e) {
			message = 'Error de conexión con el servidor';
			success = false;
			console.error(e);
		} finally {
			loading = false;
		}
	}
</script>

<Navbar />
<div class="container mt-5">
	<div class="row justify-content-center">
		<div class="col-md-8">
			{#if loading}
				<div class="text-center py-5">
					<div class="spinner-border text-primary" role="status"></div>
				</div>
			{:else if !pet}
				<div class="alert alert-warning text-center">
					No se seleccionó ninguna mascota.
					<a href="/" class="alert-link">Volver al catálogo</a>
				</div>
			{:else}
				<div class="adopt-card p-3">
					<div class="card-badge">🐾 SOLICITUD</div>

					<div class="card-head text-center mb-3">
						<h4 class="mb-0">Solicitud de Adopción</h4>
					</div>

					<div class="card-body">
						{#if message}
							<div class="alert {success ? 'alert-success' : 'alert-danger'}">{message}</div>
						{/if}

						<!-- Info mascota -->
						<div class="d-flex align-items-center gap-3 p-3 mb-4 border rounded bg-light">
							{#if pet.image_url}
								<img src={pet.image_url} alt={pet.name} class="rounded"
									style="width:80px; height:80px; object-fit:cover;" />
							{/if}
							<div>
								<h5 class="mb-0 fw-bold">{pet.name}</h5>
								<p class="text-muted mb-0">
									{ageText} · {pet.species ?? ''} · {pet.gender ?? ''}
								</p>
								{#if pet.race}<small class="text-muted">{pet.race}</small>{/if}
							</div>
						</div>

						<div class="row">
							<div class="col-md-6 mb-3">
								<label class="form-label cartoon-label" for="cedula">Cédula de identidad *</label>
								<input id="cedula" type="file" class="form-control cartoon-input"
									accept="image/*,application/pdf" on:change={handleCedula} />
							</div>
							<div class="col-md-6 mb-3">
								<label class="form-label cartoon-label" for="recibo">Recibo de servicios *</label>
								<input id="recibo" type="file" class="form-control cartoon-input"
									accept="image/*,application/pdf" on:change={handleRecibo} />
							</div>
							<div class="col-12 mb-4">
								<div class="legal-cartoon-box p-3 mb-4">
									<h6 class="fw-bold text-coral d-flex align-items-center gap-2"><i class="bi bi-shield-check"></i> Requisitos Legales y Compromisos</h6>
									<div class="small text-muted">
										<p class="mb-2">De acuerdo con la <strong>Ley 1774 de 2016</strong> y la <strong>Ley 2054 de 2020</strong>, la adopción implica una responsabilidad legal sobre el bienestar animal. Al enviar esta solicitud, te comprometes a:</p>
										<ul class="mb-3">
											<li>Ser mayor de edad (+18 años) con identificación válida.</li>
											<li>Garantizar un espacio seguro y digno para el animal.</li>
											<li>Cubrir gastos de alimentación, salud (vacunas, desparasitación) y bienestar.</li>
											<li><strong>Esterilización obligatoria</strong> (si no lo está ya).</li>
											<li>No abandonar, maltratar ni ceder el animal a terceros sin aviso.</li>
											<li>Permitir visitas de seguimiento por parte de PetHouse.</li>
										</ul>
									</div>
									<div class="form-check">
										<input class="form-check-input" type="checkbox" id="terms" bind:checked={acceptedTerms} required />
										<label class="form-check-label fw-bold" for="terms">
											Acepto los términos del Contrato de Adopción Responsable
										</label>
									</div>
								</div>

								<!-- tracker GPS option removed from form per project update -->
							</div>
						</div>

						<button class="btn-publish-cartoon w-100 py-3" on:click={submitSolicitud}
							disabled={loading || success || !acceptedTerms}>
							{loading ? 'Procesando Solicitud...' : 'Confirmar y Enviar Solicitud Legal'}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.adopt-card {
		background: white;
		border: 3px solid var(--ink);
		border-radius: 20px;
		box-shadow: var(--shadow-cartoon-lg);
		padding: 1rem;
	}

	.card-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.4rem 0.9rem;
		border-radius: 999px;
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		font-size: 0.85rem;
		border: var(--border-thin);
		position: relative;
		top: -10px;
		margin-bottom: 0.4rem;
	}

	.card-head h4 { font-family: var(--font-display); margin: 0; }

	.cartoon-label { font-family: var(--font-display); font-weight:700; color:var(--ink); }
	.cartoon-input { border: 2.5px solid var(--ink); border-radius: 12px; padding: 8px; }

	.legal-cartoon-box { background: var(--cream); border: 2.5px solid var(--ink); border-radius: 12px; }

	.btn-publish-cartoon { background: var(--mustard); color: var(--ink); font-weight:800; border:3px solid var(--ink); border-radius:20px; }
	.btn-publish-cartoon:hover:not(:disabled) { background:var(--coral); color:white; transform: translate(-3px,-3px); box-shadow: var(--shadow-hover); }
</style>