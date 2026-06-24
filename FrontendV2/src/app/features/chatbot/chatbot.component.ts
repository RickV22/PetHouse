import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ChatService } from '../../core/services/chat.service';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css'],
})
export class ChatbotComponent {
  abierto = false;

  mensaje = '';

  mensajes: any[] = [];

  esperando = false;

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef,
  ) {}

  toggleChat() {
    this.abierto = !this.abierto;

    if (this.abierto && this.mensajes.length === 0) {
      this.mensajes.push({
        tipo: 'bot',
        texto:
          '¡Hola! 🐾 Soy Togo tu asistente virtual. ¿En qué puedo ayudarte hoy? Puedo orientarte sobre adopciones, cuidado de mascotas y nuestros servicios. 😊',
      });
    }
  }

  enviar() {
    if (!this.mensaje.trim() || this.esperando) {
      return;
    }

    const texto = this.mensaje;

    // Mensaje usuario
    this.mensajes.push({
      tipo: 'usuario',
      texto,
    });

    this.mensaje = '';
    this.esperando = true;

    // Mensaje temporal
    const mensajeTemporal = {
      tipo: 'bot',
      texto: '🐾 PetHouse IA está escribiendo...',
    };

    this.mensajes.push(mensajeTemporal);

    this.cdr.detectChanges();

    this.chatService.enviarMensaje(texto).subscribe({
      next: (resp: any) => {
        console.log('RESPUESTA IA:', resp);

        mensajeTemporal.texto = resp.respuesta;
        this.esperando = false;

        this.cdr.detectChanges();

        setTimeout(() => {
          const contenedor = document.querySelector('.messages');
          if (contenedor) {
            contenedor.scrollTop = contenedor.scrollHeight;
          }
        }, 50);
      },

      error: (error) => {
        console.error('Error IA:', error);

        mensajeTemporal.texto = '❌ Lo siento, ocurrió un error al procesar tu solicitud.';
        this.esperando = false;

        this.cdr.detectChanges();
      },
    });
  }
}
