import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import Swal from 'sweetalert2';

//import { AuthService } from '../../stores/auth.service'; // ajusta la ruta

@Component({
  selector: 'app-admin-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './admin-navbar.html',
  styleUrls: ['./admin-navbar.css'],
})
export class AdminNavbarComponent {
  constructor(
    private router: Router,
    //private authService: AuthService,
  ) {}

  async logout(): Promise<void> {
    const result = await Swal.fire({
      title: '¿Cerrar sesión?',
      text: '¿Estás seguro de que deseas salir del panel administrativo?',
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#F5B731',
      cancelButtonColor: '#FF6B6B',
      confirmButtonText: 'Sí, salir',
      cancelButtonText: 'Cancelar',
      background: '#FFF8F0',
      customClass: {
        confirmButton: 'swal-btn-confirm',
        cancelButton: 'swal-btn-cancel',
        popup: 'swal-cartoon-popup',
      },
      buttonsStyling: false,
    });

    if (result.isConfirmed) {
      //this.authService.clearAuth();
      this.router.navigate(['/login']);
    }
  }
}
