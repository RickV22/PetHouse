<script>
	import { onMount } from 'svelte';
	import Navbar from '$lib/components/Navbar.svelte';

	let pet = null;
	let loading = true; // 👈 nuevo
	let cedulaFile = null;
	let reciboFile = null;

	let cedulaPreview = '';
	let reciboPreview = '';
	let message = '';
	let success = false;

	onMount(() => {
		const stored = localStorage.getItem('selectedPet');
		if (stored) {
			pet = JSON.parse(stored);
			console.log('Pet completo:', pet);
		}
		loading = false; // 👈 ya terminó de leer
	});

	function handleCedula(e) {
		cedulaFile = e.target.files[0];
		if (cedulaFile) cedulaPreview = URL.createObjectURL(cedulaFile);
	}

	function handleRecibo(e) {
		reciboFile = e.target.files[0];
		if (reciboFile) reciboPreview = URL.createObjectURL(reciboFile);
	}

	async function submitSolicitud() {
		if (!cedulaFile || !reciboFile) {
			message = 'Debes subir tu cédula y recibo de servicios';
			success = false;
			return;
		}

		const formData = new FormData();
		formData.append('pet_id', pet.id);
		formData.append('status_id', 1);

		formData.append('cedula', cedulaFile);
		formData.append('recibo', reciboFile);

		const res = await fetch('http://localhost:8000/adoptions', {
			method: 'POST',
			body: formData
		});

		const dataRes = await res.json();
		message = dataRes.message;
		success = res.ok;

		if (success) {
			cedulaFile = null;
			reciboFile = null;
			cedulaPreview = '';
			reciboPreview = '';
			quiere_tracker = false;
			localStorage.removeItem('selectedPet');
		}
	}
</script>

<Navbar />
<div class="container mt-5">
	<div class="row justify-content-center">
		<div class="col-md-8">
			{#if loading}
				<!-- Mientras lee el localStorage -->
				<div class="text-center py-5">
					<div class="spinner-border text-primary" role="status"></div>
				</div>
			{:else if !pet}
				<div class="alert alert-warning text-center">
					No se seleccionó ninguna mascota.
					<a href="/usuarios/mascotas" class="alert-link">Volver al catálogo</a>
				</div>
			{:else}
				<div class="card shadow">
					<div class="card-header bg-primary text-white">
						<h4 class="mb-0">Solicitud de Adopción</h4>
					</div>

    				<div class="card-body">
    					{#if message}
    						<div class="alert {success ? 'alert-success' : 'alert-danger'}">
    							{message}
    						</div>
    					{/if}

    					<div class="d-flex align-items-center gap-3 p-3 mb-4 border rounded bg-light">
    						<img
    							src={pet.image_url}
    							alt={pet.name}
    							class="rounded"
    							style="width:80px; height:80px; object-fit:cover;"
    						/>
    						<div>
    							<h5 class="mb-0 fw-bold">{pet.name}</h5>
    							<p class="text-muted mb-0">
    								{pet.age ?? pet.meses ?? pet.months ?? '?'} meses · {pet.species ??
    									pet.especie ??
    									''}
    								· {pet.gender ?? pet.genero ?? ''}
    							</p>
    							{#if pet.race ?? pet.raza}
    								<small class="text-muted">{pet.race ?? pet.raza}</small>
    							{/if}
    						</div>
    					</div>

    					<div class="row">
    						<div class="col-md-6 mb-3">
    							<!-- svelte-ignore a11y_label_has_associated_control -->
    							<label class="form-label fw-semibold">Cédula de identidad *</label>
    							<input
    								type="file"
    								class="form-control"
    								accept="image/*,application/pdf"
    								on:change={handleCedula}
    							/>
    							{#if cedulaPreview}
    								<img
    									src={cedulaPreview}
    									class="img-fluid rounded mt-2"
    									style="max-height:120px;"
    									alt="Vista previa cédula"
    								/>
    							{/if}
    						</div>

    						<div class="col-md-6 mb-3">
    							<!-- svelte-ignore a11y_label_has_associated_control -->
    							<label class="form-label fw-semibold">Recibo de servicios *</label>
    							<input
    								type="file"
    								class="form-control"
    								accept="image/*,application/pdf"
    								on:change={handleRecibo}
    							/>
    							{#if reciboPreview}
    								<img
    									src={reciboPreview}
    									class="img-fluid rounded mt-2"
    									style="max-height:120px;"
    									alt="Vista previa recibo"
    								/>
    							{/if}
    						</div>

    						<div class="col-12 mb-4">
    							<div class="form-check form-switch">
    								<input
    									class="form-check-input"
    									type="checkbox"
    									id="quiere_tracker"
    									bind:checked={quiere_tracker}
    								/>
    								<label class="form-check-label" for="quiere_tracker">
    									
    								</label>
    							</div>
    						</div>
    					</div>

    					<button class="btn btn-primary w-100" on:click={submitSolicitud}>
    						Enviar Solicitud
    					</button>
    				</div>
    			</div>
    		{/if}
    	</div>
    </div>

</div>
