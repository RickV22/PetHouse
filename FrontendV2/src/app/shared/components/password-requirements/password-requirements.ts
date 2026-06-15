import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

interface Requirements {
  minLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
}

@Component({
  selector: 'app-password-requirements',
  standalone: true, // 👈
  imports: [CommonModule, RouterModule],
  templateUrl: './password-requirements.html',
  styleUrls: ['./password-requirements.css'],
})
export class PasswordRequirementsComponent {
  @Input() password = '';

  get requirements(): Requirements {
    return {
      minLength: this.password.length >= 8,
      hasUppercase: /[A-Z]/.test(this.password),
      hasLowercase: /[a-z]/.test(this.password),
      hasNumber: /\d/.test(this.password),
      hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(this.password),
    };
  }

  get allRequirementsMet(): boolean {
    return Object.values(this.requirements).every(Boolean);
  }

  // Lista para el *ngFor — evita repetir el template 5 veces
  get requirementList(): { met: boolean; text: string }[] {
    const r = this.requirements;
    return [
      { met: r.minLength, text: 'Mínimo 8 caracteres' },
      { met: r.hasUppercase, text: 'Al menos una letra mayúscula' },
      { met: r.hasLowercase, text: 'Al menos una letra minúscula' },
      { met: r.hasNumber, text: 'Al menos un número' },
      { met: r.hasSpecial, text: 'Al menos un carácter especial (!@#$%^&* etc)' },
    ];
  }
}
