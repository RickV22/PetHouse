import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { AskRequest, AskResponse, HistoryItem } from '../pages/ai-assistant/ai.models';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AiAssistantService {
  // El router del backend tiene prefijo /api/v1/ai (ver ai_router.py)
  // environment.apiUrl apunta al servidor de producción; aquí usamos la URL completa local
  private apiUrl = `${environment.apiUrl}/api/v1/ai`;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  async ask(question: string): Promise<AskResponse> {
    const body: AskRequest = { question };
    return firstValueFrom(
      this.http.post<AskResponse>(`${this.apiUrl}/ask`, body, {
        headers: this.getHeaders(),
      }),
    );
  }

  async getHistory(): Promise<HistoryItem[]> {
    const response: any = await firstValueFrom(
      this.http.get(`${this.apiUrl}/history`, {
        headers: this.getHeaders(),
      }),
    );
    // El backend devuelve { items: [...], count: N } — extraemos el array
    return Array.isArray(response) ? response : (response?.items ?? []);
  }
}
