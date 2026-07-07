import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface AvatarGuiaState {
  message: string;
  durationMs: number;
}

@Injectable({ providedIn: 'root' })
export class AvatarGuiaService {
  private readonly stateSubject = new BehaviorSubject<AvatarGuiaState | null>(null);
  readonly state$ = this.stateSubject.asObservable();

  private hideTimer: ReturnType<typeof setTimeout> | null = null;

  show(message: string, durationMs = 6000): void {
    if (this.hideTimer) {
      clearTimeout(this.hideTimer);
      this.hideTimer = null;
    }

    this.stateSubject.next({ message, durationMs });

    this.hideTimer = setTimeout(() => {
      this.hide();
    }, durationMs);
  }

  hide(): void {
    if (this.hideTimer) {
      clearTimeout(this.hideTimer);
      this.hideTimer = null;
    }

    this.stateSubject.next(null);
  }
}
