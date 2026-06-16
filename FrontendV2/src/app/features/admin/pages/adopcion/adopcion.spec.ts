import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminAdopcionComponent } from './adopcion.component';

describe('AdminAdopcionComponent', () => {
  let component: AdminAdopcionComponent;
  let fixture: ComponentFixture<AdminAdopcionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminAdopcionComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminAdopcionComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
