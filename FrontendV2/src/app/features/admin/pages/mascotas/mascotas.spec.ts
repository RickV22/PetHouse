import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminMascotasComponent } from './mascotas.component';

describe('AdminMascotasComponent', () => {
  let component: AdminMascotasComponent;
  let fixture: ComponentFixture<AdminMascotasComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminMascotasComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminMascotasComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
