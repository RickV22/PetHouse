import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class PetService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

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
}
