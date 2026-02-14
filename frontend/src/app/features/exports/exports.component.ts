import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatMenuModule } from '@angular/material/menu';
import { ApiService } from '../../core/services/api.service';
import { NotificationService } from '../../core/services/notification.service';
import { ExportJob } from '../../core/models/export.model';

@Component({
  selector: 'app-exports',
  standalone: true,
  imports: [
    CommonModule, MatCardModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatProgressSpinnerModule, MatMenuModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>Exports</h1>
        <button mat-raised-button color="primary" [matMenuTriggerFor]="exportMenu">
          <mat-icon>add</mat-icon> New Export
        </button>
        <mat-menu #exportMenu="matMenu">
          <button mat-menu-item (click)="createExport('analysis_csv')">
            <mat-icon>analytics</mat-icon> Analysis Results (CSV)
          </button>
          <button mat-menu-item (click)="createExport('products_csv')">
            <mat-icon>inventory_2</mat-icon> Products (CSV)
          </button>
        </mat-menu>
      </div>

      @if (loading()) {
        <div class="loading"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        <div class="exports-list">
          @for (exp of exports(); track exp.id) {
            <mat-card class="export-card">
              <mat-card-content>
                <div class="export-info">
                  <div class="export-type">{{ exp.export_type }}</div>
                  <span class="status-badge" [class]="'status-' + exp.status">{{ exp.status }}</span>
                </div>
                <div class="export-meta">
                  @if (exp.row_count) { <span>{{ exp.row_count }} rows</span> }
                  @if (exp.file_size_bytes) { <span>{{ (exp.file_size_bytes / 1024) | number:'1.0-0' }} KB</span> }
                  <span>{{ exp.created_at | date:'short' }}</span>
                </div>
                <div class="export-actions">
                  @if (exp.status === 'completed') {
                    <button mat-stroked-button color="primary" (click)="downloadExport(exp.id)">
                      <mat-icon>download</mat-icon> Download
                    </button>
                  }
                  <button mat-icon-button color="warn" (click)="deleteExport(exp.id)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              </mat-card-content>
            </mat-card>
          } @empty {
            <div class="empty-state">
              <mat-icon>download</mat-icon>
              <p>No exports yet. Create one to get started.</p>
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
    .exports-list { display: flex; flex-direction: column; gap: 12px; }
    .export-card { border-radius: 12px; }
    .export-info { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
    .export-type { font-weight: 600; font-size: 15px; }
    .export-meta { display: flex; gap: 16px; color: #666; font-size: 13px; margin-bottom: 12px; }
    .export-actions { display: flex; gap: 8px; justify-content: flex-end; }
    .status-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
    .status-completed { background: #e8f5e9; color: #2e7d32; }
    .status-pending, .status-processing { background: #fff3e0; color: #ef6c00; }
    .status-failed { background: #fce4ec; color: #c62828; }
    .empty-state { text-align: center; padding: 48px; color: #999; }
    .empty-state mat-icon { font-size: 48px; width: 48px; height: 48px; margin-bottom: 12px; }
  `],
})
export class ExportsComponent implements OnInit {
  private api = inject(ApiService);
  private notification = inject(NotificationService);

  exports = signal<ExportJob[]>([]);
  loading = signal(true);

  ngOnInit(): void {
    this.loadExports();
  }

  loadExports(): void {
    this.api.getExports().subscribe({
      next: (data) => { this.exports.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  createExport(type: string): void {
    this.api.createExport({ export_type: type, filters: {} }).subscribe({
      next: () => { this.notification.success('Export started'); this.loadExports(); },
      error: () => this.notification.error('Failed to start export'),
    });
  }

  downloadExport(id: string): void {
    this.api.getExport(id).subscribe({
      next: (exp) => {
        if (exp.download_url) {
          window.open(exp.download_url, '_blank');
        }
      },
    });
  }

  deleteExport(id: string): void {
    this.api.deleteExport(id).subscribe({
      next: () => { this.notification.success('Export deleted'); this.loadExports(); },
    });
  }
}
