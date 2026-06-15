import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class UserService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  async registerUser(userData: any): Promise<any> {
    return firstValueFrom(this.http.post(`${this.apiUrl}/users/`, userData));
  }

  async loginUser(email: string, password: string): Promise<any> {
    return firstValueFrom(this.http.post(`${this.apiUrl}/users/login`, { email, password }));
  }

  async googleLogin(idToken: string): Promise<any> {
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/users/google-login`, { id_token: idToken }),
    );
  }
  async getUsers(): Promise<any[]> {
    const token = localStorage.getItem('token');
    const data = await firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/users/`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
    return data?.data ?? data;
  }

  async createUser(userData: any): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/users/`, userData, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }

  async updateUser(id: number, userData: any): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.put(`${this.apiUrl}/users/${id}`, userData, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }

  async deleteUser(id: number): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.delete(`${this.apiUrl}/users/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }
}
