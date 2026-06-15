import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-powerbi-report',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './power-bi.html', // 👈
  styleUrls: ['./power-bi.css'],
})
export class PowerbiReportComponent {
  @Input() title = 'Power BI Report';
  @Input() height = '400px';
  @Input() width = '100%';

  safeSrc: SafeResourceUrl = '';

  @Input() set src(url: string) {
    this.safeSrc = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  constructor(private sanitizer: DomSanitizer) {}
}
