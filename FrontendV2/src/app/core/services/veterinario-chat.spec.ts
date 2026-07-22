import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { VeterinarioChatService } from './veterinario-chat.service';

describe('VeterinarioChat', () => {
  let service: VeterinarioChatService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    service = TestBed.inject(VeterinarioChatService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
