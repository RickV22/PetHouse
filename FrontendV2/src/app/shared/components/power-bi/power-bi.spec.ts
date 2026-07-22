import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';

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
    const sanitizer = TestBed.inject(DomSanitizer);
    component.src = sanitizer.bypassSecurityTrustResourceUrl('about:blank');
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
