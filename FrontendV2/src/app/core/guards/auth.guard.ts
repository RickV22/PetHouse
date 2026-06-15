import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import Swal from 'sweetalert2';

export const authGuard: CanActivateFn = async (route, state) => {
  const router = inject(Router);
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');

  if (!token || !userStr) {
    localStorage.setItem('redirectAfterLogin', state.url);

    await Swal.fire({
      title: '¡Acceso requerido! 🔒',
      text: 'Para publicar una mascota debes iniciar sesión',
      icon: 'info',
      confirmButtonText: 'Iniciar Sesión',
      background: '#FFF8F0',
      customClass: {
        popup: 'swal-cartoon-popup',
        confirmButton: 'swal-btn-confirm',
      },
      buttonsStyling: false,
    });

    router.navigate(['/login']);
    return false;
  }

  try {
    JSON.parse(userStr);
    return true;
  } catch {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.navigate(['/login']);
    return false;
  }
};
