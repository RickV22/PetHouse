import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Title, Meta } from '@angular/platform-browser';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { PetCardComponent } from '../../../../shared/components/pet-card/pet-card';
import { PetModalComponent } from '../../../../shared/components/pet-modal/pet-modal';
import { PetSearchComponent } from '../../../../shared/components/search-bar/search-bar';
import { PetService } from '../../services/pet.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NavbarComponent,
    PetCardComponent,
    PetModalComponent,
    PetSearchComponent,
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
})
export class HomeComponent implements OnInit {
  allPets: any[] = [];
  pets: any[] = [];
  selectedPet: any = null;
  search = '';
  isLoading = true;
  readonly MAX_PREVIEW = 8;

  constructor(
    private titleService: Title,
    private metaService: Meta,
    private petService: PetService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone,
  ) {}

  async ngOnInit(): Promise<void> {
    this.titleService.setTitle('PetHouse');
    this.metaService.updateTag({
      name: 'description',
      content:
        'Adopta una mascota, encuentra tu compañero ideal. PetHouse es la plataforma más cálida para darle hogar a quien más lo necesita.',
    });

    await this.loadPets();
  }

  async loadPets(): Promise<void> {
    this.isLoading = true;
    try {
      const allPets = await this.petService.getPets();
      this.allPets = Array.isArray(allPets) ? allPets : [];
      this.pets = this.allPets.filter(
        (pet) => pet.status !== 'REJECTED' && pet.status !== 'PENDING_APPROVAL',
      );
      this.cdr.detectChanges();
    } catch (error) {
      console.error('Error cargando mascotas:', error);
    } finally {
      this.isLoading = false;
      this.cdr.detectChanges();
    }
  }

  get filteredPets(): any[] {
    const q = this.search.toLowerCase();
    return this.pets.filter(
      (pet) =>
        pet.name.toLowerCase().includes(q) ||
        pet.species.toLowerCase().includes(q) ||
        (pet.race && pet.race.toLowerCase().includes(q)),
    );
  }

  get previewPets(): any[] {
    return this.filteredPets.slice(0, this.MAX_PREVIEW);
  }

  get hasMore(): boolean {
    return this.filteredPets.length > this.MAX_PREVIEW;
  }

  get extraCount(): number {
    return this.filteredPets.length - this.MAX_PREVIEW;
  }

  get adoptedCount(): number {
    return this.allPets.filter((p) => p.status === 'ADOPTED').length;
  }

  openModal(pet: any): void {
    this.ngZone.run(() => {
      this.selectedPet = pet;
      this.cdr.detectChanges();
    });
  }

  closeModal(): void {
    this.ngZone.run(() => {
      this.selectedPet = null;
      this.cdr.detectChanges();
    });
  }
}
