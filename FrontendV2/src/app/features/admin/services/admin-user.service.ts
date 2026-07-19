import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AdminUserService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders() {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  }

  async getUsers(): Promise<any[]> {
    const data = await firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/users/`, {
        headers: this.getHeaders(),
      }),
    );
    return data?.data ?? data;
  }

  async createUser(userData: any): Promise<any> {
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/users/`, userData, {
        headers: this.getHeaders(),
      }),
    );
  }

  async updateUser(id: number, userData: any): Promise<any> {
    return firstValueFrom(
      this.http.put(`${this.apiUrl}/users/${id}`, userData, {
        headers: this.getHeaders(),
      }),
    );
  }

  async deleteUser(id: number): Promise<any> {
    return firstValueFrom(
      this.http.delete(`${this.apiUrl}/users/${id}`, {
        headers: this.getHeaders(),
      }),
    );
  }
}
