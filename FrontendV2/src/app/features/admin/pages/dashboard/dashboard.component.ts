import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AdminNavbarComponent } from '../../../../shared/components/admin-navbar/admin-navbar';
import { PowerbiReportComponent } from '../../../../shared/components/power-bi/power-bi';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, AdminNavbarComponent, PowerbiReportComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
})
export class AdminDashboardComponent {
  readonly reportUrl: SafeResourceUrl;
  readonly reportSrc =
    'https://app.powerbi.com/view?r=eyJrIjoiZjU0ZWNhMjEtYjIyMy00MTllLTlmZmYtOTNhZjI0ZjA4MjY0IiwidCI6IjFlOWFhYmU4LTY3ZjgtNGYxYy1hMzI5LWE3NTRlOTI0OTlhZSIsImMiOjR9';

  constructor(sanitizer: DomSanitizer) {
    this.reportUrl = sanitizer.bypassSecurityTrustResourceUrl(this.reportSrc);
  }
}
