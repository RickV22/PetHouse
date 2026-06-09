<script>
	export let password = '';

	$: requirements = {
		minLength: password.length >= 8,
		hasUppercase: /[A-Z]/.test(password),
		hasLowercase: /[a-z]/.test(password),
		hasNumber: /\d/.test(password),
		hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password)
	};

	$: allRequirementsMet = Object.values(requirements).every(req => req === true);

	function Requirement({ met, text }) {
		return `
			<div class="requirement-item">
				<i class="bi ${met ? 'bi-check-circle-fill' : 'bi-circle'} ${met ? 'text-success' : 'text-muted'}"></i>
				<span class="${met ? 'text-success' : 'text-muted'}">${text}</span>
			</div>
		`;
	}
</script>

<div class="password-requirements mt-2">
	<small class="d-block text-muted mb-2">
		<strong>Requisitos de contraseña:</strong>
	</small>

	<div class="requirement-item">
		<i class="bi {requirements.minLength ? 'bi-check-circle-fill text-success' : 'bi-circle text-muted'}"></i>
		<span class={requirements.minLength ? 'text-success' : 'text-muted'}>Mínimo 8 caracteres</span>
	</div>

	<div class="requirement-item">
		<i class="bi {requirements.hasUppercase ? 'bi-check-circle-fill text-success' : 'bi-circle text-muted'}"></i>
		<span class={requirements.hasUppercase ? 'text-success' : 'text-muted'}>Al menos una letra mayúscula</span>
	</div>

	<div class="requirement-item">
		<i class="bi {requirements.hasLowercase ? 'bi-check-circle-fill text-success' : 'bi-circle text-muted'}"></i>
		<span class={requirements.hasLowercase ? 'text-success' : 'text-muted'}>Al menos una letra minúscula</span>
	</div>

	<div class="requirement-item">
		<i class="bi {requirements.hasNumber ? 'bi-check-circle-fill text-success' : 'bi-circle text-muted'}"></i>
		<span class={requirements.hasNumber ? 'text-success' : 'text-muted'}>Al menos un número</span>
	</div>

	<div class="requirement-item">
		<i class="bi {requirements.hasSpecial ? 'bi-check-circle-fill text-success' : 'bi-circle text-muted'}"></i>
		<span class={requirements.hasSpecial ? 'text-success' : 'text-muted'}>Al menos un carácter especial (!@#$%^&* etc)</span>
	</div>

	{#if password && !allRequirementsMet}
		<div class="alert alert-warning mt-2 py-1 px-2" role="alert">
			<small>Completa todos los requisitos para crear la contraseña</small>
		</div>
	{:else if allRequirementsMet && password}
		<div class="alert alert-success mt-2 py-1 px-2" role="alert">
			<small>✓ Contraseña válida</small>
		</div>
	{/if}
</div>

<style>
	.requirement-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		margin-bottom: 0.5rem;
	}

	.requirement-item i {
		font-size: 1rem;
		flex-shrink: 0;
	}
</style>
