import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { PetService } from '../../../../core/services/pet.service';
import { formatAge } from '../../../../shared/utils/formatAge';

@Component({
  selector: 'app-adoptar',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './adoptar.component.html',
  styleUrls: ['./adoptar.component.css'],
})
export class AdoptarComponent implements OnInit {
  pet: any = null;
  loading = true;
  cedulaFile: File | null = null;
  reciboFile: File | null = null;
  acceptedTerms = false;
  message = '';
  success = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private petService: PetService,
  ) {}

  async ngOnInit(): Promise<void> {
    // 1. Intentar desde localStorage
    const stored = localStorage.getItem('selectedPet');
    if (stored) {
      this.pet = JSON.parse(stored);
      this.loading = false;
      return;
    }

    // 2. Intentar desde query param
    const petId = this.route.snapshot.queryParamMap.get('pet_id');
    if (petId) {
      try {
        this.pet = await this.petService.getPetById(petId);
      } catch (e) {
        console.error('Error fetching pet:', e);
      }
    }

    this.loading = false;
  }

  get ageText(): string {
    return this.pet ? formatAge(this.pet.birth_date) : 'Desconocida';
  }

  handleCedula(e: Event): void {
    const input = e.target as HTMLInputElement;
    this.cedulaFile = input.files?.[0] ?? null;
  }

  handleRecibo(e: Event): void {
    const input = e.target as HTMLInputElement;
    this.reciboFile = input.files?.[0] ?? null;
  }

  async submitSolicitud(): Promise<void> {
    this.message = '';

    if (!this.cedulaFile || !this.reciboFile) {
      this.message = 'Debes subir tu cédula y recibo de servicios';
      this.success = false;
      return;
    }

    if (!this.acceptedTerms) {
      this.message = 'Debes aceptar los términos y el compromiso de adopción responsable';
      this.success = false;
      return;
    }

    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    if (!token || !userStr) {
      this.message = 'Debes iniciar sesión para adoptar';
      this.success = false;
      return;
    }

    try {
      this.loading = true;

      const fd = new FormData();
      fd.append('pet_id', this.pet.id);
      fd.append('cedula', this.cedulaFile);
      fd.append('recibo', this.reciboFile);

      await this.petService.submitAdoption(fd);

      this.message = 'Solicitud enviada correctamente';
      this.success = true;
      this.cedulaFile = null;
      this.reciboFile = null;
      localStorage.removeItem('selectedPet');

      setTimeout(() => this.router.navigate(['/mascotas']), 2000);
    } catch (e: any) {
      this.message = e?.error?.detail || e?.error?.message || 'No se pudo enviar la solicitud';
      this.success = false;
      console.error(e);
    } finally {
      this.loading = false;
    }
  }
}
