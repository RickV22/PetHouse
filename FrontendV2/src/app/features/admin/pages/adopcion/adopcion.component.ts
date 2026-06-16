import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Grid, h } from 'gridjs';
import Swal from 'sweetalert2';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { AdoptionService } from '../../../../core/services/adoption.service';

@Component({
  selector: 'app-admin-adopcion',
  standalone: true,
  imports: [CommonModule, FormsModule, AdminNavbarComponent],
  templateUrl: './adopcion.component.html',
  styleUrls: ['./adopcion.component.css'],
})
export class AdminAdopcionComponent implements OnInit, OnDestroy {
  requests: any[] = [];
  sortOrder = 'recent';
  activeFilter = 'Todos';
  filters = ['Todos', 'Pendiente', 'Aprobado', 'Rechazado'];
  private grid: any;

  private readonly STATUS_ID: Record<string, number> = {
    Pendiente: 1,
    Aprobado: 2,
    Rechazado: 3,
  };

  private readonly STATUS_LABEL: Record<string, string> = {
    PENDING: 'Pendiente',
    APPROVED: 'Aprobado',
    REJECTED: 'Rechazado',
  };

  constructor(private adoptionService: AdoptionService) {}

  async ngOnInit(): Promise<void> {
    await this.loadRequests();
  }

  ngOnDestroy(): void {
    this.grid?.destroy();
  }

  // ── Helpers ───────────────────────────────────────
  getStatusName(r: any): string {
    const raw = r.status?.name ?? 'PENDING';
    return this.STATUS_LABEL[raw] ?? raw;
  }

  isPending(r: any): boolean {
    return (r.status?.name ?? 'PENDING') === 'PENDING';
  }

  getPetName(r: any): string {
    return r.pet?.name ?? '—';
  }
  getAdoptanteName(r: any): string {
    return `${r.adoptante?.name ?? ''} ${r.adoptante?.last_name ?? ''}`.trim() || '—';
  }
  getAdoptanteEmail(r: any): string {
    return r.adoptante?.email ?? '—';
  }

  get totalCount(): number {
    return this.requests.length;
  }
  get pendingCount(): number {
    return this.requests.filter((r) => this.isPending(r)).length;
  }
  get approvedCount(): number {
    return this.requests.filter((r) => r.status?.name === 'APPROVED').length;
  }
  get rejectedCount(): number {
    return this.requests.filter((r) => r.status?.name === 'REJECTED').length;
  }

  getFilteredRequests(): any[] {
    if (this.activeFilter === 'Todos') return this.requests;
    const reverseMap: Record<string, string> = {
      Pendiente: 'PENDING',
      Aprobado: 'APPROVED',
      Rechazado: 'REJECTED',
    };
    return this.requests.filter((r) => r.status?.name === reverseMap[this.activeFilter]);
  }

  // ── Load & Grid ───────────────────────────────────
  async loadRequests(): Promise<void> {
    try {
      this.requests = await this.adoptionService.getAdoptions();
      setTimeout(() => this.renderGrid(), 0);
    } catch (error) {
      console.error('Error cargando solicitudes:', error);
    }
  }

  renderGrid(): void {
    this.grid?.destroy();
    const filtered = this.getFilteredRequests();

    const statusBadge = (status: string) => {
      const map: Record<string, string> = {
        Pendiente: 'warning',
        Aprobado: 'success',
        Rechazado: 'danger',
      };
      return h('span', { className: `badge bg-${map[status] ?? 'secondary'}` }, status);
    };

    const boolBadge = (val: boolean) =>
      h(
        'span',
        { className: `badge bg-${val ? 'primary' : 'light text-dark'}` },
        val ? 'Sí' : 'No',
      );

    this.grid = new Grid({
      columns: [
        { name: 'Mascota', sort: true },
        { name: 'Adoptante', sort: true },
        { name: 'Correo', sort: true },
        { name: 'Tracker', sort: false, formatter: (val: boolean) => boolBadge(val) },
        { name: 'Fecha Solicitud', sort: true },
        { name: 'Estado', formatter: (val: string) => statusBadge(val) },
        {
          name: 'Acciones',
          formatter: (_: any, row: any) => {
            const request = row.cells[6]?.data;
            if (!request) return '';
            const pending = this.isPending(request);

            const buttons: any[] = [
              h(
                'button',
                {
                  className: `btn btn-sm btn-success${!pending ? ' disabled' : ''}`,
                  onClick: () => pending && this.handleApprove(request),
                },
                'Aprobar',
              ),
              h(
                'button',
                {
                  className: `btn btn-sm btn-danger${!pending ? ' disabled' : ''}`,
                  onClick: () => pending && this.handleReject(request),
                },
                'Rechazar',
              ),
            ];

            if (request.cedula_url || request.recibo_url) {
              buttons.push(
                h(
                  'button',
                  {
                    className: 'btn btn-sm btn-outline-secondary',
                    onClick: () => this.showDocs(request),
                  },
                  'Docs',
                ),
              );
            }

            return h('div', { className: 'd-flex gap-1' }, buttons);
          },
        },
      ],
      data: filtered
        .sort((a, b) =>
          this.sortOrder === 'recent'
            ? new Date(b.fecha_solicitud).getTime() - new Date(a.fecha_solicitud).getTime()
            : (a.pet?.name || '').localeCompare(b.pet?.name || ''),
        )
        .map((r) => [
          this.getPetName(r),
          this.getAdoptanteName(r),
          this.getAdoptanteEmail(r),
          r.quiere_tracker ?? false,
          r.fecha_solicitud ? new Date(r.fecha_solicitud).toLocaleDateString('es-CO') : '—',
          this.getStatusName(r),
          r,
        ]),
      search: true,
      sort: true,
      pagination: { limit: 5 },
    });

    this.grid.render(document.getElementById('adoption-table-wrapper'));
  }

  setFilter(f: string): void {
    this.activeFilter = f;
    this.renderGrid();
  }

  // ── Actions ───────────────────────────────────────
  async showDocs(request: any): Promise<void> {
    const openFile = (dataUrl: string) => {
      if (!dataUrl) return;
      try {
        const parts = dataUrl.split(',');
        const mime = parts[0].match(/:(.*?);/)![1];
        const bin = atob(parts[1]);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        const blob = new Blob([arr], { type: mime });
        window.open(URL.createObjectURL(blob), '_blank');
      } catch {
        window.open(dataUrl, '_blank');
      }
    };

    (window as any).openAdoptionDoc = openFile;

    const cedulaBtn = request.cedula_url
      ? `<button onclick="window.openAdoptionDoc('${request.cedula_url}')" class="btn btn-primary w-100 mb-2">Ver Cédula</button>`
      : '<p class="text-muted">Sin cédula adjunta</p>';

    const reciboBtn = request.recibo_url
      ? `<button onclick="window.openAdoptionDoc('${request.recibo_url}')" class="btn btn-outline-primary w-100">Ver Recibo</button>`
      : '<p class="text-muted">Sin recibo adjunto</p>';

    await Swal.fire({
      title: 'Documentos adjuntos',
      html: `<div class="p-3">${cedulaBtn}${reciboBtn}</div>`,
      icon: 'info',
      confirmButtonText: 'Cerrar',
    });
  }

  async handleApprove(request: any): Promise<void> {
    const result = await Swal.fire({
      title: '¿Aprobar solicitud?',
      html: `¿Confirmas la adopción de <b>${this.getPetName(request)}</b> por parte de <b>${this.getAdoptanteName(request)}</b>?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#198754',
      confirmButtonText: 'Sí, aprobar',
      cancelButtonText: 'Cancelar',
    });

    if (!result.isConfirmed) return;

    try {
      await this.adoptionService.changeAdoptionStatus(request.id, this.STATUS_ID['Aprobado']);
      await Swal.fire({ title: '¡Aprobada!', text: 'La solicitud fue aprobada.', icon: 'success' });
      await this.loadRequests();
    } catch {
      Swal.fire({ title: 'Error', text: 'No se pudo aprobar la solicitud.', icon: 'error' });
    }
  }

  async handleReject(request: any): Promise<void> {
    const result = await Swal.fire({
      title: '¿Rechazar solicitud?',
      html: `¿Seguro que deseas rechazar la solicitud de <b>${this.getAdoptanteName(request)}</b>?`,
      icon: 'warning',
      input: 'textarea',
      inputPlaceholder: 'Motivo del rechazo (opcional)...',
      showCancelButton: true,
      confirmButtonColor: '#dc3545',
      confirmButtonText: 'Sí, rechazar',
      cancelButtonText: 'Cancelar',
    });

    if (!result.isConfirmed) return;

    try {
      await this.adoptionService.changeAdoptionStatus(request.id, this.STATUS_ID['Rechazado']);
      await Swal.fire({ title: 'Rechazada', text: 'La solicitud fue rechazada.', icon: 'info' });
      await this.loadRequests();
    } catch {
      Swal.fire({ title: 'Error', text: 'No se pudo rechazar la solicitud.', icon: 'error' });
    }
  }
}
