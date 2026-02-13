import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../core/services/api.service';
import { DashboardStats, CategoryDistribution } from '../../core/models/pipeline.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MatCardModule, MatIconModule,
    MatButtonModule, MatProgressSpinnerModule, MatChipsModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>Dashboard</h1>
        <button mat-raised-button color="primary" routerLink="/upload">
          <mat-icon>cloud_upload</mat-icon>
          Upload Images
        </button>
      </div>

      @if (loading()) {
        <div class="loading-container">
          <mat-spinner></mat-spinner>
        </div>
      } @else if (stats()) {
        <div class="card-grid">
          <mat-card class="stat-card">
            <mat-icon class="stat-icon" style="color: #3f51b5">inventory_2</mat-icon>
            <div class="stat-value">{{ stats()!.total_products }}</div>
            <div class="stat-label">Total Products</div>
          </mat-card>
          <mat-card class="stat-card">
            <mat-icon class="stat-icon" style="color: #00bcd4">image</mat-icon>
            <div class="stat-value">{{ stats()!.total_images }}</div>
            <div class="stat-label">Images Uploaded</div>
          </mat-card>
          <mat-card class="stat-card">
            <mat-icon class="stat-icon" style="color: #4caf50">check_circle</mat-icon>
            <div class="stat-value">{{ stats()!.completed_analyses }}</div>
            <div class="stat-label">Analyses Completed</div>
          </mat-card>
          <mat-card class="stat-card">
            <mat-icon class="stat-icon" style="color: #ff9800">warning</mat-icon>
            <div class="stat-value">{{ stats()!.total_defects }}</div>
            <div class="stat-label">Defects Detected</div>
          </mat-card>
          <mat-card class="stat-card">
            <mat-icon class="stat-icon" style="color: #9c27b0">pending</mat-icon>
            <div class="stat-value">{{ stats()!.active_jobs }}</div>
            <div class="stat-label">Active Jobs</div>
          </mat-card>
          <mat-card class="stat-card">
            <mat-icon class="stat-icon" style="color: #607d8b">speed</mat-icon>
            <div class="stat-value">{{ formatTime(stats()!.avg_processing_time_ms) }}</div>
            <div class="stat-label">Avg. Processing Time</div>
          </mat-card>
        </div>

        @if (categories().length > 0) {
          <mat-card class="section-card">
            <h2>Category Distribution</h2>
            <div class="category-list">
              @for (cat of categories(); track cat.category) {
                <div class="category-item">
                  <span class="category-name">{{ cat.category | titlecase }}</span>
                  <div class="category-bar-container">
                    <div class="category-bar"
                         [style.width.%]="(cat.count / maxCategoryCount()) * 100">
                    </div>
                  </div>
                  <span class="category-count">{{ cat.count }}</span>
                </div>
              }
            </div>
          </mat-card>
        }

        @if (recentActivity().length > 0) {
          <mat-card class="section-card">
            <h2>Recent Activity</h2>
            <div class="activity-list">
              @for (job of recentActivity(); track job.id) {
                <div class="activity-item">
                  <mat-icon class="activity-icon">
                    {{ job.status === 'completed' ? 'check_circle' : job.status === 'failed' ? 'error' : 'pending' }}
                  </mat-icon>
                  <div class="activity-details">
                    <span class="activity-type">{{ job.job_type | titlecase }} Job</span>
                    <span class="activity-meta">{{ job.total_images }} images</span>
                  </div>
                  <span class="status-badge" [ngClass]="job.status">{{ job.status }}</span>
                  <span class="activity-time">{{ job.created_at | date:'short' }}</span>
                </div>
              }
            </div>
          </mat-card>
        }
      }
    </div>
  `,
  styles: [`
    .loading-container { display: flex; justify-content: center; padding: 60px; }
    .stat-icon { font-size: 32px; width: 32px; height: 32px; margin-bottom: 8px; }
    .section-card { margin-top: 24px; padding: 24px; border-radius: 12px; }
    .section-card h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
    .category-list { display: flex; flex-direction: column; gap: 12px; }
    .category-item { display: flex; align-items: center; gap: 12px; }
    .category-name { width: 120px; font-size: 14px; font-weight: 500; text-transform: capitalize; }
    .category-bar-container { flex: 1; height: 24px; background: #e8eaf6; border-radius: 4px; overflow: hidden; }
    .category-bar { height: 100%; background: #3f51b5; border-radius: 4px; transition: width 0.5s ease; min-width: 4px; }
    .category-count { width: 40px; text-align: right; font-weight: 600; font-size: 14px; }
    .activity-list { display: flex; flex-direction: column; gap: 12px; }
    .activity-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: #f9f9f9; border-radius: 8px; }
    .activity-icon { color: #666; }
    .activity-details { flex: 1; display: flex; flex-direction: column; }
    .activity-type { font-weight: 500; font-size: 14px; }
    .activity-meta { font-size: 12px; color: #888; }
    .activity-time { font-size: 12px; color: #999; }
  `],
})
export class DashboardComponent implements OnInit {
  stats = signal<DashboardStats | null>(null);
  categories = signal<CategoryDistribution[]>([]);
  recentActivity = signal<any[]>([]);
  loading = signal(true);

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.api.getDashboardStats().subscribe({
      next: (stats) => {
        this.stats.set(stats);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    this.api.getCategoryDistribution().subscribe({
      next: (cats) => this.categories.set(cats),
    });

    this.api.getRecentActivity().subscribe({
      next: (activity) => this.recentActivity.set(activity),
    });
  }

  maxCategoryCount(): number {
    const cats = this.categories();
    return cats.length > 0 ? Math.max(...cats.map((c) => c.count)) : 1;
  }

  formatTime(ms: number | null): string {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }
}
