import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Grid, h } from 'gridjs';
import Swal from 'sweetalert2';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { PetService } from '../../../../core/services/pet.service';

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

  async loadPets(): Promise<void> {
    try {
      this.pets = await this.petService.getAllPets();
      setTimeout(() => this.renderGrid(), 0);
    } catch (error) {
      console.error('Error cargando mascotas:', error);
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
}
