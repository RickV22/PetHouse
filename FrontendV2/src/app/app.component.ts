import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { Subscription } from 'rxjs';

import { ChatbotComponent } from './features/chatbot/chatbot.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ChatbotComponent, NgIf],
  templateUrl: './app.component.html',
  styleUrls: ['./app.css'],
})
export class AppComponent implements OnInit, OnDestroy {
  protected readonly title = signal('PetHouse');
  showGlobalChatbot = true;

  private routerSub!: Subscription;

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.updateGlobalChatbotVisibility(this.router.url);

    this.routerSub = this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.updateGlobalChatbotVisibility(event.urlAfterRedirects);
      }
    });
  }

  ngOnDestroy(): void {
    this.routerSub.unsubscribe();
  }

  private updateGlobalChatbotVisibility(url: string): void {
    this.showGlobalChatbot = !url.startsWith('/veterinario');
  }
}
