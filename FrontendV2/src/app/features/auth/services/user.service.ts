import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class UserService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  async registerUser(userData: any): Promise<any> {
    return firstValueFrom(this.http.post(`${this.apiUrl}/users/register`, userData));
  }

  async loginUser(email: string, password: string): Promise<any> {
    return firstValueFrom(this.http.post(`${this.apiUrl}/users/login`, { email, password }));
  }

  async googleLogin(idToken: string): Promise<any> {
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/users/google-login`, { id_token: idToken }),
    );
  }

  // El usuario actualiza su propio perfil (ej: aceptar política de datos)
  async updateUser(id: number, userData: any): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.put(`${this.apiUrl}/users/${id}`, userData, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }

  async unlinkTelegram(userId: number): Promise<any> {
    const token = localStorage.getItem('token');
    return firstValueFrom(
      this.http.patch(`${this.apiUrl}/users/unlink-telegram/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    );
  }
}
