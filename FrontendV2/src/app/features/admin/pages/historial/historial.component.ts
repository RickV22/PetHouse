import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import Swal from 'sweetalert2';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { AuditService } from '../../services/audit.service';

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
  users: any[] = [];
  auditLogs: any[] = [];
  filteredLogs: any[] = [];
  loading = false;
  showDetailModal = false;
  selectedLog: any = null;
  authError = false;

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
  hasNextPage = false;

  constructor(private auditService: AuditService) {}

  async ngOnInit(): Promise<void> {
    await this.loadUsers();
    await this.fetchAuditLogs();
  }

  async loadUsers(): Promise<void> {
    try {
      const users = await this.auditService.getUsers();
      this.users = Array.isArray(users) ? users : [];
    } catch {
      this.users = [];
    }
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

      const dateFilters = this.buildDateFilterParams();
      if (dateFilters.start_date) params.start_date = dateFilters.start_date;
      if (dateFilters.end_date) params.end_date = dateFilters.end_date;

      const logs = await this.auditService.getAuditLogs(params);
      const normalizedLogs = Array.isArray(logs) ? logs : [];
      this.auditLogs = this.decorateLogsWithUserName(normalizedLogs);
      this.hasNextPage = normalizedLogs.length === this.pageSize;
      this.filteredLogs = [...this.auditLogs];
      this.applySearch();
    } catch (error: any) {
      this.auditLogs = [];
      this.filteredLogs = [];
      this.hasNextPage = false;
      this.authError = error?.status === 401 || error?.status === 403;
    } finally {
      this.loading = false;
    }
  }

  decorateLogsWithUserName(logs: any[]): any[] {
    const userMap: Record<number, string> = {};
    this.users.forEach((u: any) => {
      userMap[u.id] = `${u.name} ${u.last_name || ''}`.trim();
    });

    return logs.map((l) => ({
      ...l,
      user_name: l.user_id ? userMap[l.user_id] || `Usuario #${l.user_id}` : 'Sistema',
    }));
  }

  private formatDateForQuery(dateValue: string, endOfDay = false): string | null {
    if (!dateValue) return null;

    const [year, month, day] = dateValue.split('-').map(Number);
    if (!year || !month || !day) return null;

    const date = new Date(
      Date.UTC(
        year,
        month - 1,
        day,
        endOfDay ? 23 : 0,
        endOfDay ? 59 : 0,
        endOfDay ? 59 : 0,
        endOfDay ? 999 : 0,
      ),
    );

    return date.toISOString();
  }

  private buildDateFilterParams(): { start_date?: string; end_date?: string } {
    const params: { start_date?: string; end_date?: string } = {};
    const startDate = this.formatDateForQuery(this.startDate);
    const endDate = this.formatDateForQuery(this.endDate, true);

    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    return params;
  }

  applySearch(): void {
    const term = this.searchTerm.trim().toLowerCase();
    if (!term) {
      this.filteredLogs = this.auditLogs;
      return;
    }
    this.filteredLogs = this.auditLogs.filter((log) => {
      const details = typeof log.details === 'string' ? log.details : '';
      const userName = (log.user_name || '').toLowerCase();
      const resourceId = `${log.resource_id ?? ''}`;
      const status = (log.status || '').toLowerCase();
      const action = (log.action || '').toLowerCase();
      const resource = (log.resource || '').toLowerCase();

      return (
        action.includes(term) ||
        resource.includes(term) ||
        details.toLowerCase().includes(term) ||
        userName.includes(term) ||
        resourceId.includes(term) ||
        status.includes(term)
      );
    });
  }

  async onFiltersSubmit(): Promise<void> {
    this.currentPage = 1;
    await this.fetchAuditLogs();
  }

  async changePageSize(): Promise<void> {
    this.currentPage = 1;
    await this.fetchAuditLogs();
  }

  async goToPreviousPage(): Promise<void> {
    if (this.currentPage <= 1 || this.loading) return;
    this.currentPage -= 1;
    await this.fetchAuditLogs();
  }

  async goToNextPage(): Promise<void> {
    if (!this.hasNextPage || this.loading) return;
    this.currentPage += 1;
    await this.fetchAuditLogs();
  }

  async exportToCSV(): Promise<void> {
    try {
      const params: any = {};
      if (this.filterAction) params.action = this.filterAction;
      if (this.filterResource) params.resource = this.filterResource;
      if (this.filterUser) params.user_id = this.filterUser;

      const dateFilters = this.buildDateFilterParams();
      if (dateFilters.start_date) params.start_date = dateFilters.start_date;
      if (dateFilters.end_date) params.end_date = dateFilters.end_date;

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
    const payload = log.changes || log.details;
    if (!payload) return 'Sin detalles adicionales.';
    if (typeof payload === 'string') return payload;
    return JSON.stringify(payload, null, 2);
  }
}
