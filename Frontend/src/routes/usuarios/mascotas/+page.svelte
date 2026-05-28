<script>
	import Navbar from '$lib/components/Navbar.svelte';
	import PetCard from '$lib/components/PetCard.svelte';
	import PetModal from '$lib/components/PetModal.svelte';
	import { onMount } from 'svelte';
	import { fly, fade } from 'svelte/transition';

	let selectedPet = null;
	let search = '';
	let pets = [];
	let loading = true;
	let filterType = 'all'; // all, perro, gato, otro

	onMount(async () => {
		try {
			const res = await fetch('http://localhost:8000/pets?status=AVAILABLE');
			if (res.ok) {
				pets = await res.json();
			}
		} catch (error) {
			console.error('Error fetching pets:', error);
		} finally {
			loading = false;
		}
	});

	function openModal(pet) {
		selectedPet = pet;
	}

	function closeModal() {
		selectedPet = null;
	}

	function setFilter(type) {
		filterType = type;
	}

	$: filteredPets = pets?.filter((pet) => {
		const matchesSearch = 
			pet.name.toLowerCase().includes(search.toLowerCase()) ||
			pet.species.toLowerCase().includes(search.toLowerCase()) ||
			(pet.race && pet.race.toLowerCase().includes(search.toLowerCase()));
		
		const matchesType = filterType === 'all' || pet.species.toLowerCase() === filterType;
		
		return matchesSearch && matchesType;
	}) ?? [];
</script>

<Navbar />

<main class="catalog-page pb-5">
	<!-- Hero Banner -->
	<section class="catalog-hero py-5 mb-5 text-center text-white position-relative overflow-hidden">
		<div class="hero-overlay"></div>
		<div class="container position-relative z-1 py-4">
			<h1 class="display-4 fw-bold mb-3" in:fly={{ y: -30, duration: 800 }}>Encuentra a tu Nuevo <span class="text-warning">Mejor Amigo</span></h1>
			<p class="lead mb-0 opacity-90 mx-auto" style="max-width: 600px;">
				Explora cientos de mascotas que buscan un hogar lleno de amor. Cada adopción cambia una vida para siempre.
			</p>
		</div>
	</section>

	<div class="container">
		<!-- Search & Filter Bar -->
		<div class="row justify-content-center mb-5">
			<div class="col-lg-10">
				<div class="filter-card bg-white p-4 shadow-lg rounded-4">
					<div class="row g-3 align-items-center">
						<div class="col-md-6">
							<div class="search-input-wrapper position-relative">
								<i class="bi bi-search position-absolute top-50 start-0 translate-middle-y ms-3 text-muted"></i>
								<input
									type="search"
									class="form-control form-control-lg ps-5 rounded-pill border-light bg-light cartoon-input"
									placeholder="Buscar por nombre o raza..."
									bind:value={search}
								/>
							</div>
						</div>
						<div class="col-md-6">
							<div class="d-flex flex-wrap gap-2 justify-content-md-end align-items-center">
								<button 
									class="filter-btn {filterType === 'all' ? 'active' : ''}" 
									on:click={() => setFilter('all')}
								>Todos</button>
								<button 
									class="filter-btn {filterType === 'perro' ? 'active' : ''}" 
									on:click={() => setFilter('perro')}
								>
									<i class="bi bi-dog me-1"></i> Perros
								</button>
								<button 
									class="filter-btn {filterType === 'gato' ? 'active' : ''}" 
									on:click={() => setFilter('gato')}
								>
									<i class="bi bi-cat me-1"></i> Gatos
								</button>
								<button 
									class="filter-btn {filterType === 'otro' ? 'active' : ''}" 
									on:click={() => setFilter('otro')}
								>Otros</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Grid -->
		{#if loading}
			<div class="text-center py-5">
				<div class="spinner-border text-primary fs-2" role="status"></div>
				<p class="mt-3 text-muted">Buscando compañeros para ti...</p>
			</div>
		{:else if filteredPets.length > 0}
			<div class="row g-4 g-lg-5">
				{#each filteredPets as pet (pet.id)}
					<div class="col-sm-6 col-md-4 col-xl-3" in:fade={{ duration: 300 }}>
						<PetCard {pet} on:view={() => openModal(pet)} />
					</div>
				{/each}
			</div>
		{:else}
			<div class="text-center py-5" in:fade>
				<div class="mb-4">
					<i class="bi bi-search-heart display-1 text-muted opacity-50"></i>
				</div>
				<h3 class="fw-bold text-dark">No encontramos resultados</h3>
				<p class="text-muted">Prueba buscando con otras palabras o filtros.</p>
				<button class="btn btn-outline-primary rounded-pill px-4 mt-2" on:click={() => {search = ''; filterType = 'all';}}>
					Ver todos de nuevo
				</button>
			</div>
		{/if}

		{#if selectedPet}
			<PetModal {selectedPet} on:close={closeModal} />
		{/if}
	</div>
</main>

<style>
	.catalog-page {
		background-color: #fcfcfd;
		min-height: 100vh;
	}

	.catalog-hero {
		background: url('https://images.unsplash.com/photo-1450778869180-41d0601e046e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80') center/cover no-repeat;
		min-height: 300px;
		display: flex;
		align-items: center;
	}

	.hero-overlay {
		position: absolute;
		top: 0; left: 0; right: 0; bottom: 0;
		background: linear-gradient(135deg, rgba(67, 97, 238, 0.85) 0%, rgba(76, 201, 240, 0.7) 100%);
	}

	.filter-card {
		margin-top: -80px;
		z-index: 10;
		position: relative;
		background: var(--cream);
		border: var(--border-thick);
		border-radius: 28px;
		box-shadow: var(--shadow-cartoon-lg);
	}

	.filter-btn {
		padding: 0.55rem 1.25rem;
		border-radius: var(--radius-pill);
		border: var(--border-thin);
		background: var(--cream);
		color: var(--ink);
		font-weight: 700;
		transition: transform 0.18s var(--bounce), box-shadow 0.18s ease, background 0.18s ease;
		box-shadow: var(--shadow-cartoon-sm);
	}

	.filter-btn:hover {
		transform: translateY(-3px);
		box-shadow: var(--shadow-hover);
	}

	.filter-btn.active {
		background: linear-gradient(135deg, var(--mustard), var(--mustard-dark));
		color: var(--ink);
		border: var(--border-thick);
		box-shadow: var(--shadow-hover);
	}

	.search-input-wrapper input:focus {
		background: white !important;
		box-shadow: 0 0 0 4px rgba(67, 97, 238, 0.1) !important;
		border-color: #4361ee !important;
	}

	.opacity-90 { opacity: 0.9; }
	.z-1 { z-index: 1; }
</style>
