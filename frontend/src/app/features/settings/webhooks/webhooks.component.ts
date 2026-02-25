import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { WebhookEndpoint } from '../../../core/models/webhook.model';

@Component({
  selector: 'app-webhooks',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatSlideToggleModule, MatChipsModule,
    MatDialogModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>Webhooks</h1>
        <button mat-raised-button color="primary" (click)="showForm.set(!showForm())">
          <mat-icon>{{ showForm() ? 'close' : 'add' }}</mat-icon>
          {{ showForm() ? 'Cancel' : 'Add Webhook' }}
        </button>
      </div>

      @if (showForm()) {
        <mat-card class="form-card">
          <mat-card-content>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>URL</mat-label>
              <input matInput [(ngModel)]="newUrl" placeholder="https://example.com/webhook">
            </mat-form-field>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Description</mat-label>
              <input matInput [(ngModel)]="newDescription">
            </mat-form-field>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Events (comma-separated)</mat-label>
              <input matInput [(ngModel)]="newEvents" placeholder="job.completed, job.failed">
            </mat-form-field>
            <button mat-raised-button color="primary" (click)="createWebhook()">Create</button>
          </mat-card-content>
        </mat-card>
      }

      @if (loading()) {
        <div class="loading"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        <div class="webhook-list">
          @for (wh of webhooks(); track wh.id) {
            <mat-card class="webhook-card">
              <mat-card-content>
                <div class="webhook-header">
                  <div>
                    <div class="webhook-url">{{ wh.url }}</div>
                    <div class="webhook-desc">{{ wh.description || 'No description' }}</div>
                  </div>
                  <mat-slide-toggle [checked]="wh.is_active"
                    (change)="toggleActive(wh)">
                  </mat-slide-toggle>
                </div>
                <div class="webhook-meta">
                  <div class="events">
                    @for (ev of wh.events; track ev) {
                      <span class="event-chip">{{ ev }}</span>
                    }
                  </div>
                  @if (wh.failure_count > 0) {
                    <span class="failure-count">{{ wh.failure_count }} failures</span>
                  }
                </div>
                <div class="webhook-actions">
                  <button mat-stroked-button (click)="testWebhook(wh.id)">
                    <mat-icon>send</mat-icon> Test
                  </button>
                  <button mat-icon-button color="warn" (click)="deleteWebhook(wh.id)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              </mat-card-content>
            </mat-card>
          } @empty {
            <div class="empty-state">
              <mat-icon>webhook</mat-icon>
              <p>No webhooks configured. Add one to receive event notifications.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .page-container { padding: 24px; }
    .page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
    .page-header h1 { margin: 0; font-size: 24px; font-weight: 600; }
    .loading { display: flex; justify-content: center; padding: 48px; }
    .form-card { margin-bottom: 24px; border-radius: 12px; }
    .full-width { width: 100%; }
    .webhook-list { display: flex; flex-direction: column; gap: 12px; }
    .webhook-card { border-radius: 12px; }
    .webhook-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
    .webhook-url { font-weight: 600; font-size: 14px; word-break: break-all; }
    .webhook-desc { color: #666; font-size: 13px; margin-top: 4px; }
    .webhook-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
    .events { display: flex; gap: 6px; flex-wrap: wrap; }
    .event-chip { background: #e3f2fd; color: #1565c0; padding: 2px 10px; border-radius: 12px; font-size: 12px; }
    .failure-count { color: #c62828; font-size: 12px; font-weight: 500; }
    .webhook-actions { display: flex; gap: 8px; justify-content: flex-end; }
    .empty-state { text-align: center; padding: 48px; color: #999; }
    .empty-state mat-icon { font-size: 48px; width: 48px; height: 48px; margin-bottom: 12px; }
  `],
})
export class WebhooksComponent implements OnInit {
  private api = inject(ApiService);
  private notification = inject(NotificationService);

  webhooks = signal<WebhookEndpoint[]>([]);
  loading = signal(true);
  showForm = signal(false);
  newUrl = '';
  newDescription = '';
  newEvents = 'job.completed, job.failed';

  ngOnInit(): void {
    this.loadWebhooks();
  }

  loadWebhooks(): void {
    this.api.getWebhooks().subscribe({
      next: (data) => { this.webhooks.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  createWebhook(): void {
    const events = this.newEvents.split(',').map((e) => e.trim()).filter(Boolean);
    this.api.createWebhook({ url: this.newUrl, events, description: this.newDescription }).subscribe({
      next: () => {
        this.notification.success('Webhook created');
        this.showForm.set(false);
        this.newUrl = '';
        this.newDescription = '';
        this.loadWebhooks();
      },
      error: () => this.notification.error('Failed to create webhook'),
    });
  }

  toggleActive(wh: WebhookEndpoint): void {
    this.api.updateWebhook(wh.id, { is_active: !wh.is_active }).subscribe({
      next: () => this.loadWebhooks(),
    });
  }

  testWebhook(id: string): void {
    this.api.testWebhook(id).subscribe({
      next: () => this.notification.success('Test webhook queued'),
    });
  }

  deleteWebhook(id: string): void {
    this.api.deleteWebhook(id).subscribe({
      next: () => { this.notification.success('Webhook deleted'); this.loadWebhooks(); },
    });
  }
}
