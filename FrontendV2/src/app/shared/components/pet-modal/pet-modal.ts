import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { formatAge } from '../../utils/formatAge';

@Component({
  selector: 'app-pet-modal',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './pet-modal.html',
  styleUrls: ['./pet-modal.css'],
})
export class PetModalComponent {
  @Input() selectedPet!: any;
  @Output() closeModal = new EventEmitter<void>();

  private readonly statusMap: Record<string, string> = {
    AVAILABLE: 'Disponible',
    ADOPTED: 'Adoptado',
    RESERVED: 'Reservado',
    UNAVAILABLE: 'No disponible',
  };

  private readonly statusClassMap: Record<string, string> = {
    AVAILABLE: 'disponible',
    ADOPTED: 'adoptado',
    RESERVED: 'reservado',
    UNAVAILABLE: 'no-disponible',
  };

  private readonly speciesEmoji: Record<string, string> = {
    perro: '🐕',
    gato: '🐱',
    conejo: '🐰',
    ave: '🐦',
    hamster: '🐹',
    tortuga: '🐢',
    pez: '🐟',
  };

  constructor(private router: Router) {}

  get ageText(): string {
    return formatAge(this.selectedPet.birth_date);
  }

  get notAvailable(): boolean {
    return this.selectedPet.status !== 'AVAILABLE';
  }

  get statusText(): string {
    return this.statusMap[this.selectedPet.status] ?? this.selectedPet.status;
  }

  get statusClass(): string {
    return this.statusClassMap[this.selectedPet.status] ?? 'adoptado';
  }

  get emoji(): string {
    return this.speciesEmoji[this.selectedPet.species?.toLowerCase()] ?? '🐾';
  }

  get genderEmoji(): string {
    return this.selectedPet.gender === 'macho' ? '♂️' : '♀️';
  }

  @HostListener('document:keydown', ['$event'])
  handleKey(e: KeyboardEvent): void {
    if (e.key === 'Escape') this.close();
  }

  close(): void {
    this.closeModal.emit();
  }

  handleAdopt(): void {
    localStorage.setItem('selectedPet', JSON.stringify(this.selectedPet));
    this.router.navigate(['/adoptar'], {
      queryParams: { pet_id: this.selectedPet.id },
    });
    setTimeout(() => this.close(), 50);
  }
}
