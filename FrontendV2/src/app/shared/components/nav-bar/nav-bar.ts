import { Component, Input, OnInit, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import Swal from 'sweetalert2';
import { Subscription } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { isAdminRole } from '../../utils/roles';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './nav-bar.html',
  styleUrls: ['./nav-bar.css'],
})
export class NavbarComponent implements OnInit, OnDestroy {
  @Input() showLogin = true;
  @Input() variant: 'default' | 'login' = 'default';

  scrolled = false;
  user: any = null;

  private authSub!: Subscription;

  constructor(
    private router: Router,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.authSub = this.authService.auth$.subscribe((auth) => {
      this.user = auth?.user ?? null;
    });
  }

  ngOnDestroy(): void {
    this.authSub.unsubscribe();
  }

  @HostListener('window:scroll')
  onScroll(): void {
    this.scrolled = window.scrollY > 30;
  }

  isAdmin(): boolean {
    return this.user ? isAdminRole(this.user) : false;
  }

  getInitial(): string {
    return this.user?.name?.charAt(0).toUpperCase() ?? '';
  }

  async logout(): Promise<void> {
    const result = await Swal.fire({
      title: '¿Cerrar sesión?',
      text: '¿Estás seguro de que deseas salir de tu cuenta?',
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#F5B731',
      cancelButtonColor: '#FF6B6B',
      confirmButtonText: 'Sí, ¡nos vemos! 👋',
      cancelButtonText: 'Me quedo',
      background: '#FFF8F0',
      customClass: {
        confirmButton: 'swal-btn-confirm',
        cancelButton: 'swal-btn-cancel',
        popup: 'swal-cartoon-popup',
      },
      buttonsStyling: false,
    });

    if (result.isConfirmed) {
      await Swal.fire({
        title: '¡Hasta pronto! 🐾',
        text: 'Cerrando tu sesión...',
        timer: 1200,
        timerProgressBar: true,
        showConfirmButton: false,
        background: '#FFF8F0',
        didOpen: () => Swal.showLoading(),
      });

      this.authService.clearAuth();
      this.router.navigate(['/']);
    }
  }
}
