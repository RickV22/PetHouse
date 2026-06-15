import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private authSubject = new BehaviorSubject<any>(this.loadFromStorage());

  auth$ = this.authSubject.asObservable();

  private loadFromStorage(): any {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    if (!token || !userStr) return null;
    try {
      return { user: JSON.parse(userStr), token };
    } catch {
      return null;
    }
  }

  setAuth(user: any, token: string): void {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    this.authSubject.next({ user, token });
  }

  clearAuth(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this.authSubject.next(null);
  }
}
