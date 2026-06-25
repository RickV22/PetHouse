import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { AuthService } from '../../../../core/services/auth.service';

interface UpcomingCare {
  type: string;
  icon: string;
  date: string;
  status: 'ok' | 'urgent' | 'pending';
  description: string;
  colorClass: string;
}

interface CareRecord {
  date: string;
  type: string;
  icon: string;
  notes: string;
}

interface ChatMessage {
  type: 'user' | 'bot';
  text: string;
}

@Component({
  selector: 'app-veterinario',
  standalone: true,
  imports: [CommonModule, FormsModule, NavbarComponent],
  templateUrl: './veterinario.component.html',
  styleUrls: ['./veterinario.component.css'],
})
export class VeterinarioComponent implements OnInit, OnDestroy {
  user: any = null;
  agentOpen = false;
  chatInput = '';
  chatMessages: ChatMessage[] = [];

  private authSub!: Subscription;

  // ── Mock data ──────────────────────────────────────────────────────────────
  mockPet = {
    name: 'Luna',
    species: 'Perro',
    breed: 'Golden Retriever',
    sex: 'Hembra',
    age: 3,
    photo: 'https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=500&q=80',
    bloodType: 'DEA 1.1+',
    allergies: ['Pollo', 'Polen'],
    conditions: ['Sin condiciones crónicas'],
    observations:
      'Muy activa. Necesita ejercicio diario mínimo 1 hora. Sensible al calor excesivo. Reactiva con perros desconocidos en la calle.',
  };

  upcomingCare: UpcomingCare[] = [
    {
      type: 'Vacuna Antirrábica',
      icon: '💉',
      date: '2026-07-15',
      status: 'pending',
      description: 'Refuerzo anual obligatorio',
      colorClass: 'care-teal',
    },
    {
      type: 'Desparasitación',
      icon: '🪱',
      date: '2026-07-01',
      status: 'urgent',
      description: 'Próxima dosis antiparasitaria',
      colorClass: 'care-coral',
    },
    {
      type: 'Baño',
      icon: '🛁',
      date: '2026-06-30',
      status: 'urgent',
      description: 'Baño con champú medicado',
      colorClass: 'care-sky',
    },
    {
      type: 'Corte de Uñas',
      icon: '✂️',
      date: '2026-07-05',
      status: 'pending',
      description: 'Mantenimiento mensual',
      colorClass: 'care-lavender',
    },
    {
      type: 'Control Veterinario',
      icon: '🩺',
      date: '2026-08-10',
      status: 'ok',
      description: 'Chequeo general semestral',
      colorClass: 'care-leaf',
    },
  ];

  careHistory: CareRecord[] = [
    {
      date: '2026-06-10',
      type: 'Vacuna Triple Canina',
      icon: '💉',
      notes: 'Aplicada sin reacciones adversas. Próxima dosis en 1 año.',
    },
    {
      date: '2026-05-22',
      type: 'Baño completo',
      icon: '🛁',
      notes: 'Baño con champú anti-pulgas y acondicionador. Sin irritación.',
    },
    {
      date: '2026-05-15',
      type: 'Control veterinario',
      icon: '🩺',
      notes: 'Peso: 28 kg. Excelente estado de salud general. Sin anomalías.',
    },
    {
      date: '2026-04-30',
      type: 'Desparasitación interna',
      icon: '🪱',
      notes: 'Pastilla antiparasitaria administrada. Sin efectos secundarios.',
    },
    {
      date: '2026-04-12',
      type: 'Corte de uñas',
      icon: '✂️',
      notes: 'Uñas cortadas y limadas. Sin sangrado. Buena conducta.',
    },
  ];

  notifications = [
    { message: 'Desparasitación de Luna vence en 7 días', icon: '🪱', urgency: 'urgent' },
    { message: 'Baño programado para mañana', icon: '🛁', urgency: 'info' },
    { message: 'Vacuna antirrábica en 3 semanas', icon: '💉', urgency: 'info' },
  ];
  // ──────────────────────────────────────────────────────────────────────────

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.authSub = this.authService.auth$.subscribe((auth) => {
      this.user = auth?.user ?? null;
    });
  }

  ngOnDestroy(): void {
    this.authSub.unsubscribe();
  }

  get urgentCount(): number {
    return this.upcomingCare.filter((c) => c.status === 'urgent').length;
  }

  openAgent(): void {
    this.agentOpen = true;
    if (this.chatMessages.length === 0) {
      this.chatMessages.push({
        type: 'bot',
        text: '¡Hola! 🐾 Soy el Agente Veterinario Virtual de PetHouse. Puedo orientarte sobre la salud de Luna. ¿En qué te puedo ayudar hoy?',
      });
    }
  }

  closeAgent(): void {
    this.agentOpen = false;
  }

  sendMessage(): void {
    if (!this.chatInput.trim()) return;
    this.chatMessages.push({ type: 'user', text: this.chatInput });
    this.chatInput = '';
    // Placeholder para futura integración con IA
    setTimeout(() => {
      this.chatMessages.push({
        type: 'bot',
        text: '🔬 Procesando tu consulta... (Integración con IA veterinaria próximamente)',
      });
    }, 800);
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }

  getDaysUntil(dateStr: string): number {
    const now = new Date();
    const target = new Date(dateStr);
    return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  }
}
