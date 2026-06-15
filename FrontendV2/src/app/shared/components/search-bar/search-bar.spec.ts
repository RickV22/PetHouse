import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PetSearchComponent } from './search-bar';

describe('PetSearchComponent', () => {
  let component: PetSearchComponent;
  let fixture: ComponentFixture<PetSearchComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PetSearchComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(PetSearchComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
