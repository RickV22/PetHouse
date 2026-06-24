import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/chat';

  constructor(private http: HttpClient) {}

  enviarMensaje(mensaje: string) {
    return this.http.post(this.apiUrl, {
      mensaje,
    });
  }
}
