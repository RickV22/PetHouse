<script>
	import Navbar from '$lib/components/Navbar.svelte';
	import { createPet } from '../../../api/pet_service.js';
	import { auth } from '$lib/stores/auth.js';
	import { isAdminRole } from '$lib/utils/roles.js';
	import Swal from 'sweetalert2';
	import { fly } from 'svelte/transition';

	let name = '';
	let species = '';
	let race = '';
	let birth_date = '';
	let gender = '';
	let description = '';
	let imageFile = null;
	let acceptedTerms = false;

	let preview = '';
	let isSubmitting = false;

	$: user = $auth?.user;

	function handleImage(e) {
		imageFile = e.target.files[0];
		if (imageFile) {
			preview = URL.createObjectURL(imageFile);
		}
	}

	async function publishPet() {
		if (!name || !species) {
			Swal.fire({
				title: '¡Oops!',
				text: 'Debes completar los campos obligatorios 🐾',
				icon: 'warning',
				confirmButtonColor: '#F5B731'
			});
			return;
		}

		if (!acceptedTerms) {
			Swal.fire({
				title: 'Términos Legales',
				text: 'Debes aceptar los términos y condiciones para continuar.',
				icon: 'info',
				confirmButtonColor: '#F5B731'
			});
			return;
		}

		isSubmitting = true;

		const formData = new FormData();
		formData.append('name', name);
		formData.append('species', species);
		formData.append('race', race);
		formData.append('birth_date', birth_date);
		formData.append('gender', gender);
		formData.append('description', description);

		if (imageFile) {
			formData.append('image', imageFile);
		}

		try {
			await createPet(formData);
			
			const isAdmin = isAdminRole(user);

			await Swal.fire({
				title: isAdmin ? '¡Publicada!' : '¡Solicitud Recibida! 🐾',
				html: isAdmin 
					? 'La mascota se ha publicado directamente.' 
					: `Tu solicitud ha sido registrada.<br><br><b>Siguiente paso:</b> Acércate a nuestra casa de adopción para dejar a la mascota y completar el proceso oficial.`,
				icon: 'success',
				confirmButtonText: 'Entendido',
				confirmButtonColor: '#4361ee',
				background: '#FFF8F0',
				customClass: {
					popup: 'swal-cartoon-popup',
					confirmButton: 'swal-btn-confirm'
				},
				buttonsStyling: false
			});

			// Limpiar formulario
			name = ''; species = ''; race = ''; birth_date = ''; gender = ''; description = '';
			imageFile = null; preview = ''; acceptedTerms = false;
		} catch (error) {
			Swal.fire('Error', error.message, 'error');
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Navbar />

<main class="publish-page py-5">
	<div class="container" in:fly={{ y: 20, duration: 600 }}>
		<div class="row justify-content-center">
			<div class="col-lg-8">
				<div class="publish-card p-4 p-md-5">
					<div class="text-center mb-4">
						<span class="publish-badge mb-2">🐾 Nueva Publicación</span>
						<h1 class="fw-bold display-6">Dar en Adopción</h1>
						<p class="text-muted">Ayúdanos a encontrarle el hogar que se merece</p>
					</div>

					<div class="row g-4">
						<!-- Columna Izquierda: Imagen -->
						<div class="col-md-5 order-md-2">
							<div class="image-upload-wrapper {preview ? 'has-preview' : ''}">
								{#if preview}
									<img src={preview} alt="Vista previa" class="preview-img" />
									<button class="btn btn-sm btn-danger remove-img" on:click={() => {preview = ''; imageFile = null;}}>
										<i class="bi bi-x"></i>
									</button>
								{:else}
									<label class="upload-label">
										<i class="bi bi-camera-fill display-4 mb-2"></i>
										<span class="small fw-bold">Subir Foto</span>
										<input type="file" class="d-none" accept="image/*" on:change={handleImage} />
									</label>
								{/if}
							</div>
						</div>

						<!-- Columna Derecha: Datos -->
						<div class="col-md-7 order-md-1">
							<div class="row g-3">
								<div class="col-12">
									<label class="form-label cartoon-label">Nombre de la Mascota *</label>
									<input class="form-control cartoon-input" bind:value={name} placeholder="Ej: Bobby" />
								</div>

								<div class="col-6">
									<label class="form-label cartoon-label">Especie *</label>
									<select class="form-select cartoon-input" bind:value={species}>
										<option value="">Elegir...</option>
										<option value="perro">🐶 Perro</option>
										<option value="gato">🐱 Gato</option>
									</select>
								</div>

								<div class="col-6">
									<label class="form-label cartoon-label">Género</label>
									<select class="form-select cartoon-input" bind:value={gender}>
										<option value="">Elegir...</option>
										<option value="macho">Macho</option>
										<option value="hembra">Hembra</option>
									</select>
								</div>

								<div class="col-12">
									<label class="form-label cartoon-label">Raza (opcional)</label>
									<input class="form-control cartoon-input" bind:value={race} placeholder="Ej: Golden Retriever" />
								</div>

								<div class="col-12">
									<label class="form-label cartoon-label">Fecha Nacimiento (aprox)</label>
									<input type="date" class="form-control cartoon-input" bind:value={birth_date} />
								</div>
							</div>
						</div>

						<div class="col-12 order-3">
							<label class="form-label cartoon-label">Cuéntanos sobre su personalidad</label>
							<textarea 
								class="form-control cartoon-input" 
								rows="4" 
								bind:value={description} 
								placeholder="Es muy juguetón, le gustan los niños..."></textarea>
						</div>

						<!-- Sección Legal Mejorada -->
						<div class="col-12 order-4">
							<div class="legal-cartoon-box p-3 mb-3">
								<h6 class="fw-bold text-coral d-flex align-items-center gap-2">
									<i class="bi bi-shield-lock-fill"></i> Compromiso de Bienestar
								</h6>
								<p class="small text-muted mb-3 lh-sm">
									Certifico que esta información es verídica. Me comprometo a entregar a la mascota 
									personalmente en la sede de PetHouse para validar su estado de salud.
								</p>
								<div class="form-check">
									<input class="form-check-input" type="checkbox" id="termsCheck" bind:checked={acceptedTerms} />
									<label class="form-check-label fw-bold small" for="termsCheck">
										Acepto los términos y el proceso de entrega física.
									</label>
								</div>
							</div>

							<button 
								class="btn btn-publish-cartoon w-100 py-3" 
								on:click={publishPet}
								disabled={isSubmitting}
							>
								{#if isSubmitting}
									<span class="spinner-border spinner-border-sm me-2"></span> Publicando...
								{:else}
									<i class="bi bi-send-fill me-2"></i> Enviar Publicación
								{/if}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</main>

<style>
	.publish-page {
		background: var(--cream);
		min-height: calc(100vh - 70px);
		font-family: var(--font-main);
	}

	.publish-card {
		background: white;
		border: 3px solid var(--ink);
		border-radius: 30px;
		box-shadow: 10px 10px 0 var(--ink);
	}

	.publish-badge {
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		padding: 4px 16px;
		border-radius: 50px;
		display: inline-block;
		border: 2px solid var(--ink);
		font-size: 0.85rem;
		text-transform: uppercase;
	}

	.cartoon-label {
		font-family: var(--font-display);
		font-weight: 700;
		color: var(--ink);
		margin-bottom: 5px;
	}

	.cartoon-input {
		border: 2.5px solid var(--ink) !important;
		border-radius: 15px !important;
		padding: 10px 15px;
		font-weight: 600;
		transition: all 0.2s ease;
	}

	.cartoon-input:focus {
		box-shadow: 4px 4px 0 var(--ink) !important;
		transform: translate(-2px, -2px);
		border-color: var(--coral) !important;
	}

	.image-upload-wrapper {
		border: 3px dashed #ddd;
		border-radius: 20px;
		height: 100%;
		min-height: 200px;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		overflow: hidden;
		transition: all 0.3s ease;
		background: #f8f9fa;
	}

	.image-upload-wrapper:hover {
		border-color: var(--mustard);
		background: #fff;
	}

	.image-upload-wrapper.has-preview {
		border: 3px solid var(--ink);
	}

	.preview-img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.upload-label {
		cursor: pointer;
		display: flex;
		flex-direction: column;
		align-items: center;
		color: #999;
	}

	.remove-img {
		position: absolute;
		top: 10px;
		right: 10px;
		border-radius: 50%;
		width: 32px;
		height: 32px;
		padding: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid var(--ink);
		box-shadow: 2px 2px 0 var(--ink);
	}

	.legal-cartoon-box {
		background: #FFF8F0;
		border: 2.5px solid var(--ink);
		border-radius: 15px;
	}

	.btn-publish-cartoon {
		background: var(--mustard);
		color: var(--ink);
		font-weight: 800;
		font-family: var(--font-display);
		font-size: 1.2rem;
		border: 3px solid var(--ink);
		border-radius: 20px;
		box-shadow: 6px 6px 0 var(--ink);
		transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	}

	.btn-publish-cartoon:hover:not(:disabled) {
		transform: translate(-3px, -3px);
		box-shadow: 9px 9px 0 var(--ink);
		background: var(--coral);
		color: white;
	}

	.btn-publish-cartoon:active:not(:disabled) {
		transform: translate(2px, 2px);
		box-shadow: 2px 2px 0 var(--ink);
	}

	/* SweetAlert Custom for consistent look */
	:global(.swal-cartoon-popup) {
		border-radius: 25px !important;
		border: 4px solid var(--ink) !important;
		box-shadow: 8px 8px 0 var(--ink) !important;
	}
	:global(.swal-btn-confirm) {
		background: var(--mustard) !important;
		color: var(--ink) !important;
		border: 3px solid var(--ink) !important;
		border-radius: 50px !important;
		padding: 12px 30px !important;
		font-weight: 800 !important;
		box-shadow: 4px 4px 0 var(--ink) !important;
	}
</style>
