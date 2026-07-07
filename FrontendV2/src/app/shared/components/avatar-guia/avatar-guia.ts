import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { AvatarGuiaService, AvatarGuiaState } from './avatar-guia.service';

@Component({
  selector: 'app-avatar-guia',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './avatar-guia.html',
  styleUrls: ['./avatar-guia.css'],
})
export class AvatarGuiaComponent implements OnInit, OnDestroy {
  state: AvatarGuiaState | null = null;

  private stateSub!: Subscription;

  constructor(private avatarGuiaService: AvatarGuiaService) {}

  ngOnInit(): void {
    this.stateSub = this.avatarGuiaService.state$.subscribe((state) => {
      this.state = state;
    });
  }

  ngOnDestroy(): void {
    this.stateSub.unsubscribe();
  }

  close(): void {
    this.avatarGuiaService.hide();
  }
}
