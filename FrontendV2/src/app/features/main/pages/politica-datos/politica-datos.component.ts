import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../../../shared/components/nav-bar/nav-bar';

@Component({
  selector: 'app-politica-datos',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './politica-datos.component.html',
  styleUrls: ['./politica-datos.component.css'],
})
export class PoliticaDatosComponent {
  currentDate = new Date();
}
