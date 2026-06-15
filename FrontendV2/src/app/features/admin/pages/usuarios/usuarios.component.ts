import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Grid, h } from 'gridjs';
import Swal from 'sweetalert2';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { PasswordRequirementsComponent } from '../../../../shared/components/password-requirements/password-requirements';
import { UserService } from '../../../../core/services/user.service';
import { getUserRoleLabel, roleLabelToId } from '../../../../shared/utils/roles';

@Component({
  selector: 'app-admin-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule, AdminNavbarComponent, PasswordRequirementsComponent],
  templateUrl: './usuarios.component.html',
  styleUrls: ['./usuarios.component.css'],
})
export class AdminUsuariosComponent implements OnInit, OnDestroy {
  users: any[] = [];
  editUserId: number | null = null;
  sortOrder = 'recent';
  showPasswordReq = false;
  private grid: any;

  newUser = {
    name: '',
    last_name: '',
    email: '',
    password: '',
    role: 'Usuario',
    status: 'Activo',
  };

  constructor(private userService: UserService) {}

  async ngOnInit(): Promise<void> {
    await this.loadUsers();
  }

  ngOnDestroy(): void {
    this.grid?.destroy();
  }

  // ── Password validation ───────────────────────────
  get passwordRequirements() {
    const p = this.newUser.password;
    return {
      minLength: p.length >= 8,
      hasUppercase: /[A-Z]/.test(p),
      hasLowercase: /[a-z]/.test(p),
      hasNumber: /\d/.test(p),
      hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(p),
    };
  }

  get isPasswordValid(): boolean {
    return Object.values(this.passwordRequirements).every(Boolean);
  }

  isValidPassword(pwd: string): boolean {
    return (
      pwd.length >= 8 &&
      /[A-Z]/.test(pwd) &&
      /[a-z]/.test(pwd) &&
      /\d/.test(pwd) &&
      /[!@#$%^&*(),.?":{}|<>]/.test(pwd)
    );
  }

  // ── Load & render ─────────────────────────────────
  async loadUsers(): Promise<void> {
    try {
      this.users = await this.userService.getUsers();
      setTimeout(() => this.renderGrid(), 0);
    } catch (error) {
      console.error('Error cargando usuarios:', error);
    }
  }

  renderGrid(): void {
    this.grid?.destroy();

    const sorted = [...this.users].sort((a, b) =>
      this.sortOrder === 'recent'
        ? new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        : a.name.localeCompare(b.name),
    );

    this.grid = new Grid({
      columns: [
        'Nombre',
        'Apellido',
        'Correo',
        'Rol',
        { name: 'Fecha Registro', sort: true },
        {
          name: 'Acciones',
          formatter: (_: any, row: any) => {
            const user = row.cells[5]?.data;
            if (!user) return '';
            return h('div', {}, [
              h(
                'button',
                {
                  className: 'btn btn-sm btn-warning me-1',
                  onClick: () => this.startEdit(user),
                },
                'Editar',
              ),
              h(
                'button',
                {
                  className: 'btn btn-sm btn-danger',
                  onClick: () => this.removeUser(user.id),
                },
                'Eliminar',
              ),
            ]);
          },
        },
      ],
      data: sorted.map((u) => [
        u.name,
        u.last_name,
        u.email,
        getUserRoleLabel(u),
        u.created_at ? new Date(u.created_at).toLocaleDateString('es-CO') : '—',
        u,
      ]),
      search: true,
      sort: true,
      pagination: { limit: 5 },
    });

    this.grid.render(document.getElementById('table-wrapper'));
  }

  // ── CRUD ──────────────────────────────────────────
  async addUser(): Promise<void> {
    if (
      !this.newUser.name ||
      !this.newUser.last_name ||
      !this.newUser.email ||
      !this.newUser.password
    ) {
      Swal.fire({
        title: 'Campos incompletos',
        text: 'Por favor, rellena todos los campos.',
        icon: 'warning',
      });
      return;
    }

    if (!this.isValidPassword(this.newUser.password)) {
      Swal.fire({
        title: 'Contraseña inválida',
        text: 'La contraseña debe cumplir todos los requisitos.',
        icon: 'error',
      });
      return;
    }

    const userData = {
      name: this.newUser.name,
      last_name: this.newUser.last_name,
      email: this.newUser.email,
      password: this.newUser.password,
      role_id: roleLabelToId(this.newUser.role),
    };

    try {
      await this.userService.createUser(userData);
      await Swal.fire({
        title: '¡Usuario Creado!',
        text: `${userData.name} registrado correctamente.`,
        icon: 'success',
        timer: 2000,
        showConfirmButton: false,
      });
      await this.loadUsers();
      this.resetForm();
    } catch (error: any) {
      Swal.fire({
        title: 'Error',
        text: error?.error?.detail || 'No se pudo crear el usuario.',
        icon: 'error',
      });
    }
  }

  async removeUser(id: number): Promise<void> {
    const result = await Swal.fire({
      title: '¿Eliminar usuario?',
      text: 'Esta acción no se puede deshacer',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
    });

    if (!result.isConfirmed) return;

    try {
      await this.userService.deleteUser(id);
      await Swal.fire({
        title: 'Eliminado',
        text: 'El usuario fue eliminado correctamente',
        icon: 'success',
      });
      await this.loadUsers();
    } catch {
      Swal.fire({ title: 'Error', text: 'No se pudo eliminar el usuario', icon: 'error' });
    }
  }

  startEdit(user: any): void {
    this.editUserId = user.id;
    this.newUser = {
      name: user.name,
      last_name: user.last_name,
      email: user.email,
      password: '',
      role: getUserRoleLabel(user),
      status: user.status ?? 'Activo',
    };
  }

  async saveEdit(): Promise<void> {
    const userData: any = {
      name: this.newUser.name,
      last_name: this.newUser.last_name,
      email: this.newUser.email,
      role_id: roleLabelToId(this.newUser.role),
    };

    if (this.newUser.password) {
      if (!this.isValidPassword(this.newUser.password)) {
        Swal.fire({
          title: 'Contraseña inválida',
          text: 'La contraseña debe cumplir todos los requisitos.',
          icon: 'error',
        });
        return;
      }
      userData.password = this.newUser.password;
    }

    try {
      await this.userService.updateUser(this.editUserId!, userData);
      await this.loadUsers();
      this.resetForm();
      this.editUserId = null;
    } catch (error: any) {
      Swal.fire({
        title: 'Error',
        text: error?.error?.detail || 'No se pudo actualizar el usuario',
        icon: 'error',
      });
    }
  }

  cancelEdit(): void {
    this.editUserId = null;
    this.resetForm();
  }

  resetForm(): void {
    this.newUser = {
      name: '',
      last_name: '',
      email: '',
      password: '',
      role: 'Usuario',
      status: 'Activo',
    };
    this.showPasswordReq = false;
  }
}
