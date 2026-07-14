import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { AdminHistorialComponent } from './historial.component';

describe('AdminHistorialComponent', () => {
  let component: AdminHistorialComponent;
  let fixture: ComponentFixture<AdminHistorialComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminHistorialComponent, HttpClientTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminHistorialComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should format selected dates for backend filters', () => {
    component.startDate = '2026-07-08';
    component.endDate = '2026-07-08';

    const params = (component as any).buildDateFilterParams();

    expect(params).toEqual({
      start_date: '2026-07-08T00:00:00.000Z',
      end_date: '2026-07-08T23:59:59.999Z',
    });
  });
});
