import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment.development';

@Injectable({
  providedIn: 'root'
})
export class VeterinarioChatService {

  private readonly apiUrl = `${environment.apiUrl}/veterinario/chat`;

  constructor(private readonly http: HttpClient) {}

  enviarMensaje(petId: number, mensaje: string) {
    return this.http.post(this.apiUrl, {
      pet_id: petId,
      mensaje: mensaje
    });
  }

}