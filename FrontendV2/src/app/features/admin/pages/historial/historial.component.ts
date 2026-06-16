import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import Swal from 'sweetalert2';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { AuditService } from '../../../../core/services/audit.service';

interface ActionBadge {
  class: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-admin-historial',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, AdminNavbarComponent],
  templateUrl: './historial.component.html',
  styleUrls: ['./historial.component.css'],
})
export class AdminHistorialComponent implements OnInit {
  auditLogs: any[] = [];
  filteredLogs: any[] = [];
  loading = false;
  showDetailModal = false;
  selectedLog: any = null;

  // Filtros
  filterAction = '';
  filterResource = '';
  filterUser = '';
  startDate = '';
  endDate = '';
  searchTerm = '';

  // Paginación
  currentPage = 1;
  pageSize = 20;
  pageSizeOptions = [20, 50, 100];

  constructor(private auditService: AuditService) {}

  async ngOnInit(): Promise<void> {
    await this.fetchAuditLogs();
  }

  async fetchAuditLogs(): Promise<void> {
    this.loading = true;
    try {
      const params: any = {
        limit: this.pageSize,
        offset: (this.currentPage - 1) * this.pageSize,
      };

      if (this.filterAction) params.action = this.filterAction;
      if (this.filterResource) params.resource = this.filterResource;
      if (this.filterUser) params.user_id = this.filterUser;
      if (this.startDate) params.start_date = new Date(this.startDate).toISOString();
      if (this.endDate) params.end_date = new Date(this.endDate).toISOString();

      this.auditLogs = await this.auditService.getAuditLogs(params);

      // Enriquecer con nombres de usuario
      try {
        const users = await this.auditService.getUsers();
        const userMap: Record<number, string> = {};
        users.forEach((u: any) => {
          userMap[u.id] = `${u.name} ${u.last_name || ''}`.trim();
        });
        this.auditLogs = this.auditLogs.map((l) => ({
          ...l,
          user_name: l.user_id ? userMap[l.user_id] || `Usuario #${l.user_id}` : 'Sistema',
        }));
      } catch {
        this.auditLogs = this.auditLogs.map((l) => ({
          ...l,
          user_name: l.user_id ? `Usuario #${l.user_id}` : 'Sistema',
        }));
      }

      this.applySearch();
    } catch (error) {
      Swal.fire({
        icon: 'error',
        title: 'Error de Carga',
        text: 'No se pudo obtener el historial. Verifica tu conexión.',
        confirmButtonColor: '#ff6b6b',
      });
    } finally {
      this.loading = false;
    }
  }

  applySearch(): void {
    const term = this.searchTerm.trim().toLowerCase();
    if (!term) {
      this.filteredLogs = this.auditLogs;
      return;
    }
    this.filteredLogs = this.auditLogs.filter(
      (log) =>
        log.action.toLowerCase().includes(term) ||
        log.resource.toLowerCase().includes(term) ||
        (log.details && log.details.toLowerCase().includes(term)),
    );
  }

  async exportToCSV(): Promise<void> {
    try {
      const params: any = {};
      if (this.filterAction) params.action = this.filterAction;
      if (this.filterResource) params.resource = this.filterResource;
      if (this.filterUser) params.user_id = this.filterUser;
      if (this.startDate) params.start_date = new Date(this.startDate).toISOString();
      if (this.endDate) params.end_date = new Date(this.endDate).toISOString();

      const data = await this.auditService.exportAuditLogsCSV(params);
      const blob = new Blob([data.content], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      a.click();
      URL.revokeObjectURL(url);

      Swal.fire({
        icon: 'success',
        title: '¡Exportado!',
        text: 'El archivo CSV se ha descargado.',
        confirmButtonColor: '#4361ee',
      });
    } catch {
      Swal.fire('Error', 'No se pudo exportar el historial.', 'error');
    }
  }

  async resetFilters(): Promise<void> {
    this.filterAction = '';
    this.filterResource = '';
    this.filterUser = '';
    this.startDate = '';
    this.endDate = '';
    this.searchTerm = '';
    this.currentPage = 1;
    await this.fetchAuditLogs();
  }

  viewDetails(log: any): void {
    this.selectedLog = log;
    this.showDetailModal = true;
  }

  closeModal(): void {
    this.showDetailModal = false;
    this.selectedLog = null;
  }

  formatDate(dateString: string): string {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  getActionBadge(action: string): ActionBadge {
    const config: Record<string, ActionBadge> = {
      create: { class: 'badge-create', label: 'Crear', icon: 'bi-plus-circle' },
      update: { class: 'badge-update', label: 'Editar', icon: 'bi-pencil' },
      delete: { class: 'badge-delete', label: 'Borrar', icon: 'bi-trash' },
      login: { class: 'badge-login', label: 'Login', icon: 'bi-box-arrow-in-right' },
      login_failed: { class: 'badge-failed', label: 'Fallo', icon: 'bi-exclamation-triangle' },
    };
    return config[action] ?? { class: 'bg-secondary', label: action, icon: 'bi-dot' };
  }

  getDetailsJson(log: any): string {
    return JSON.stringify(log.changes || log.details, null, 2);
  }
}
