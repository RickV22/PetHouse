import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PetModalComponent } from './pet-modal';

describe('PetModalComponent', () => {
  let component: PetModalComponent;
  let fixture: ComponentFixture<PetModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PetModalComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(PetModalComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
