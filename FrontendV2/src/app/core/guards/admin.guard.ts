import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { isAdminRole } from '../../shared/utils/roles';

// ── MODO PRUEBAS: comenta esto y descomenta el bloque de abajo ──
export const adminGuard: CanActivateFn = () => true;

// ── PRODUCCIÓN: descomenta esto cuando el backend esté disponible ──
/*
export const adminGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');

  if (!token || !userStr) {
    router.navigate(['/login']);
    return false;
  }

  try {
    const user = JSON.parse(userStr);
    if (!isAdminRole(user)) {
      router.navigate(['/']);
      return false;
    }
    return true;
  } catch {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.navigate(['/login']);
    return false;
  }
};
*/
