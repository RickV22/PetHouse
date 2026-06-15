import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuditService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private getHeaders() {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  }

  async getAuditLogs(params: any = {}): Promise<any[]> {
    const query = new URLSearchParams(params).toString();
    const data = await firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/audit/?${query}`, {
        headers: this.getHeaders(),
      }),
    );
    return Array.isArray(data) ? data : (data?.data ?? []);
  }

  async getUsers(): Promise<any[]> {
    return firstValueFrom(
      this.http.get<any[]>(`${this.apiUrl}/users/`, {
        headers: this.getHeaders(),
      }),
    );
  }

  async exportAuditLogsCSV(params: any = {}): Promise<{ content: string; filename: string }> {
    const query = new URLSearchParams(params).toString();
    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/audit/export?${query}`, {
        headers: this.getHeaders(),
      }),
    );
  }
}
