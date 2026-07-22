import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { AiAssistantService } from '../../services/ai-assistant.service';
import { HistoryItem } from './ai.models';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sql?: string | null;
  executionTime?: number | null;
  provider?: string;
  model?: string;
  timestamp: Date;
}

@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule, AdminNavbarComponent],
  templateUrl: './ai-assistant.component.html',
  styleUrls: ['./ai-assistant.component.css'],
})
export class AiAssistantComponent implements OnInit {
  messages: ChatMessage[] = [];
  question = '';
  loading = false;
  history: HistoryItem[] = [];
  showHistory = true;
  error = '';
  copiedIndex: number | null = null;

  constructor(private aiService: AiAssistantService) {}

  ngOnInit(): void {
    this.loadHistory();
    this.messages.push({
      role: 'assistant',
      content:
        '¡Hola! Soy tu asistente de PetHouse. 🐾 Puedo ayudarte a consultar información sobre usuarios, mascotas, solicitudes de adopción o generar reportes del sistema. ¿Qué te gustaría saber hoy?',
      timestamp: new Date(),
    });
  }

  async send(inputEl?: HTMLInputElement): Promise<void> {
    const q = this.question.trim();
    if (!q || this.loading) return;

    this.question = '';
    if (inputEl) {
      inputEl.value = '';
    }
    this.messages.push({ role: 'user', content: q, timestamp: new Date() });
    this.loading = true;
    this.error = '';

    try {
      const response = await this.aiService.ask(q);
      this.messages.push({
        role: 'assistant',
        content: response.answer,
        sql: response.generated_sql || null,
        executionTime: response.execution_time_ms || null,
        provider: response.provider,
        model: response.model,
        timestamp: new Date(),
      });
    } catch (err: any) {
      this.error =
        err.error?.detail || 'Ocurrió un error al procesar tu solicitud.';
    } finally {
      this.loading = false;
      this.loadHistory();
      setTimeout(() => {
        this.question = '';
        if (inputEl) {
          inputEl.value = '';
          inputEl.focus();
        }
      }, 50);
    }
  }

  async loadHistory(): Promise<void> {
    try {
      this.history = await this.aiService.getHistory();
    } catch {
      // Silently fail
    }
  }

  selectHistoryItem(item: HistoryItem): void {
    this.messages.push({
      role: 'user',
      content: item.question,
      timestamp: new Date(),
    });
    this.messages.push({
      role: 'assistant',
      content: item.answer,
      sql: item.generated_sql,
      executionTime: item.execution_time_ms,
      provider: item.provider,
      timestamp: new Date(),
    });
  }

  clearChat(): void {
    this.messages = [];
    this.error = '';
    this.messages.push({
      role: 'assistant',
      content:
        '¡Hola! Soy tu asistente de PetHouse. 🐾 Puedo ayudarte a consultar información sobre usuarios, mascotas, solicitudes de adopción o generar reportes del sistema. ¿Qué te gustaría saber hoy?',
      timestamp: new Date(),
    });
  }

  async copySql(sql: string, index: number): Promise<void> {
    try {
      await navigator.clipboard.writeText(sql);
      this.copiedIndex = index;
      setTimeout(() => (this.copiedIndex = null), 2000);
    } catch {
      // Clipboard not available
    }
  }

  exportPdf(msg: ChatMessage): void {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Reporte PetHouse - ${new Date(msg.timestamp).toLocaleDateString()}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; color: #1a1d20; }
            .header { border-bottom: 3px solid #0d6efd; padding-bottom: 12px; margin-bottom: 24px; }
            .header h1 { margin: 0; color: #0d6efd; font-size: 24px; }
            .meta { color: #6c757d; font-size: 13px; margin-top: 6px; }
            .content { white-space: pre-wrap; line-height: 1.6; font-size: 14px; background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; }
            .sql-box { background: #1e293b; color: #f8fafc; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 13px; margin-top: 20px; white-space: pre-wrap; }
            .footer { margin-top: 30px; text-align: center; color: #adb5bd; font-size: 12px; border-top: 1px solid #dee2e6; padding-top: 10px; }
            @media print {
              body { margin: 20px; }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>🐾 PetHouse - Reporte de la Base de Datos</h1>
            <div class="meta">
              Generado el ${new Date(msg.timestamp).toLocaleString()} | Asistente SQL
            </div>
          </div>
          <div class="content">${msg.content}</div>
          ${msg.sql ? `<h3 style="margin-top: 20px; font-size: 16px;">Consulta SQL ejecutada:</h3><div class="sql-box">${msg.sql}</div>` : ''}
          <div class="footer">PetHouse Admin System &copy; ${new Date().getFullYear()}</div>
          <script>
            window.onload = function() { window.print(); };
          </script>
        </body>
      </html>
    `;

    printWindow.document.write(htmlContent);
    printWindow.document.close();
  }
}
