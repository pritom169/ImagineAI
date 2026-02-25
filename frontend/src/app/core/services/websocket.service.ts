import { Injectable } from '@angular/core';
import { Observable, Subject, timer } from 'rxjs';
import { retry, share } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { ProcessingUpdate } from '../models/pipeline.model';

@Injectable({ providedIn: 'root' })
export class WebSocketService {
  private socket: WebSocket | null = null;

  constructor(private authService: AuthService) {}

  connect(jobId: string): Observable<ProcessingUpdate> {
    const subject = new Subject<ProcessingUpdate>();
    const token = this.authService.getToken();
    const wsUrl = `${environment.wsUrl}/processing/${jobId}?token=${token}`;

    this.disconnect();

    this.socket = new WebSocket(wsUrl);

    this.socket.onmessage = (event) => {
      try {
        const data: ProcessingUpdate = JSON.parse(event.data);
        subject.next(data);

        if (data.type === 'job_complete' || data.type === 'job_failed') {
          subject.complete();
          this.disconnect();
        }
      } catch (e) {
        console.error('WebSocket parse error:', e);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      subject.error(error);
    };

    this.socket.onclose = (event) => {
      if (!event.wasClean) {
        subject.error(new Error(`WebSocket closed: ${event.code} ${event.reason}`));
      }
    };

    return subject.asObservable().pipe(share());
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
