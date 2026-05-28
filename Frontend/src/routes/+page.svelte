<script>
	import Navbar from '$lib/components/Navbar.svelte';
	import PetCard from '$lib/components/PetCard.svelte';
	import PetModal from '$lib/components/PetModal.svelte';
	import SearchBar from '$lib/components/SearchBar.svelte';
	import { fade, fly } from 'svelte/transition';
	import '../app.css';

	export let data;
	let selectedPet = null;

	function openModal(pet) {
		selectedPet = pet;
	}

	function closeModal() {
		selectedPet = null;
	}

	let search = '';
	const MAX_PREVIEW = 8;

	$: filteredPets = data.pets.filter(
		(pet) =>
			pet.name.toLowerCase().includes(search.toLowerCase()) ||
			pet.species.toLowerCase().includes(search.toLowerCase()) ||
			(pet.race && pet.race.toLowerCase().includes(search.toLowerCase()))
	);

	$: previewPets = filteredPets.slice(0, MAX_PREVIEW);
	$: hasMore = filteredPets.length > MAX_PREVIEW;
</script>

<svelte:head>
	<title>PetHouse - Encuentra tu mejor amigo 🐾</title>
	<meta name="description" content="Adopta una mascota, encuentra tu compañero ideal. PetHouse es la plataforma más cálida para darle hogar a quien más lo necesita." />
</svelte:head>

<Navbar />

<!-- ===== HERO CARTOON ===== -->
<section class="hero-cartoon">
	<!-- Paw pattern background -->
	<div class="paw-pattern hero-paws"></div>

	<!-- Pastel background blobs -->
	<div class="hero-blob hb-1"></div>
	<div class="hero-blob hb-2"></div>
	<div class="hero-blob hb-3"></div>

	<!-- Decorative floating elements -->
	<div class="deco deco-paw deco-1">🐾</div>
	<div class="deco deco-paw deco-2">🐾</div>
	<div class="deco deco-heart deco-3">💛</div>
	<div class="deco deco-star deco-4">⭐</div>
	<div class="deco deco-paw deco-5">🐾</div>
	<div class="deco deco-bone deco-6">🦴</div>

	<div class="container">
		<div class="hero-grid">
			<div class="hero-text" >
				<span class="hero-tag" in:fly={{ x: -30, duration: 600 }}>🏠 Plataforma de adopción</span>
				<h1 class="hero-title" in:fly={{ y: 30, duration: 700, delay: 100 }}>
					Encuentra a tu
					<span class="highlight-coral">mejor amigo</span>
					<span class="highlight-hand">para siempre</span>
				</h1>
				<p class="hero-subtitle" in:fly={{ y: 20, duration: 600, delay: 250 }}>
					Cada mascota merece un hogar lleno de amor.
					Descubre quién te está esperando. 🐶🐱
				</p>
				
				<div class="hero-stats" in:fly={{ y: 20, duration: 600, delay: 500 }}>
					<div class="stat-bubble">
						<span class="stat-number">{data.pets.length}</span>
						<span class="stat-label">Mascotas</span>
					</div>
					<div class="stat-bubble">
						<span class="stat-number">{data.pets.filter(p => p.status === 'ADOPTED').length}</span>
						<span class="stat-label">Adoptados</span>
					</div>
					<div class="stat-bubble">
						<span class="stat-number">❤️</span>
						<span class="stat-label">Mucho amor</span>
					</div>
				</div>
			</div>
			<div class="hero-illustration" in:fly={{ x: 40, duration: 800, delay: 200 }}>
				<div class="illustration-frame">
					<img src="/img/hero_pets_cartoon.png" alt="Mascotas felices esperando un hogar" />
				</div>
			</div>
		</div>
	</div>

	<!-- Wavy separator -->
	<div class="wave-separator">
		<svg viewBox="0 0 1440 100" preserveAspectRatio="none">
			<path d="M0,40 C360,100 720,0 1080,60 C1260,90 1380,40 1440,50 L1440,100 L0,100 Z" fill="var(--cream-dark)"/>
		</svg>
	</div>
</section>

<!-- ===== CATALOG SECTION ===== -->
<section class="catalog-section">
	<!-- Pastel decorative blobs -->
	<div class="pastel-blob pb-1"></div>
	<div class="pastel-blob pb-2"></div>
	<div class="pastel-blob pb-3"></div>
	<div class="pastel-blob pb-4"></div>
	<div class="pastel-blob pb-5"></div>
	<div class="pastel-blob pb-6"></div>

	<!-- Paw print pattern overlay -->
	<div class="paw-pattern"></div>

	<div class="container catalog-content">
		<div class="section-header">
			<span class="section-tag">🐾 Catálogo</span>
			<h2 class="section-title">Nuestras Mascotas</h2>
			<p class="section-subtitle">Cada uno tiene una historia especial. ¿Cuál será la tuya?</p>
			<div class="title-underline"></div>
		</div>

		<div class="pets-grid">
			{#each previewPets as pet, i (pet.id)}
				<div
					class="pet-grid-item"
					in:fly={{ y: 30, duration: 400, delay: Math.min(i * 80, 400) }}
				>
					<PetCard {pet} on:view={() => openModal(pet)} />
				</div>
			{/each}
		</div>

		{#if filteredPets.length === 0}
			<div class="empty-state" in:fade>
				<span class="empty-emoji">🔍</span>
				<h3>No encontramos mascotas</h3>
				<p>Intenta con otro nombre o especie</p>
			</div>
		{/if}

		{#if hasMore}
			<div class="see-more-wrap">
				<a href="/usuarios/mascotas" class="btn-see-more">
					Ver todas las mascotas 🐾
					<span class="see-more-count">+{filteredPets.length - MAX_PREVIEW} más</span>
				</a>
			</div>
		{/if}

		{#if selectedPet}
			<PetModal {selectedPet} on:close={closeModal} />
		{/if}
	</div>
</section>

<!-- ===== CTA SECTION ===== -->
<section class="cta-section">
	<div class="paw-pattern cta-paws"></div>
	<div class="container cta-container">
		<div class="cta-banner">
			<!-- Organic blob decorations -->
			<div class="blob blob-1"></div>
			<div class="blob blob-2"></div>
			<div class="blob blob-3"></div>

			<div class="cta-inner">
				<div class="cta-text">
					<h3 class="cta-title">¿Tienes una mascota que <em>busca hogar</em>?</h3>
					<p class="cta-subtitle">Publica gratis y llega a miles de familias en minutos.</p>
				</div>
				<a href="/usuarios/publicar" class="btn-cta">
					Publicar mascota <span class="cta-arrow">→</span>
				</a>
			</div>
		</div>
	</div>
</section>

<!-- ===== FOOTER ===== -->
<footer class="cartoon-footer">
	<div class="container">
		<div class="footer-content">
			<span class="footer-logo">🏠 PetHouse</span>
			<p>Hecho con ❤️ para las mascotas del mundo</p>
			<div class="footer-paws">🐾 🐾 🐾</div>
		</div>
	</div>
</footer>

<style>
	/* ===== HERO ===== */
	.hero-cartoon {
		background: var(--cream);
		padding: 6rem 0 0 0;
		position: relative;
		overflow: hidden;
		min-height: 75vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	/* Hero paw pattern */
	.hero-paws {
		opacity: 0.03;
	}

	/* Hero pastel blobs */
	.hero-blob {
		position: absolute;
		border-radius: 50%;
		pointer-events: none;
		z-index: 0;
	}

	.hb-1 {
		width: 280px;
		height: 280px;
		background: rgba(184, 169, 232, 0.18);
		top: -80px;
		right: -60px;
	}

	.hb-2 {
		width: 200px;
		height: 200px;
		background: rgba(255, 181, 154, 0.2);
		bottom: 10%;
		left: -70px;
	}

	.hb-3 {
		width: 140px;
		height: 140px;
		background: rgba(112, 193, 232, 0.18);
		top: 50%;
		left: 30%;
	}

	.hero-cartoon > .container {
		position: relative;
		z-index: 2;
	}

	.hero-grid {
		display: grid;
		grid-template-columns: 1.1fr 0.9fr;
		gap: 3rem;
		align-items: center;
		padding-bottom: 2rem;
	}

	/* Hero text */
	.hero-tag {
		display: inline-block;
		background: var(--mustard);
		color: var(--ink);
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 0.9rem;
		padding: 6px 18px;
		border-radius: 50px;
		border: 2.5px solid var(--ink);
		box-shadow: 3px 3px 0 var(--ink);
		margin-bottom: 1.2rem;
	}

	.hero-title {
		font-family: var(--font-display);
		font-size: 3.2rem;
		font-weight: 800;
		color: var(--ink);
		line-height: 1.15;
		margin-bottom: 1rem;
	}

	.highlight-coral {
		color: var(--coral);
		position: relative;
		display: inline-block;
	}

	.highlight-coral::after {
		content: '';
		position: absolute;
		bottom: 2px;
		left: -4px;
		right: -4px;
		height: 12px;
		background: rgba(255, 107, 107, 0.2);
		border-radius: 4px;
		z-index: -1;
		transform: rotate(-1deg);
	}

	.highlight-hand {
		font-family: var(--font-handwritten);
		color: var(--teal);
		font-size: 2.8rem;
		display: block;
		margin-top: -4px;
	}

	.hero-subtitle {
		font-family: var(--font-body);
		font-size: 1.15rem;
		color: var(--warm-gray);
		line-height: 1.7;
		margin-bottom: 1.5rem;
		max-width: 480px;
	}

	.hero-search {
		margin-bottom: 1.5rem;
	}

	/* Stats */
	.hero-stats {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
	}

	.stat-bubble {
		background: white;
		border: 2.5px solid var(--ink);
		border-radius: 16px;
		padding: 10px 18px;
		box-shadow: 3px 3px 0 var(--ink);
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 90px;
		transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
	}

	.stat-bubble:hover {
		transform: translateY(-4px) rotate(-2deg);
		box-shadow: 5px 5px 0 var(--ink);
	}

	.stat-number {
		font-family: var(--font-display);
		font-size: 1.6rem;
		font-weight: 800;
		color: var(--coral);
	}

	.stat-label {
		font-family: var(--font-body);
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--warm-gray);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	/* Illustration */
	.hero-illustration {
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.illustration-frame {
		position: relative;
		background: white;
		border: 3px solid var(--ink);
		border-radius: 28px;
		box-shadow: 6px 6px 0 var(--ink);
		overflow: hidden;
		transform: rotate(2deg);
		transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
		max-width: 440px;
	}

	.illustration-frame:hover {
		transform: rotate(-1deg) scale(1.03);
		box-shadow: 8px 8px 0 var(--ink);
	}

	.illustration-frame img {
		width: 100%;
		height: auto;
		display: block;
	}

	/* Floating decorations */
	.deco {
		position: absolute;
		font-size: 1.8rem;
		opacity: 0.15;
		pointer-events: none;
		z-index: 0;
	}

	.deco-1 { top: 15%; left: 5%; animation: paw-float 4s ease-in-out infinite; }
	.deco-2 { top: 60%; right: 8%; animation: paw-float 5s ease-in-out 1s infinite; }
	.deco-3 { top: 20%; right: 15%; animation: paw-float 3.5s ease-in-out 0.5s infinite; font-size: 1.4rem; }
	.deco-4 { bottom: 25%; left: 12%; animation: paw-float 4.5s ease-in-out 1.5s infinite; font-size: 1.2rem; }
	.deco-5 { bottom: 15%; right: 25%; animation: paw-float 5s ease-in-out 2s infinite; font-size: 1.3rem; }
	.deco-6 { top: 40%; left: 18%; animation: paw-float 4s ease-in-out 0.8s infinite; font-size: 1.5rem; }

	@keyframes paw-float {
		0%, 100% { transform: translateY(0) rotate(0deg); }
		50% { transform: translateY(-18px) rotate(12deg); }
	}

	/* Wave separator */
	.wave-separator {
		margin-top: auto;
		line-height: 0;
	}

	.wave-separator svg {
		width: 100%;
		height: 60px;
	}

	/* ===== CATALOG ===== */
	.catalog-section {
		background: var(--cream-dark);
		padding: 3rem 0 4rem;
		position: relative;
		overflow: hidden;
	}

	.catalog-content {
		position: relative;
		z-index: 2;
	}

	/* Paw print pattern */
	.paw-pattern {
		position: absolute;
		inset: 0;
		z-index: 0;
		opacity: 0.04;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60' viewBox='0 0 60 60'%3E%3Cg fill='%231A1A2E'%3E%3Cellipse cx='30' cy='38' rx='8' ry='10'/%3E%3Ccircle cx='19' cy='26' r='5'/%3E%3Ccircle cx='41' cy='26' r='5'/%3E%3Ccircle cx='14' cy='35' r='4'/%3E%3Ccircle cx='46' cy='35' r='4'/%3E%3C/g%3E%3C/svg%3E");
		background-size: 80px 80px;
		pointer-events: none;
	}

	/* Pastel decorative blobs */
	.pastel-blob {
		position: absolute;
		border-radius: 50%;
		pointer-events: none;
		z-index: 1;
		/* removed blur filter per request */
	}

	.pb-1 {
		width: 200px;
		height: 200px;
		background: rgba(255, 181, 154, 0.25);
		top: 5%;
		left: -60px;
	}

	.pb-2 {
		width: 150px;
		height: 150px;
		background: rgba(184, 169, 232, 0.2);
		top: 15%;
		right: -30px;
	}

	.pb-3 {
		width: 120px;
		height: 120px;
		background: rgba(112, 193, 232, 0.2);
		bottom: 20%;
		left: 8%;
	}

	.pb-4 {
		width: 180px;
		height: 180px;
		background: rgba(140, 203, 118, 0.18);
		bottom: 5%;
		right: 5%;
	}

	.pb-5 {
		width: 100px;
		height: 100px;
		background: rgba(245, 183, 49, 0.18);
		top: 50%;
		right: 15%;
	}

	.pb-6 {
		width: 90px;
		height: 90px;
		background: rgba(255, 107, 107, 0.15);
		top: 40%;
		left: 3%;
	}

	.section-header {
		text-align: center;
		margin-bottom: 2.5rem;
	}

	.section-tag {
		display: inline-block;
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 0.85rem;
		color: var(--teal);
		background: rgba(46, 196, 182, 0.12);
		padding: 5px 16px;
		border-radius: 50px;
		margin-bottom: 0.8rem;
		letter-spacing: 0.5px;
	}

	.section-title {
		font-family: var(--font-display);
		font-size: 2.4rem;
		font-weight: 800;
		color: var(--ink);
		margin: 0.4rem 0;
	}

	.section-subtitle {
		font-family: var(--font-body);
		color: var(--warm-gray);
		font-size: 1rem;
		margin-bottom: 0.5rem;
	}

	.title-underline {
		width: 80px;
		height: 4px;
		background: var(--coral);
		border-radius: 4px;
		margin: 0.8rem auto 0;
		transform: rotate(-1deg);
	}

	/* Grid — fixed 4 columns for uniformity */
	.pets-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}

	.pet-grid-item {
		display: flex;
		min-width: 0; /* prevent overflow */
	}

	/* See more button */
	.see-more-wrap {
		text-align: center;
		margin-top: 2.5rem;
	}

	.btn-see-more {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		background: var(--coral);
		color: white;
		font-family: var(--font-display);
		font-weight: 800;
		font-size: 1.15rem;
		padding: 14px 40px;
		border-radius: 50px;
		border: 3px solid var(--ink);
		box-shadow: 4px 4px 0 var(--ink);
		transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
		text-decoration: none;
	}

	.btn-see-more:hover {
		transform: translateY(-4px) rotate(-1deg);
		box-shadow: 6px 6px 0 var(--ink);
		background: var(--coral-dark);
		color: white;
	}

	.btn-see-more:active {
		transform: translateY(1px);
		box-shadow: 1px 1px 0 var(--ink);
	}

	.see-more-count {
		font-family: var(--font-body);
		font-size: 0.8rem;
		font-weight: 600;
		opacity: 0.8;
	}

	/* Empty state */
	.empty-state {
		text-align: center;
		padding: 4rem 2rem;
	}

	.empty-emoji {
		font-size: 3rem;
		display: block;
		margin-bottom: 1rem;
		animation: float 3s ease-in-out infinite;
	}

	@keyframes float {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	.empty-state h3 {
		font-family: var(--font-display);
		font-size: 1.5rem;
		color: var(--ink);
		margin-bottom: 0.3rem;
	}

	.empty-state p {
		color: var(--warm-gray);
	}

	/* ===== CTA SECTION ===== */
	.cta-section {
		background: var(--cream);
		padding: 2.5rem 0 3.5rem;
		position: relative;
		overflow: hidden;
	}

	.cta-paws {
		opacity: 0.03;
	}

	.cta-container {
		position: relative;
		z-index: 2;
	}

	.cta-banner {
		background: var(--ink);
		border-radius: 24px;
		padding: 3rem 3.5rem;
		position: relative;
		overflow: hidden;
	}

	/* Organic blob decorations */
	.blob {
		position: absolute;
		border-radius: 50%;
		pointer-events: none;
	}

	.blob-1 {
		width: 180px;
		height: 180px;
		background: rgba(46, 196, 182, 0.2);
		bottom: -50px;
		left: -40px;
	}

	.blob-2 {
		width: 140px;
		height: 140px;
		background: rgba(122, 90, 60, 0.5);
		top: -30px;
		left: 60px;
		border-radius: 50% 50% 50% 30%;
	}

	.blob-3 {
		width: 160px;
		height: 160px;
		background: rgba(140, 70, 60, 0.55);
		top: -40px;
		right: -30px;
		border-radius: 40% 50% 50% 50%;
	}

	.cta-inner {
		position: relative;
		z-index: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 2rem;
	}

	.cta-text {
		flex: 1;
	}

	.cta-title {
		font-family: var(--font-display);
		font-size: 2rem;
		font-weight: 800;
		color: #fff;
		line-height: 1.2;
		margin: 0 0 0.5rem 0;
	}

	.cta-title em {
		font-family: var(--font-handwritten);
		font-style: italic;
		color: var(--mustard);
		font-size: 2.2rem;
	}

	.cta-subtitle {
		font-family: var(--font-body);
		color: rgba(255, 255, 255, 0.55);
		font-size: 1rem;
		margin: 0;
		max-width: 420px;
	}

	.btn-cta {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		background: var(--mustard);
		color: var(--ink);
		font-family: var(--font-display);
		font-weight: 800;
		font-size: 1.05rem;
		padding: 16px 32px;
		border-radius: 50px;
		border: none;
		transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
		text-decoration: none;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.btn-cta:hover {
		background: #ffc800;
		color: var(--ink);
		transform: translateY(-3px) scale(1.03);
		box-shadow: 0 8px 25px rgba(245, 183, 49, 0.35);
	}

	.btn-cta:active {
		transform: translateY(0px) scale(0.98);
	}

	.cta-arrow {
		font-size: 1.2rem;
		transition: transform 0.3s ease;
	}

	.btn-cta:hover .cta-arrow {
		transform: translateX(4px);
	}

	/* ===== FOOTER ===== */
	.cartoon-footer {
		background: var(--ink);
		padding: 2rem 0;
		text-align: center;
	}

	.footer-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.footer-logo {
		font-family: var(--font-display);
		font-size: 1.6rem;
		font-weight: 800;
		color: var(--mustard);
	}

	.cartoon-footer p {
		color: rgba(255, 255, 255, 0.5);
		font-family: var(--font-body);
		font-size: 0.9rem;
		margin: 0;
	}

	.footer-paws {
		font-size: 1.2rem;
		opacity: 0.3;
		letter-spacing: 8px;
		margin-top: 0.3rem;
	}

	/* ===== RESPONSIVE ===== */
	@media (max-width: 991px) {
		.hero-grid {
			grid-template-columns: 1fr;
			text-align: center;
			gap: 2rem;
		}

		.hero-title {
			font-size: 2.5rem;
		}

		.highlight-hand {
			font-size: 2.2rem;
		}

		.hero-subtitle {
			margin-left: auto;
			margin-right: auto;
		}

		.hero-stats {
			justify-content: center;
		}

		.illustration-frame {
			max-width: 340px;
			margin: 0 auto;
		}

		.pets-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}

	@media (max-width: 768px) {
		.pets-grid {
			grid-template-columns: repeat(2, 1fr);
			gap: 1rem;
		}

		.cta-inner {
			flex-direction: column;
			text-align: center;
		}

		.cta-subtitle {
			margin-left: auto;
			margin-right: auto;
		}

		.cta-banner {
			padding: 2.5rem 2rem;
		}
	}

	@media (max-width: 576px) {
		.hero-cartoon {
			padding: 5rem 0 0 0;
		}

		.hero-title {
			font-size: 2rem;
		}

		.highlight-hand {
			font-size: 1.8rem;
		}

		.pets-grid {
			grid-template-columns: repeat(2, 1fr);
			gap: 0.8rem;
		}

		.cta-banner {
			padding: 2rem 1.5rem;
		}

		.cta-title {
			font-size: 1.5rem;
		}

		.cta-title em {
			font-size: 1.7rem;
		}
	}
</style>
