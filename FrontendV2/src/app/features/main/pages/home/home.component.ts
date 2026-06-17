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
    // ── DATOS DE PRUEBA (eliminar cuando el backend esté disponible) ──
    this.pets = [
      {
        id: 1,
        name: 'Bobby',
        species: 'perro',
        race: 'Golden Retriever',
        gender: 'macho',
        birth_date: '2022-03-15',
        status: 'AVAILABLE',
        description: 'Muy juguetón, le encanta correr en el parque y es excelente con los niños.',
        image_url: 'https://images.unsplash.com/photo-1633722715463-d30f4f325e24?w=400',
      },
      {
        id: 2,
        name: 'Misu',
        species: 'gato',
        race: 'Siamés',
        gender: 'hembra',
        birth_date: '2023-06-10',
        status: 'AVAILABLE',
        description: 'Tranquila y cariñosa, perfecta para apartamentos.',
        image_url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=400',
      },
      {
        id: 3,
        name: 'Rocky',
        species: 'perro',
        race: 'Bulldog Francés',
        gender: 'macho',
        birth_date: '2021-11-20',
        status: 'ADOPTED',
        description: 'Activo y leal, ya encontró su hogar para siempre.',
        image_url: 'https://images.unsplash.com/photo-1583512603805-3cc6b41f3edb?w=400',
      },
      {
        id: 4,
        name: 'Luna',
        species: 'gato',
        race: 'Persa',
        gender: 'hembra',
        birth_date: '2023-01-05',
        status: 'RESERVED',
        description: 'Curiosa y elegante, le gusta dormir en lugares cálidos.',
        image_url: 'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400',
      },
    ];

    // ── BACKEND REAL: descomentar cuando esté disponible ──
    // this.petService.getAvailablePets().then(pets => this.pets = pets);
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
