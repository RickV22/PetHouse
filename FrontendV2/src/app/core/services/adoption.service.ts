import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AdoptionService {
  private apiUrl = 'http://localhost:8000';

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
