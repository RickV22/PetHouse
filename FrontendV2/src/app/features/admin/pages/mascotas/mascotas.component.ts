import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Grid, h } from 'gridjs';
import Swal from 'sweetalert2';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { PetService } from '../../../main/services/pet.service';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

@Component({
  selector: 'app-admin-mascotas',
  standalone: true,
  imports: [CommonModule, FormsModule, AdminNavbarComponent],
  templateUrl: './mascotas.component.html',
  styleUrls: ['./mascotas.component.css'],
})
export class AdminMascotasComponent implements OnInit, OnDestroy {
  pets: any[] = [];
  sortOrder = 'recent';
  isLoading = true;
  private grid: any;

  private readonly statusMap: Record<string, { text: string; class: string }> = {
    PENDING_APPROVAL: { text: '🟠 Solicitud', class: 'badge bg-warning text-dark' },
    AVAILABLE: { text: '🟢 Publicada', class: 'badge bg-success' },
    ADOPTED: { text: '🔵 Adoptada', class: 'badge bg-info' },
    REJECTED: { text: '🔴 Rechazada', class: 'badge bg-danger' },
  };

  constructor(private petService: PetService) {}

  async ngOnInit(): Promise<void> {
    await this.loadPets();
  }

  ngOnDestroy(): void {
    this.grid?.destroy();
  }

  // async loadPets(): Promise<void> {
  //   try {
  //     this.pets = await this.petService.getAllPets();
  //     setTimeout(() => this.renderGrid(), 0);
  //   } catch (error) {
  //     console.error('Error cargando mascotas:', error);
  //   }
  // }

  async loadPets(): Promise<void> {
    this.isLoading = true;
    try {
      this.pets = await this.petService.getAllPets();
      setTimeout(() => this.renderGrid(), 0);
    } catch (error) {
      console.error('Error cargando mascotas:', error);
    } finally {
      this.isLoading = false;
    }
  }

  renderGrid(): void {
    const container = document.getElementById('pets-table-wrapper');
    if (!container) return;
    this.grid?.destroy();

    const sorted = [...this.pets].sort((a, b) =>
      this.sortOrder === 'recent'
        ? new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        : a.name.localeCompare(b.name),
    );

    this.grid = new Grid({
      columns: [
        'Nombre',
        {
          name: 'Publicado por',
          formatter: (cell: string) => h('span', { className: 'fw-bold text-primary' }, cell),
        },
        'Especie',
        'Raza',
        {
          name: 'Estado',
          formatter: (cell: string) => {
            const info = this.statusMap[cell] ?? { text: cell, class: 'badge bg-secondary' };
            return h('span', { className: `${info.class} p-2 rounded-pill shadow-sm` }, info.text);
          },
        },
        { name: 'Fecha Registro', sort: true },
        {
          name: 'Acciones',
          formatter: (_: any, row: any) => {
            const pet = row.cells[6]?.data;
            if (!pet) return '';

            const buttons = [];

            if (pet.status === 'PENDING_APPROVAL') {
              buttons.push(
                h(
                  'button',
                  {
                    className: 'btn btn-sm btn-primary me-1 shadow-sm',
                    onClick: () => this.viewPet(pet),
                  },
                  '👁️ Ver',
                ),
              );
              buttons.push(
                h(
                  'button',
                  {
                    className: 'btn btn-sm btn-success me-1 shadow-sm',
                    onClick: () => this.approvePet(pet),
                  },
                  'Aprobar',
                ),
              );
              buttons.push(
                h(
                  'button',
                  {
                    className: 'btn btn-sm btn-outline-danger me-1 shadow-sm',
                    onClick: () => this.rejectPet(pet),
                  },
                  'Rechazar',
                ),
              );
            }

            buttons.push(
              h(
                'button',
                {
                  className: 'btn btn-sm btn-light border me-1 shadow-sm',
                  onClick: () => this.editPetStatus(pet),
                },
                '⚙️',
              ),
            );

            buttons.push(
              h(
                'button',
                {
                  className: 'btn btn-sm btn-outline-danger shadow-sm',
                  onClick: () => this.removePet(pet.id),
                },
                '🗑️',
              ),
            );

            return h('div', { className: 'd-flex' }, buttons);
          },
        },
      ],
      data: sorted.map((p) => [
        p.name,
        p.publisher_name || 'Desconocido',
        p.species,
        p.race,
        p.status,
        p.created_at ? new Date(p.created_at).toLocaleDateString('es-CO') : '—',
        p,
      ]),
      search: true,
      sort: true,
      pagination: { limit: 10 },
      language: {
        search: { placeholder: '🔍 Buscar mascota o usuario...' },
        pagination: { previous: 'Anterior', next: 'Siguiente' },
      },
    });

    this.grid.render(container);
  }

  async viewPet(pet: any): Promise<void> {
    let age = 'No especificada';
    if (pet.birth_date) {
      const birth = new Date(pet.birth_date);
      const now = new Date();
      // Comparar solo fechas (sin hora) para evitar problemas de zona horaria
      const birthUTC = Date.UTC(birth.getFullYear(), birth.getMonth(), birth.getDate());
      const nowUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
      const totalDays = Math.floor((nowUTC - birthUTC) / (1000 * 60 * 60 * 24));
      const years = Math.floor(totalDays / 365);
      const months = Math.floor((totalDays % 365) / 30);
      const days = totalDays % 30;

      if (years > 0) {
        age =
          months > 0
            ? `${years} año${years > 1 ? 's' : ''} y ${months} mes${months > 1 ? 'es' : ''}`
            : `${years} año${years > 1 ? 's' : ''}`;
      } else if (months > 0) {
        age =
          days > 0
            ? `${months} mes${months > 1 ? 'es' : ''} y ${days} día${days > 1 ? 's' : ''}`
            : `${months} mes${months > 1 ? 'es' : ''}`;
      } else {
        age = totalDays > 0 ? `${totalDays} día${totalDays !== 1 ? 's' : ''}` : 'Recién nacido';
      }
    }

    const genderLabel: Record<string, string> = {
      macho: '♂️ Macho',
      hembra: '♀️ Hembra',
    };

    const imageHtml = pet.image_url
      ? `<img src="${pet.image_url}" alt="${pet.name}"
            style="width:100%;max-height:260px;object-fit:cover;border-radius:12px;margin-bottom:12px;"
            onerror="this.style.display='none'">`
      : `<div class="text-muted mb-3" style="font-size:3rem;">🐾</div>`;

    const modalidadBadge =
      pet.modalidad === 'hogar'
        ? `<span class="badge bg-warning text-dark">🏠 Se queda en hogar del publicador</span>`
        : `<span class="badge bg-primary">🏡 Se entrega en sede PetHouse</span>`;

    const telefonoRow = '';

    const isSede = pet.modalidad !== 'hogar';

    const { value: action } = await Swal.fire({
      title: `${pet.name}`,
      html: `
        ${imageHtml}
        <div class="mb-2">${modalidadBadge}</div>
        <table class="table table-sm text-start" style="font-size:.9rem;">
          <tbody>
            <tr><th>Especie</th><td>${pet.species ?? '—'}</td></tr>
            <tr><th>Raza</th><td>${pet.race ?? '—'}</td></tr>
            <tr><th>Género</th><td>${genderLabel[pet.gender] ?? pet.gender ?? '—'}</td></tr>
            <tr><th>Edad</th><td>${age}</td></tr>
            <tr><th>Publicado por</th><td>${pet.publisher_name ?? '—'}</td></tr>
            <tr><th>Fecha publicación</th><td>${pet.created_at ? new Date(pet.created_at).toLocaleDateString('es-CO') : '—'}</td></tr>
            ${telefonoRow}
          </tbody>
        </table>
        <div class="text-start p-2 bg-light rounded" style="font-size:.88rem;">
          <strong>Descripción:</strong><br>
          ${pet.description ?? '<em class="text-muted">Sin descripción</em>'}
        </div>
        ${isSede ? '<div class="mt-2 p-2 bg-warning bg-opacity-10 border border-warning rounded text-start" style="font-size:.82rem;"><i class="bi bi-envelope-fill me-1 text-warning"></i><strong>Sede:</strong> Envía primero las instrucciones al publicador. Una vez la mascota llegue a la sede, aprueba la publicación.</div>' : ''}
      `,
      showDenyButton: true,
      showCancelButton: true,
      confirmButtonText: '✅ Aprobar',
      denyButtonText: isSede ? '📧 Enviar instrucciones' : '❌ Rechazar',
      cancelButtonText: isSede ? '❌ Rechazar' : 'Cerrar',
      confirmButtonColor: '#198754',
      denyButtonColor: isSede ? '#f0a500' : '#dc3545',
      cancelButtonColor: isSede ? '#dc3545' : '#6c757d',
      width: '520px',
    });

    if (action === true) {
      await this.approvePet(pet);
    } else if (action === false) {
      if (isSede) {
        await this.sendSedeInstructions(pet);
      } else {
        await this.rejectPet(pet);
      }
    } else if (action === undefined && isSede) {
      // cancelButtonText → Rechazar (solo para sede)
      const btn = document.querySelector('.swal2-cancel') as HTMLElement;
      if (btn?.innerText?.includes('Rechazar')) {
        await this.rejectPet(pet);
      }
    }
  }

  async sendSedeInstructions(pet: any): Promise<void> {
    try {
      await this.petService.sendSedeInstructions(pet.id);
      Swal.fire({
        title: '📧 Instrucciones enviadas',
        text: `Se le notificó a ${pet.publisher_name} para que lleve a ${pet.name} a la sede. Una vez recibida, aprueba la publicación.`,
        icon: 'success',
        confirmButtonColor: '#f0a500',
      });
    } catch (e: any) {
      Swal.fire('Error', e?.error?.detail || 'No se pudo enviar el correo.', 'error');
    }
  }

  async approvePet(pet: any): Promise<void> {
    const result = await Swal.fire({
      title: '¿Aprobar publicación?',
      text: `La mascota "${pet.name}" será visible en el catálogo público.`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Sí, publicar',
      confirmButtonColor: '#4361ee',
    });

    if (result.isConfirmed) {
      try {
        await this.petService.updatePet(pet.id, { status: 'AVAILABLE' });
        Swal.fire('¡Publicada!', 'La mascota ahora es visible.', 'success');
        await this.loadPets();
      } catch (e: any) {
        Swal.fire('Error', e.message, 'error');
      }
    }
  }

  async rejectPet(pet: any): Promise<void> {
    const result = await Swal.fire({
      title: '¿Rechazar solicitud?',
      text: 'Se le notificará al usuario que la solicitud fue rechazada.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, rechazar',
      confirmButtonColor: '#ff6b6b',
    });

    if (result.isConfirmed) {
      try {
        await this.petService.updatePet(pet.id, { status: 'REJECTED' });
        Swal.fire('Rechazada', 'La solicitud ha sido marcada como rechazada.', 'success');
        await this.loadPets();
      } catch (e: any) {
        Swal.fire('Error', e.message, 'error');
      }
    }
  }

  async removePet(id: number): Promise<void> {
    const result = await Swal.fire({
      title: '¿Eliminar permanentemente?',
      text: 'Esta acción borrará todos los datos de la mascota.',
      icon: 'error',
      showCancelButton: true,
      confirmButtonText: 'Sí, borrar',
      confirmButtonColor: '#d33',
    });

    if (!result.isConfirmed) return;

    try {
      await this.petService.deletePet(id);
      await this.loadPets();
    } catch {
      Swal.fire('Error', 'No se pudo eliminar.', 'error');
    }
  }

  async editPetStatus(pet: any): Promise<void> {
    const { value: formValues } = await Swal.fire({
      title: 'Editar Mascota',
      html: `
        <div class="text-start">
          <label class="form-label small fw-bold">Estado:</label>
          <select id="swal-status" class="form-select mb-3">
            <option value="PENDING_APPROVAL" ${pet.status === 'PENDING_APPROVAL' ? 'selected' : ''}>🟠 Solicitud Pendiente</option>
            <option value="AVAILABLE"        ${pet.status === 'AVAILABLE' ? 'selected' : ''}>🟢 Disponible / Publicada</option>
            <option value="ADOPTED"          ${pet.status === 'ADOPTED' ? 'selected' : ''}>🔵 Adoptada</option>
            <option value="REJECTED"         ${pet.status === 'REJECTED' ? 'selected' : ''}>🔴 Rechazada</option>
          </select>
          <label class="form-label small fw-bold">Nombre:</label>
          <input id="swal-name" class="form-control" value="${pet.name}" />
        </div>
      `,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: 'Guardar Cambios',
      preConfirm: () => ({
        status: (document.getElementById('swal-status') as HTMLSelectElement).value,
        name: (document.getElementById('swal-name') as HTMLInputElement).value,
      }),
    });

    if (formValues) {
      try {
        await this.petService.updatePet(pet.id, formValues);
        await this.loadPets();
        Swal.fire('¡Listo!', 'Cambios guardados correctamente.', 'success');
      } catch {
        Swal.fire('Error', 'No se pudo actualizar.', 'error');
      }
    }
  }

  generatePDF(): void {
    const published = this.pets.filter((p) => p.status === 'AVAILABLE');
    const adopted = this.pets.filter((p) => p.status === 'ADOPTED');

    const doc = new jsPDF({ orientation: 'landscape' });
    const primaryColor: [number, number, number] = [67, 97, 238];
    const successColor: [number, number, number] = [25, 135, 84];
    const infoColor: [number, number, number] = [13, 110, 253];
    const lightGray: [number, number, number] = [248, 249, 250];
    const today = new Date().toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    // ── Encabezado principal ──
    doc.setFillColor(...primaryColor);
    doc.rect(0, 0, 297, 28, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('PetHouse - Reporte de Mascotas', 14, 12);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.text(`Generado el ${today}`, 14, 20);
    doc.text(
      `Total registradas: ${this.pets.length}   |   Publicadas: ${published.length}   |   Adoptadas: ${adopted.length}`,
      14,
      26,
    );

    let cursorY = 36;

    const columns = [
      { header: 'Nombre', dataKey: 'name' },
      { header: 'Publicado por', dataKey: 'publisher' },
      { header: 'Especie', dataKey: 'species' },
      { header: 'Raza', dataKey: 'race' },
      { header: 'Género', dataKey: 'gender' },
      { header: 'Fecha Registro', dataKey: 'date' },
    ];

    const genderLabel: Record<string, string> = {
      macho: 'Macho',
      hembra: 'Hembra',
    };

    const buildRows = (pets: any[]) =>
      pets.map((p) => ({
        name: p.name ?? '—',
        publisher: p.publisher_name ?? 'Desconocido',
        species: p.species ?? '—',
        race: p.race ?? '—',
        gender: genderLabel[p.gender] ?? p.gender ?? '—',
        date: p.created_at ? new Date(p.created_at).toLocaleDateString('es-CO') : '—',
      }));

    // ── Sección: Publicadas ─
    doc.setTextColor(...successColor);
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.text(`Mascotas Publicadas (${published.length})`, 14, cursorY);
    cursorY += 4;

    autoTable(doc, {
      startY: cursorY,
      columns,
      body: buildRows(published),
      theme: 'grid',
      headStyles: {
        fillColor: successColor,
        textColor: 255,
        fontStyle: 'bold',
        fontSize: 9,
      },
      bodyStyles: { fontSize: 8.5, textColor: [33, 37, 41] },
      alternateRowStyles: { fillColor: lightGray },
      styles: { cellPadding: 3 },
      margin: { left: 14, right: 14 },
    });

    cursorY = (doc as any).lastAutoTable.finalY + 14;

    // Si la segunda sección no cabe en la misma página, añade una nueva
    if (cursorY > 170) {
      doc.addPage();
      cursorY = 16;
    }

    // ── Sección: Adoptadas ─────────────────────────────────────────────
    doc.setTextColor(...infoColor);
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.text(`Mascotas Adoptadas (${adopted.length})`, 14, cursorY);
    cursorY += 4;

    autoTable(doc, {
      startY: cursorY,
      columns,
      body: buildRows(adopted),
      theme: 'grid',
      headStyles: {
        fillColor: infoColor,
        textColor: 255,
        fontStyle: 'bold',
        fontSize: 9,
      },
      bodyStyles: { fontSize: 8.5, textColor: [33, 37, 41] },
      alternateRowStyles: { fillColor: lightGray },
      styles: { cellPadding: 3 },
      margin: { left: 14, right: 14 },
    });

    // ── Pie de página en todas las páginas ────────────────────────────
    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(7.5);
      doc.setTextColor(150);
      doc.setFont('helvetica', 'normal');
      doc.text(
        `PetHouse Admin  •  Página ${i} de ${pageCount}`,
        297 / 2,
        doc.internal.pageSize.getHeight() - 6,
        { align: 'center' },
      );
    }

    doc.save(`PetHouse_Mascotas_${new Date().toISOString().slice(0, 10)}.pdf`);
  }
}
