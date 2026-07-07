import { ChangeDetectorRef, Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import Swal from 'sweetalert2';
import { Router, RouterModule } from '@angular/router';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';
import { AuthService } from '../../../auth/services/auth.service';
import { UserService } from '../../../auth/services/user.service';
import { PetMedicalCard, PetReminder, PetService } from '../../services/pet.service';
import { VeterinarioChatService } from '../../../../core/services/veterinario-chat.service';

interface UpcomingCare {
  id: number;
  type: string;
  icon: string;
  date: string;
  status: 'ok' | 'urgent' | 'pending';
  description: string;
  colorClass: string;
}

interface CareRecord {
  id: number;
  date: string;
  type: string;
  icon: string;
  notes: string;
}

interface ChatMessage {
  type: 'user' | 'bot';
  text: string;
}

interface ReminderNotification {
  careType: string;
  icon: string;
  date: string;
  daysLeft: number;
  urgency: 'urgent' | 'info';
  message: string;
}

@Component({
  selector: 'app-veterinario',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, NavbarComponent],
  templateUrl: './veterinario.component.html',
  styleUrls: ['./veterinario.component.css'],
})
export class VeterinarioComponent implements OnInit, OnDestroy {
  user: any = null;
  pets: any[] = [];
  selectedPetId: number | null = null;
  selectedPet: any | null = null;
  loadingPets = true;
  loadingHealthData = false;
  savingCard = false;
  savingReminder = false;
  editingMedicalCard = false;
  currentMedicalCard: PetMedicalCard | null = null;

  medicalCardForm = {
    bloodType: '',
    allergies: '',
    conditions: '',
    observations: '',
  };

  reminderForm = {
    type: '',
    fecha: '',
    notes: '',
  };

  agentOpen = false;
  bellOpen = false;
  isBellSticky = false;
  chatInput = '';
  chatMessages: ChatMessage[] = [];
  allReminders: PetReminder[] = [];
  private readonly notificationWindowDays = 7;

  private authSub!: Subscription;

  upcomingCare: UpcomingCare[] = [];
  careHistory: CareRecord[] = [];

  constructor(
    private authService: AuthService,
    private userService: UserService,
    private petService: PetService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private veterinarioChat: VeterinarioChatService,
  ) {}

  ngOnInit(): void {
    this.authSub = this.authService.auth$.subscribe(async (auth) => {
      this.user = auth?.user ?? null;
      if (this.user) {
        await this.loadInitialData();
      } else {
        this.clearViewState();
      }
    });
  }

  ngOnDestroy(): void {
    this.authSub.unsubscribe();
  }

  @HostListener('window:scroll')
  onWindowScroll(): void {
    this.isBellSticky = window.scrollY > 120;
  }

  hasTelegramLinked(): boolean {
    return !!this.user?.telegram_chat_id;
  }

  getTelegramBotLink(): string {
    const botUsername = 'Togopet_bot';
    return `https://t.me/${botUsername}?start=${this.user?.id}`;
  }

  async unlinkTelegram(): Promise<void> {
    const result = await Swal.fire({
      title: '¿Desvincular Telegram?',
      text: 'Ya no recibirás recordatorios ni podrás consultar al asistente por Telegram.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#FF6B6B',
      cancelButtonColor: '#6c757d',
      confirmButtonText: 'Sí, desvincular',
      cancelButtonText: 'Cancelar',
      background: '#FFF8F0',
      customClass: {
        confirmButton: 'swal-btn-confirm',
        cancelButton: 'swal-btn-cancel',
        popup: 'swal-cartoon-popup',
      },
      buttonsStyling: false,
    });

    if (!result.isConfirmed) return;

    try {
      const updatedUser = await this.userService.unlinkTelegram(this.user.id);
      // Actualizar estado local sin cerrar sesión
      const merged = { ...this.user, telegram_chat_id: null };
      this.authService.setAuth(merged, localStorage.getItem('token')!);
      this.user = merged;
      this.cdr.detectChanges();

      await Swal.fire({
        title: '¡Desvinculado! 📱',
        text: 'Tu cuenta de Telegram ha sido desvinculada correctamente.',
        icon: 'success',
        timer: 2000,
        showConfirmButton: false,
        background: '#FFF8F0',
      });
    } catch (err) {
      console.error('[ERROR] No se pudo desvincular Telegram:', err);
      Swal.fire({
        title: 'Error',
        text: 'No se pudo desvincular Telegram. Intenta de nuevo.',
        icon: 'error',
        background: '#FFF8F0',
      });
    }
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.bellOpen) return;

    const target = event.target;
    if (!(target instanceof Element) || !target.closest('.notif-top-anchor')) {
      this.bellOpen = false;
    }
  }

  @HostListener('document:keydown.escape')
  onEscapePress(): void {
    this.bellOpen = false;
  }

  async onPetSelectionChange(): Promise<void> {
    if (!this.selectedPetId) {
      this.selectedPet = null;
      this.cdr.detectChanges();
      return;
    }

    this.selectedPet = this.pets.find((pet) => pet.id === this.selectedPetId) ?? null;
    if (this.selectedPet) {
      await this.loadPetHealthData(this.selectedPet.id);
    }
    this.cdr.detectChanges();
  }

  async saveMedicalCard(): Promise<void> {
    if (!this.selectedPet) return;

    this.savingCard = true;
    try {
      const savedCard = await this.petService.savePetMedicalCard(this.selectedPet.id, {
        blood_type: this.medicalCardForm.bloodType.trim() || '',
        allergies: this.medicalCardForm.allergies.trim() || '',
        conditions: this.medicalCardForm.conditions.trim() || '',
        observations: this.medicalCardForm.observations.trim() || '',
      });

      this.currentMedicalCard = savedCard;
      this.editingMedicalCard = false;

      await Swal.fire({
        title: 'Guardado',
        text: 'El carnet de salud fue actualizado.',
        icon: 'success',
        timer: 1700,
        showConfirmButton: false,
      });
    } catch (error) {
      if (this.handleAuthError(error)) return;
      console.error('Error guardando carnet:', error);
      await Swal.fire('Error', 'No se pudo guardar el carnet de salud.', 'error');
    } finally {
      this.savingCard = false;
      this.cdr.detectChanges();
    }
  }

  async addReminder(): Promise<void> {
    if (!this.selectedPet || !this.reminderForm.type.trim() || !this.reminderForm.fecha) {
      await Swal.fire('Faltan datos', 'Debes indicar tipo y fecha del recordatorio.', 'info');
      return;
    }

    this.savingReminder = true;
    try {
      await this.petService.createPetReminder(this.selectedPet.id, {
        type: this.reminderForm.type.trim(),
        fecha: this.reminderForm.fecha,
        notes: this.reminderForm.notes.trim() || undefined,
        status: 'pendiente',
      });

      this.reminderForm = { type: '', fecha: '', notes: '' };
      await this.loadPetHealthData(this.selectedPet.id);
    } catch (error) {
      if (this.handleAuthError(error)) return;
      console.error('Error creando recordatorio:', error);
      await Swal.fire('Error', 'No se pudo crear el recordatorio.', 'error');
    } finally {
      this.savingReminder = false;
      this.cdr.detectChanges();
    }
  }

  async markReminderAsSent(reminder: UpcomingCare): Promise<void> {
    if (!this.selectedPet) return;

    try {
      await this.petService.updatePetReminder(reminder.id, { status: 'enviado' });
      await this.loadPetHealthData(this.selectedPet.id);
      this.cdr.detectChanges();
    } catch (error) {
      if (this.handleAuthError(error)) return;
      console.error('Error marcando recordatorio:', error);
      await Swal.fire('Error', 'No se pudo actualizar el recordatorio.', 'error');
    }
  }

  async deleteReminder(reminderId: number): Promise<void> {
    if (!this.selectedPet) return;

    const result = await Swal.fire({
      title: 'Eliminar recordatorio',
      text: 'Esta acción no se puede deshacer.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Eliminar',
      cancelButtonText: 'Cancelar',
    });

    if (!result.isConfirmed) return;

    try {
      await this.petService.deletePetReminder(reminderId);
      await this.loadPetHealthData(this.selectedPet.id);
      this.cdr.detectChanges();
    } catch (error) {
      if (this.handleAuthError(error)) return;
      console.error('Error eliminando recordatorio:', error);
      await Swal.fire('Error', 'No se pudo eliminar el recordatorio.', 'error');
    }
  }

  get urgentCount(): number {
    return this.reminderNotifications.filter((n) => n.urgency === 'urgent').length;
  }

  get bellCount(): number {
    return this.reminderNotifications.length;
  }

  get hasActiveReminders(): boolean {
    return this.bellCount > 0;
  }

  get hasUrgentReminders(): boolean {
    return this.urgentCount > 0;
  }

  get reminderNotifications(): ReminderNotification[] {
    return this.upcomingCare
      .map((care) => {
        const daysLeft = this.getDaysUntil(care.date);
        const urgency: 'urgent' | 'info' = daysLeft <= 2 ? 'urgent' : 'info';

        return {
          careType: care.type,
          icon: care.icon,
          date: care.date,
          daysLeft,
          urgency,
          message: `${care.type} ${this.formatRelativeDay(daysLeft)}`,
        };
      })
      .filter((notification) => notification.daysLeft >= 0)
      .filter((notification) => notification.daysLeft <= this.notificationWindowDays)
      .sort((a, b) => a.daysLeft - b.daysLeft);
  }

  toggleBellPanel(): void {
    this.bellOpen = !this.bellOpen;
  }

  openAgent(): void {
    const petName = this.selectedPet?.name ?? 'tu mascota';
    this.agentOpen = true;
    if (this.chatMessages.length === 0) {
      this.chatMessages.push({
        type: 'bot',
        text: `¡Hola! 🐾 Soy el Agente Veterinario Virtual de PetHouse. Puedo orientarte sobre la salud de ${petName}. ¿En qué te puedo ayudar hoy?`,
      });
    }
  }

  closeAgent(): void {
    this.agentOpen = false;
  }

  sendMessage(): void {

    if (!this.chatInput.trim()) return;

    const pregunta = this.chatInput;

    this.chatMessages.push({
      type: 'user',
      text: pregunta
    });

    this.chatInput = '';

    // Mensaje temporal mientras responde la IA
    this.chatMessages.push({
      type: 'bot',
      text: '🔬 Analizando la información...'
    });

    this.veterinarioChat
      .enviarMensaje(this.selectedPet.id, pregunta)
      .subscribe({

        next: (resp: any) => {

          // Elimina el mensaje temporal
          this.chatMessages.pop();

          this.chatMessages.push({
            type: 'bot',
            text: resp.respuesta
          });

          this.cdr.detectChanges();

        },

        error: () => {

          this.chatMessages.pop();

          this.chatMessages.push({
            type: 'bot',
            text: '❌ No fue posible comunicarse con el Veterinario IA.'
          });

          this.cdr.detectChanges();

        }

      });

  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString('es-ES', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  getDaysUntil(dateStr: string): number {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const targetDate = new Date(dateStr);
    const target = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
    return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  }

  get selectedPetImage(): string {
    return (
      this.selectedPet?.image_url ||
      'https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=500&q=80'
    );
  }

  get selectedPetRace(): string {
    return this.selectedPet?.race || 'Raza no registrada';
  }

  get selectedPetGender(): string {
    return this.selectedPet?.gender || 'No definido';
  }

  get selectedPetAge(): string {
    const birthDate = this.selectedPet?.birth_date;
    if (!birthDate) return 'No registrada';

    const birth = new Date(birthDate);
    if (Number.isNaN(birth.getTime())) return 'No registrada';

    const now = new Date();
    if (birth > now) return 'No registrada';

    let years = now.getFullYear() - birth.getFullYear();
    let months = now.getMonth() - birth.getMonth();

    if (now.getDate() < birth.getDate()) {
      months -= 1;
    }

    if (months < 0) {
      years -= 1;
      months += 12;
    }

    if (years < 0) return 'No registrada';

    if (years === 0) {
      if (months === 0) {
        const diffMs = now.getTime() - birth.getTime();
        const days = Math.max(Math.floor(diffMs / (1000 * 60 * 60 * 24)), 0);
        return `${days} ${days === 1 ? 'día' : 'días'}`;
      }

      const safeMonths = Math.max(months, 0);
      return `${safeMonths} ${safeMonths === 1 ? 'mes' : 'meses'}`;
    }

    return `${years} ${years === 1 ? 'año' : 'años'}`;
  }

  get allergiesList(): string[] {
    return this.splitByComma(this.medicalCardForm.allergies);
  }

  get conditionsList(): string[] {
    return this.splitByComma(this.medicalCardForm.conditions);
  }

  get hasMedicalCardData(): boolean {
    return Boolean(
      this.medicalCardForm.bloodType.trim() ||
      this.medicalCardForm.allergies.trim() ||
      this.medicalCardForm.conditions.trim() ||
      this.medicalCardForm.observations.trim(),
    );
  }

  startMedicalCardEdit(): void {
    this.editingMedicalCard = true;
  }

  cancelMedicalCardEdit(): void {
    this.editingMedicalCard = false;
    this.applyMedicalCard(this.currentMedicalCard);
    this.cdr.detectChanges();
  }

  private async loadInitialData(): Promise<void> {
    this.loadingPets = true;

    try {
      this.pets = await this.petService.getMyPets();
      if (this.pets.length === 0) {
        this.clearHealthData();
        this.selectedPet = null;
        this.selectedPetId = null;
        return;
      }

      if (!this.selectedPetId || !this.pets.some((pet) => pet.id === this.selectedPetId)) {
        this.selectedPetId = this.pets[0].id;
      }

      this.selectedPet = this.pets.find((pet) => pet.id === this.selectedPetId) ?? this.pets[0];
      await this.loadPetHealthData(this.selectedPet.id);
    } catch (error) {
      if (this.handleAuthError(error)) return;
      console.error('Error cargando mascotas del usuario:', error);
      this.clearHealthData();
      await Swal.fire('Error', 'No se pudo cargar la información veterinaria.', 'error');
    } finally {
      this.loadingPets = false;
      this.cdr.detectChanges();
    }
  }

  private async loadPetHealthData(petId: number): Promise<void> {
    this.loadingHealthData = true;

    try {
      const [medicalCard, reminders] = await Promise.all([
        this.petService.getPetMedicalCard(petId),
        this.petService.getPetReminders(petId),
      ]);

      this.applyMedicalCard(medicalCard);
      this.applyReminders(reminders);
    } catch (error) {
      if (this.handleAuthError(error)) return;
      console.error('Error cargando salud de la mascota:', error);
      this.clearHealthData();
    } finally {
      this.loadingHealthData = false;
      this.cdr.detectChanges();
    }
  }

  private applyMedicalCard(card: PetMedicalCard | null): void {
    this.currentMedicalCard = card;
    this.medicalCardForm = {
      bloodType: card?.blood_type || '',
      allergies: card?.allergies || '',
      conditions: card?.conditions || '',
      observations: card?.observations || '',
    };
  }

  private applyReminders(reminders: PetReminder[]): void {
    this.allReminders = reminders;

    const upcoming = reminders
      .filter((reminder) => {
        const daysLeft = this.getDaysUntil(reminder.fecha);
        const status = (reminder.status || 'pendiente').toLowerCase();
        return status === 'pendiente' && daysLeft >= 0;
      })
      .map((reminder) => {
        const daysLeft = this.getDaysUntil(reminder.fecha);
        const status: 'ok' | 'urgent' | 'pending' =
          daysLeft <= 2 ? 'urgent' : daysLeft <= this.notificationWindowDays ? 'pending' : 'ok';

        return {
          id: reminder.id,
          type: reminder.type,
          icon: this.getCareIcon(reminder.type),
          date: reminder.fecha,
          status,
          description: reminder.notes || 'Recordatorio de cuidado',
          colorClass: this.getCareColor(reminder.type),
        } satisfies UpcomingCare;
      })
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    this.upcomingCare = upcoming;

    const history = reminders
      .filter((reminder) => {
        const daysLeft = this.getDaysUntil(reminder.fecha);
        const status = (reminder.status || 'pendiente').toLowerCase();
        return status === 'enviado' || daysLeft < 0;
      })
      .map((reminder) => ({
        id: reminder.id,
        date: reminder.fecha,
        type: reminder.type,
        icon: this.getCareIcon(reminder.type),
        notes: reminder.notes || 'Sin notas registradas.',
      }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    this.careHistory = history;
  }

  private splitByComma(value: string): string[] {
    return value
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }

  private getCareIcon(type: string): string {
    const normalized = type.toLowerCase();
    if (normalized.includes('vacuna')) return '💉';
    if (normalized.includes('desparas')) return '🪱';
    if (normalized.includes('baño') || normalized.includes('bano')) return '🛁';
    if (normalized.includes('uña') || normalized.includes('una')) return '✂️';
    if (normalized.includes('control') || normalized.includes('veterin')) return '🩺';
    return '🐾';
  }

  private getCareColor(type: string): string {
    const normalized = type.toLowerCase();
    if (normalized.includes('vacuna')) return 'care-teal';
    if (normalized.includes('desparas')) return 'care-coral';
    if (normalized.includes('baño') || normalized.includes('bano')) return 'care-sky';
    if (normalized.includes('uña') || normalized.includes('una')) return 'care-lavender';
    if (normalized.includes('control') || normalized.includes('veterin')) return 'care-leaf';
    return 'care-teal';
  }

  private clearHealthData(): void {
    this.medicalCardForm = {
      bloodType: '',
      allergies: '',
      conditions: '',
      observations: '',
    };
    this.reminderForm = { type: '', fecha: '', notes: '' };
    this.upcomingCare = [];
    this.careHistory = [];
    this.allReminders = [];
    this.currentMedicalCard = null;
    this.editingMedicalCard = false;
  }

  private clearViewState(): void {
    this.pets = [];
    this.selectedPet = null;
    this.selectedPetId = null;
    this.loadingPets = false;
    this.loadingHealthData = false;
    this.clearHealthData();
  }

  private handleAuthError(error: unknown): boolean {
    if (!(error instanceof HttpErrorResponse)) return false;
    if (error.status !== 401) return false;

    this.authService.clearAuth();
    void this.router.navigate(['/login'], {
      queryParams: { message: 'Tu sesión expiró. Inicia sesión de nuevo.' },
    });
    return true;
  }

  private formatRelativeDay(daysLeft: number): string {
    if (daysLeft === 0) {
      return 'vence hoy';
    }
    if (daysLeft === 1) {
      return 'vence mañana';
    }
    return `vence en ${daysLeft} días`;
  }
}
