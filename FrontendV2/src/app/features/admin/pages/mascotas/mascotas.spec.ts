import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { AdminMascotasComponent } from './mascotas.component';

describe('AdminMascotasComponent', () => {
  let component: AdminMascotasComponent;
  let fixture: ComponentFixture<AdminMascotasComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminMascotasComponent, HttpClientTestingModule],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminMascotasComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
