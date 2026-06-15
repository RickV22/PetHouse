import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Title, Meta } from '@angular/platform-browser';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { PetCardComponent } from '../../../../shared/components/pet-card/pet-card';
import { PetModalComponent } from '../../../../shared/components/pet-modal/pet-modal';
import { PetSearchComponent } from '../../../../shared/components/search-bar/search-bar';

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
  pets: any[] = [];
  selectedPet: any = null;
  search = '';
  readonly MAX_PREVIEW = 8;

  constructor(
    private titleService: Title,
    private metaService: Meta,
    // private petService: PetService  ← cuando tengas el servicio
  ) {}

  ngOnInit(): void {
    this.titleService.setTitle('PetHouse');
    this.metaService.updateTag({
      name: 'description',
      content:
        'Adopta una mascota, encuentra tu compañero ideal. PetHouse es la plataforma más cálida para darle hogar a quien más lo necesita.',
    });

    this.loadPets();
  }

  loadPets(): void {
    // this.petService.getPets().subscribe(pets => this.pets = pets);
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
    return this.pets.filter((p) => p.status === 'ADOPTED').length;
  }

  openModal(pet: any): void {
    this.selectedPet = pet;
  }

  closeModal(): void {
    this.selectedPet = null;
  }
}
