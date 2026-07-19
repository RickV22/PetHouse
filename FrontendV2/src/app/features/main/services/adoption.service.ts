import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment.development';

@Injectable({ providedIn: 'root' })
export class AdoptionService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders() {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  }

  async getAdoptions(): Promise<any[]> {
    const data = await firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/adoptions/`, {
        headers: this.getHeaders(),
      }),
    );
    return data?.data ?? data;
  }

  async getAdoptionById(id: number): Promise<any> {
    const data = await firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/adoptions/${id}`, {
        headers: this.getHeaders(),
      }),
    );
    return data?.data ?? data;
  }

  async changeAdoptionStatus(id: number, statusId: number): Promise<any> {
    return firstValueFrom(
      this.http.put(
        `${this.apiUrl}/adoptions/${id}/status`,
        { status_id: statusId },
        {
          headers: this.getHeaders(),
        },
      ),
    );
  }
}
