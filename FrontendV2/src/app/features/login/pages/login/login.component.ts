import { Component, OnInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import Swal from 'sweetalert2';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { UserService } from '../../../../core/services/user.service';
import { AuthService } from '../../../../core/services/auth.service';
import { isAdminRole } from '../../../../shared/utils/roles';
import { getAndClearRedirectUrl } from '../../../../shared/utils/auth';

const GOOGLE_CLIENT_ID = ''; // ← pega aquí tu GOOGLE_CLIENT_ID

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent implements OnInit {
  isRegister = false;
  nombre = '';
  apellido = '';
  email = '';
  password = '';
  showPassword = false;
  authMessage = '';
  passwordError = '';

  readonly googleClientId = GOOGLE_CLIENT_ID;

  constructor(
    private userService: UserService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private ngZone: NgZone,
  ) {}

  ngOnInit(): void {
    // Mostrar mensaje desde query param (equivalente a $page.url.searchParams)
    const message = this.route.snapshot.queryParamMap.get('message');
    if (message) {
      this.authMessage = message;
      Swal.fire({
        title: 'Acceso requerido',
        text: message,
        icon: 'info',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
      });
    }

    // Inicializar Google Sign-In
    if (this.googleClientId) {
      this.loadGoogleScript().then(() => this.initGoogle());
    }
  }

  // ── Password rules ────────────────────────────────
  get pwdRules() {
    return {
      length: this.password.length >= 8,
      upper: /[A-Z]/.test(this.password),
      lower: /[a-z]/.test(this.password),
      number: /\d/.test(this.password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(this.password),
    };
  }

  get isPasswordValid(): boolean {
    return Object.values(this.pwdRules).every(Boolean);
  }

  // ── Google Sign-In ────────────────────────────────
  private loadGoogleScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      if ((window as any).google?.accounts?.id) return resolve();
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Google Identity Services'));
      document.head.appendChild(script);
    });
  }

  private initGoogle(): void {
    const g = (window as any).google;
    if (!g) return;

    if (!(window as any).__pethouse_google_initialized) {
      g.accounts.id.initialize({
        client_id: this.googleClientId,
        callback: (response: any) => this.ngZone.run(() => this.handleCredentialResponse(response)),
      });
      (window as any).__pethouse_google_initialized = true;
    }

    try {
      g.accounts.id.renderButton(document.getElementById('googleSignInDiv'), {
        theme: 'outline',
        size: 'large',
        width: '280',
      });
    } catch {
      /* ignore */
    }
  }

  async handleCredentialResponse(response: any): Promise<void> {
    if (!response?.credential) return;
    try {
      const data = await this.userService.googleLogin(response.credential);
      this.authService.setAuth(data.user, data.access_token);
      Swal.fire({ title: 'Bienvenido', text: `Hola ${data.user.name}`, icon: 'success' });
      this.redirectAfterLogin(data.user);
    } catch {
      Swal.fire('Error', 'No se pudo iniciar sesión con Google.', 'error');
    }
  }

  handleGoogleClick(): void {
    this.loadGoogleScript().then(() => {
      this.initGoogle();
      const sdkBtn = document.querySelector('#googleSignInDiv button') as HTMLElement;
      if (sdkBtn) {
        sdkBtn.click();
        return;
      }
      (window as any).google?.accounts?.id?.prompt();
    });
  }

  // ── Login / Register ──────────────────────────────
  async handleSubmit(): Promise<void> {
    this.passwordError = '';

    if (this.isRegister) {
      await this.register();
    } else {
      await this.login();
    }
  }

  private async register(): Promise<void> {
    const userData = {
      role_id: 2,
      name: this.nombre,
      last_name: this.apellido,
      email: this.email,
      password: this.password,
    };

    try {
      await this.userService.registerUser(userData);
      Swal.fire({
        title: 'Éxito',
        text: 'Usuario registrado correctamente. Ahora puedes iniciar sesión.',
        icon: 'success',
      });
      this.nombre = '';
      this.apellido = '';
      this.email = '';
      this.password = '';
      this.isRegister = false;
    } catch (error: any) {
      this.passwordError = error?.error?.detail || error.message || 'Error registrando usuario';
      const msg = this.passwordError;
      if (!msg.includes('contraseña') && !msg.includes('caracter')) {
        Swal.fire({ title: 'Error', text: msg, icon: 'error' });
      }
    }
  }

  private async login(): Promise<void> {
    try {
      const result = await this.userService.loginUser(this.email, this.password);
      this.authService.setAuth(result.user, result.access_token);
      Swal.fire({ title: 'Bienvenido', text: `Hola ${result.user.name}`, icon: 'success' });
      this.redirectAfterLogin(result.user);
    } catch (error: any) {
      Swal.fire({
        title: 'Error',
        text: error?.error?.detail || error.message || 'Credenciales incorrectas',
        icon: 'error',
      });
    }
  }

  private redirectAfterLogin(user: any): void {
    const redirectUrl = getAndClearRedirectUrl();
    if (redirectUrl) {
      this.router.navigateByUrl(redirectUrl);
    } else {
      this.router.navigate([isAdminRole(user) ? '/admin' : '/']);
    }
  }

  toggleMode(): void {
    this.isRegister = !this.isRegister;
    this.passwordError = '';
  }
}
