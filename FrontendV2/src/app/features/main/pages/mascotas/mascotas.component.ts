import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { PetCardComponent } from '../../../../shared/components/pet-card/pet-card';
import { PetModalComponent } from '../../../../shared/components/pet-modal/pet-modal';
import { PetService } from '../../../../core/services/pet.service';

@Component({
  selector: 'app-mascotas',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    NavbarComponent,
    PetCardComponent,
    PetModalComponent,
  ],
  templateUrl: './mascotas.component.html',
  styleUrls: ['./mascotas.component.css'],
})
export class MascotasComponent implements OnInit {
  pets: any[] = [];
  selectedPet: any = null;
  search = '';
  filterType = 'all';
  loading = true;

  constructor(private petService: PetService) {}

  async ngOnInit(): Promise<void> {
    try {
      this.pets = await this.petService.getAvailablePets();
    } catch (error) {
      console.error('Error fetching pets:', error);
    } finally {
      this.loading = false;
    }
  }

  get filteredPets(): any[] {
    const q = this.search.toLowerCase();
    return this.pets.filter((pet) => {
      const matchesSearch =
        pet.name.toLowerCase().includes(q) ||
        pet.species.toLowerCase().includes(q) ||
        (pet.race && pet.race.toLowerCase().includes(q));

      const matchesType =
        this.filterType === 'all' ||
        (this.filterType === 'otro'
          ? !['perro', 'gato'].includes(pet.species.toLowerCase())
          : pet.species.toLowerCase() === this.filterType);

      return matchesSearch && matchesType;
    });
  }

  setFilter(type: string): void {
    this.filterType = type;
  }

  openModal(pet: any): void {
    this.selectedPet = pet;
  }
  closeModal(): void {
    this.selectedPet = null;
  }

  resetFilters(): void {
    this.search = '';
    this.filterType = 'all';
  }
}
