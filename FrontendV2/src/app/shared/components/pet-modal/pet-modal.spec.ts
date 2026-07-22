import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { PetModalComponent } from './pet-modal';

describe('PetModalComponent', () => {
  let component: PetModalComponent;
  let fixture: ComponentFixture<PetModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PetModalComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(PetModalComponent);
    component = fixture.componentInstance;
    component.selectedPet = { id: 1, name: 'Buddy', species: 'Dog', status: 'AVAILABLE', birth_date: '2020-01-01', image_url: 'test.jpg', gender: 'macho' };
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
