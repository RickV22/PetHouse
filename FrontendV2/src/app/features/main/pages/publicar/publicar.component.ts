import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import Swal from 'sweetalert2';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { PetService } from '../../../../core/services/pet.service';
import { AuthService } from '../../../../core/services/auth.service';
import { isAdminRole } from '../../../../shared/utils/roles';

@Component({
  selector: 'app-publicar',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './publicar.component.html',
  styleUrls: ['./publicar.component.css'],
})
export class PublicarComponent {
  name = '';
  species = '';
  race = '';
  birth_date = '';
  gender = '';
  description = '';
  imageFile: File | null = null;
  acceptedTerms = false;
  preview = '';
  isSubmitting = false;

  user: any = null;

  constructor(
    private petService: PetService,
    private authService: AuthService,
  ) {
    this.authService.auth$.subscribe((auth) => {
      this.user = auth?.user ?? null;
    });
  }

  handleImage(e: Event): void {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      this.imageFile = file;
      this.preview = URL.createObjectURL(file);
    }
  }

  removeImage(): void {
    this.preview = '';
    this.imageFile = null;
  }

  async publishPet(): Promise<void> {
    if (!this.name || !this.species) {
      Swal.fire({
        title: '¡Oops!',
        text: 'Debes completar los campos obligatorios 🐾',
        icon: 'warning',
        confirmButtonColor: '#F5B731',
      });
      return;
    }

    if (!this.acceptedTerms) {
      Swal.fire({
        title: 'Términos Legales',
        text: 'Debes aceptar los términos y condiciones para continuar.',
        icon: 'info',
        confirmButtonColor: '#F5B731',
      });
      return;
    }

    this.isSubmitting = true;

    const formData = new FormData();
    formData.append('name', this.name);
    formData.append('species', this.species);
    formData.append('race', this.race);
    formData.append('birth_date', this.birth_date);
    formData.append('gender', this.gender);
    formData.append('description', this.description);
    if (this.imageFile) {
      formData.append('image', this.imageFile);
    }

    try {
      await this.petService.createPet(formData);

      const isAdmin = isAdminRole(this.user);

      await Swal.fire({
        title: isAdmin ? '¡Publicada!' : '¡Solicitud Recibida! 🐾',
        html: isAdmin
          ? 'La mascota se ha publicado directamente.'
          : `Tu solicitud ha sido registrada.<br><br><b>Siguiente paso:</b> Acércate a nuestra casa de adopción para dejar a la mascota y completar el proceso oficial.`,
        icon: 'success',
        confirmButtonText: 'Entendido',
        confirmButtonColor: '#4361ee',
        background: '#FFF8F0',
        customClass: {
          popup: 'swal-cartoon-popup',
          confirmButton: 'swal-btn-confirm',
        },
        buttonsStyling: false,
      });

      this.resetForm();
    } catch (error: any) {
      Swal.fire('Error', error.message, 'error');
    } finally {
      this.isSubmitting = false;
    }
  }

  private resetForm(): void {
    this.name = '';
    this.species = '';
    this.race = '';
    this.birth_date = '';
    this.gender = '';
    this.description = '';
    this.imageFile = null;
    this.preview = '';
    this.acceptedTerms = false;
  }
}
