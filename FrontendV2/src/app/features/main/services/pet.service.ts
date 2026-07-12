import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface PetMedicalCard {
  id: number;
  pet_id: number;
  blood_type: string | null;
  allergies: string | null;
  conditions: string | null;
  observations: string | null;
  created_at: string;
  updated_at: string;
}

export interface PetReminder {
  id: number;
  pet_id: number;
  type: string;
  fecha: string;
  proxima_fecha: string | null;
  status: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PetMedicalCardPayload {
  blood_type?: string;
  allergies?: string;
  conditions?: string;
  observations?: string;
}

export interface PetReminderPayload {
  type?: string;
  fecha?: string;
  proxima_fecha?: string | null;
  status?: string;
  notes?: string;
}

@Injectable({ providedIn: 'root' })
export class PetService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private authHeaders(): { Authorization?: string } {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async createPet(formData: FormData): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/pets`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }

  async getPets(): Promise<any[]> {
    return firstValueFrom(this.http.get<any[]>(`${this.apiUrl}/pets`));
  }

  async getAvailablePets(): Promise<any[]> {
    return firstValueFrom(this.http.get<any[]>(`${this.apiUrl}/pets?status=AVAILABLE`));
  }

  async getPetById(id: string): Promise<any> {
    return firstValueFrom(this.http.get<any>(`${this.apiUrl}/pets/${id}`));
  }

  async submitAdoption(formData: FormData): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/adoptions/`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }
  async getAllPets(): Promise<any[]> {
    const data = await firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/pets`, {
        headers: this.authHeaders(),
      }),
    );
    return data?.data ?? data;
  }

  async getMyPets(): Promise<any[]> {
    return firstValueFrom(
      this.http.get<any[]>(`${this.apiUrl}/users/me/pets`, {
        headers: this.authHeaders(),
      }),
    );
  }

  async getPetMedicalCard(petId: number): Promise<PetMedicalCard | null> {
    return firstValueFrom(
      this.http.get<PetMedicalCard | null>(`${this.apiUrl}/pets/${petId}/medical-card`, {
        headers: this.authHeaders(),
      }),
    );
  }

  async savePetMedicalCard(petId: number, payload: PetMedicalCardPayload): Promise<PetMedicalCard> {
    return firstValueFrom(
      this.http.put<PetMedicalCard>(`${this.apiUrl}/pets/${petId}/medical-card`, payload, {
        headers: this.authHeaders(),
      }),
    );
  }

  async getPetReminders(petId: number): Promise<PetReminder[]> {
    return firstValueFrom(
      this.http.get<PetReminder[]>(`${this.apiUrl}/pets/${petId}/reminders`, {
        headers: this.authHeaders(),
      }),
    );
  }

  async getMyUpcomingReminders(days = 7): Promise<PetReminder[]> {
    return firstValueFrom(
      this.http.get<PetReminder[]>(`${this.apiUrl}/pet-reminders/my/upcoming?days=${days}`, {
        headers: this.authHeaders(),
      }),
    );
  }

  async createPetReminder(petId: number, payload: PetReminderPayload): Promise<PetReminder> {
    return firstValueFrom(
      this.http.post<PetReminder>(`${this.apiUrl}/pets/${petId}/reminders`, payload, {
        headers: this.authHeaders(),
      }),
    );
  }

  async updatePetReminder(reminderId: number, payload: PetReminderPayload): Promise<PetReminder> {
    return firstValueFrom(
      this.http.put<PetReminder>(`${this.apiUrl}/pet-reminders/${reminderId}`, payload, {
        headers: this.authHeaders(),
      }),
    );
  }

  async deletePetReminder(reminderId: number): Promise<{ message: string }> {
    return firstValueFrom(
      this.http.delete<{ message: string }>(`${this.apiUrl}/pet-reminders/${reminderId}`, {
        headers: this.authHeaders(),
      }),
    );
  }

  async updatePet(id: number, data: any): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.put(`${this.apiUrl}/pets/${id}`, data, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }

  async deletePet(id: number): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.delete(`${this.apiUrl}/pets/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }

  async sendSedeInstructions(id: number): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.post(
        `${this.apiUrl}/pets/${id}/send-instructions`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      ),
    );
  }
}
