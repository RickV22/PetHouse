import { Component, Input, Output, EventEmitter } from '@angular/core';
import { NgClass } from '@angular/common';
import { formatAge } from '../../utils/formatAge';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-pet-card',
  standalone: true,

  imports: [NgClass, CommonModule, RouterModule],
  templateUrl: './pet-card.html',
  styleUrl: './pet-card.css',
})
export class PetCardComponent {
  @Input() pet: any;
  @Output() view = new EventEmitter<void>();

  private statusMap: Record<string, string> = {
    AVAILABLE: 'Disponible',
    ADOPTED: 'Adoptado',
    RESERVED: 'Reservado',
    UNAVAILABLE: 'No disponible',
  };

  private statusColorMap: Record<string, string> = {
    AVAILABLE: 'status-available',
    ADOPTED: 'status-adopted',
    RESERVED: 'status-reserved',
    UNAVAILABLE: 'status-unavailable',
  };

  private speciesEmoji: Record<string, string> = {
    perro: '🐕',
    gato: '🐱',
    conejo: '🐰',
    ave: '🐦',
    hamster: '🐹',
    tortuga: '🐢',
    pez: '🐟',
  };

  get ageText(): string {
    return formatAge(this.pet.birth_date);
  }

  get statusText(): string {
    return this.statusMap[this.pet.status] ?? this.pet.status;
  }

  get statusColorClass(): string {
    return this.statusColorMap[this.pet.status] ?? 'status-adopted';
  }

  get emoji(): string {
    return this.speciesEmoji[this.pet.species?.toLowerCase()] ?? '🐾';
  }
}
