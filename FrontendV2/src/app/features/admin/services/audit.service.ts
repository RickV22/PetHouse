import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuditService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders() {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  }

  async getAuditLogs(params: any = {}): Promise<any[]> {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${this.apiUrl}/audit-logs/?${query}` : `${this.apiUrl}/audit-logs/`;

    try {
      const data = await firstValueFrom(
        this.http.get<any>(url, {
          headers: this.getHeaders(),
        }),
      );

      if (Array.isArray(data)) {
        return data;
      }
      if (Array.isArray(data?.data)) {
        return data.data;
      }
      if (Array.isArray(data?.items)) {
        return data.items;
      }
      return [];
    } catch {
      return [];
    }
  }

  async getUsers(): Promise<any[]> {
    try {
      const data = await firstValueFrom(
        this.http.get<any>(`${this.apiUrl}/users/`, {
          headers: this.getHeaders(),
        }),
      );

      if (Array.isArray(data)) {
        return data;
      }
      if (Array.isArray(data?.data)) {
        return data.data;
      }
      if (Array.isArray(data?.items)) {
        return data.items;
      }
      return [];
    } catch {
      return [];
    }
  }

  async exportAuditLogsCSV(params: any = {}): Promise<{ content: string; filename: string }> {
    const query = new URLSearchParams(params).toString();
    const url = query
      ? `${this.apiUrl}/audit-logs/export/csv?${query}`
      : `${this.apiUrl}/audit-logs/export/csv`;

    return firstValueFrom(
      this.http.get<any>(url, {
        headers: this.getHeaders(),
      }),
    );
  }
}
