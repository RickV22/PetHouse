<script>
	import Navbar from '$lib/components/Navbar.svelte';
</script>

<Navbar />
<section class="container my-5">
	<div class="card shadow-sm p-4">
		<h2>Bienvenido a tu espacio de usuario</h2>
		<p>Selecciona una acción para continuar:</p>

		<div class="d-flex flex-column gap-3 mt-4">
			<a class="btn btn-primary" href="/usuarios/mascotas">Ver mascotas disponibles</a>
			<a class="btn btn-secondary" href="/usuarios/publicar">Publicar una mascota</a></div>
	</div>
</section>

