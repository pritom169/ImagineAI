import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ABExperiment, ABVariantStats } from '../../../core/models/ab-testing.model';

@Component({
  selector: 'app-ab-testing',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatSlideToggleModule,
    MatProgressSpinnerModule, MatExpansionModule, MatProgressBarModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>A/B Testing Experiments</h1>
        <button mat-raised-button color="primary" (click)="showForm.set(!showForm())">
          <mat-icon>{{ showForm() ? 'close' : 'add' }}</mat-icon>
          {{ showForm() ? 'Cancel' : 'New Experiment' }}
        </button>
      </div>

      @if (showForm()) {
        <mat-card class="form-card">
          <mat-card-content>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Experiment Name</mat-label>
              <input matInput [(ngModel)]="newName">
            </mat-form-field>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Model Type</mat-label>
              <input matInput [(ngModel)]="newModelType" placeholder="classifier">
            </mat-form-field>
            <h3>Variants</h3>
            @for (v of newVariants; track $index) {
              <div class="variant-row">
                <mat-form-field appearance="outline">
                  <mat-label>Version</mat-label>
                  <input matInput [(ngModel)]="v.model_version">
                </mat-form-field>
                <mat-form-field appearance="outline">
                  <mat-label>Weight</mat-label>
                  <input matInput type="number" [(ngModel)]="v.weight">
                </mat-form-field>
                <mat-slide-toggle [(ngModel)]="v.is_control">Control</mat-slide-toggle>
              </div>
            }
            <button mat-stroked-button (click)="addVariant()">
              <mat-icon>add</mat-icon> Add Variant
            </button>
            <div class="form-actions">
              <button mat-raised-button color="primary" (click)="createExperiment()">Create Experiment</button>
            </div>
          </mat-card-content>
        </mat-card>
      }

      @if (loading()) {
        <div class="loading"><mat-spinner diameter="40"></mat-spinner></div>
      } @else {
        <mat-accordion>
          @for (exp of experiments(); track exp.id) {
            <mat-expansion-panel>
              <mat-expansion-panel-header>
                <mat-panel-title>
                  {{ exp.name }}
                  <span class="status-dot" [class.active]="exp.is_active"></span>
                </mat-panel-title>
                <mat-panel-description>
                  {{ exp.model_type }} | {{ exp.variants.length }} variants
                </mat-panel-description>
              </mat-expansion-panel-header>

              <div class="experiment-detail">
                <div class="variants-grid">
                  @for (variant of exp.variants; track variant.id) {
                    <mat-card class="variant-card">
                      <mat-card-content>
                        <div class="variant-header">
                          <span class="variant-version">{{ variant.model_version }}</span>
                          @if (variant.is_control) {
                            <span class="control-badge">Control</span>
                          }
                        </div>
                        <div class="variant-weight">Weight: {{ variant.weight }}%</div>
                        <mat-progress-bar mode="determinate" [value]="variant.weight"></mat-progress-bar>
                      </mat-card-content>
                    </mat-card>
                  }
                </div>

                @if (experimentResults()[exp.id]) {
                  <h3>Results</h3>
                  <div class="results-grid">
                    @for (stat of experimentResults()[exp.id]; track stat.variant_id) {
                      <mat-card class="result-card">
                        <mat-card-content>
                          <div class="result-version">{{ stat.model_version }}</div>
                          <div class="result-metric">
                            <span class="metric-label">Samples</span>
                            <span class="metric-value">{{ stat.sample_count }}</span>
                          </div>
                          <div class="result-metric">
                            <span class="metric-label">Avg Confidence</span>
                            <span class="metric-value">{{ stat.avg_confidence !== null ? (stat.avg_confidence | number:'1.4-4') : 'N/A' }}</span>
                          </div>
                          <div class="result-metric">
                            <span class="metric-label">Avg Processing</span>
                            <span class="metric-value">{{ stat.avg_processing_time_ms !== null ? (stat.avg_processing_time_ms | number:'1.0-0') + 'ms' : 'N/A' }}</span>
                          </div>
                        </mat-card-content>
                      </mat-card>
                    }
                  </div>
                }

                <div class="experiment-actions">
                  <button mat-stroked-button (click)="loadResults(exp.id)">
                    <mat-icon>analytics</mat-icon> Load Results
                  </button>
                  <mat-slide-toggle [checked]="exp.is_active" (change)="toggleExperiment(exp)">
                    {{ exp.is_active ? 'Active' : 'Inactive' }}
                  </mat-slide-toggle>
                  <button mat-icon-button color="warn" (click)="deleteExperiment(exp.id)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
              </div>
            </mat-expansion-panel>
          } @empty {
            <div class="empty-state">
              <mat-icon>science</mat-icon>
              <p>No experiments configured.</p>
            </div>
          }
        </mat-accordion>
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
    .variant-row { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }
    .form-actions { margin-top: 16px; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #ccc; display: inline-block; margin-left: 8px; }
    .status-dot.active { background: #4caf50; }
    .experiment-detail { padding: 16px 0; }
    .variants-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .variant-card { border-radius: 8px; }
    .variant-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
    .variant-version { font-weight: 600; }
    .control-badge { background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 8px; font-size: 11px; }
    .variant-weight { font-size: 13px; color: #666; margin-bottom: 8px; }
    .results-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }
    .result-card { border-radius: 8px; }
    .result-version { font-weight: 600; margin-bottom: 8px; }
    .result-metric { display: flex; justify-content: space-between; margin-bottom: 4px; }
    .metric-label { color: #666; font-size: 13px; }
    .metric-value { font-weight: 500; }
    .experiment-actions { display: flex; gap: 12px; align-items: center; padding-top: 12px; border-top: 1px solid #eee; }
    .empty-state { text-align: center; padding: 48px; color: #999; }
    .empty-state mat-icon { font-size: 48px; width: 48px; height: 48px; margin-bottom: 12px; }
  `],
})
export class ABTestingComponent implements OnInit {
  private api = inject(ApiService);
  private notification = inject(NotificationService);

  experiments = signal<ABExperiment[]>([]);
  experimentResults = signal<Record<string, ABVariantStats[]>>({});
  loading = signal(true);
  showForm = signal(false);
  newName = '';
  newModelType = 'classifier';
  newVariants = [
    { model_version: 'v1', weight: 90, is_control: true },
    { model_version: 'v2', weight: 10, is_control: false },
  ];

  ngOnInit(): void {
    this.loadExperiments();
  }

  loadExperiments(): void {
    this.api.getExperiments().subscribe({
      next: (data) => { this.experiments.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  addVariant(): void {
    this.newVariants.push({ model_version: '', weight: 0, is_control: false });
  }

  createExperiment(): void {
    this.api.createExperiment({
      name: this.newName,
      model_type: this.newModelType,
      variants: this.newVariants,
    }).subscribe({
      next: () => {
        this.notification.success('Experiment created');
        this.showForm.set(false);
        this.newName = '';
        this.loadExperiments();
      },
      error: () => this.notification.error('Failed to create experiment'),
    });
  }

  toggleExperiment(exp: ABExperiment): void {
    this.api.updateExperiment(exp.id, { is_active: !exp.is_active }).subscribe({
      next: () => this.loadExperiments(),
    });
  }

  deleteExperiment(id: string): void {
    this.api.deleteExperiment(id).subscribe({
      next: () => { this.notification.success('Experiment deleted'); this.loadExperiments(); },
    });
  }

  loadResults(experimentId: string): void {
    this.api.getExperimentResults(experimentId).subscribe({
      next: (stats) => {
        this.experimentResults.update((prev) => ({ ...prev, [experimentId]: stats }));
      },
    });
  }
}
