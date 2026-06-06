export function isAdminRole(user) {
	const roleId = Number(user?.role_id ?? 0);
	const roleName = String(user?.role_name || user?.role || '').toLowerCase();

	return roleId === 1 || roleId === 3 || /admin|superadmin/.test(roleName);
}

export function getUserRoleLabel(user) {
	const roleId = Number(user?.role_id ?? 0);
	const roleName = String(user?.role_name || user?.role || '').trim().toLowerCase();

	if (roleName.includes('super')) return 'SUPERADMIN';
	if (roleName.includes('admin')) return 'Admin';
	if (roleId === 3) return 'SUPERADMIN';
	if (roleId === 1) return 'Admin';
	return 'Usuario';
}

export function roleLabelToId(label) {
	const normalized = String(label || '').trim().toLowerCase();

	if (normalized === 'superadmin' || normalized === 'super_admin') return 3;
	if (normalized === 'admin') return 1;
	return 2;
}
