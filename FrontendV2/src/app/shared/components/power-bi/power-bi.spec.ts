import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PowerbiReportComponent } from './power-bi';

describe('PowerbiReportComponent', () => {
  let component: PowerbiReportComponent;
  let fixture: ComponentFixture<PowerbiReportComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PowerbiReportComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(PowerbiReportComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
