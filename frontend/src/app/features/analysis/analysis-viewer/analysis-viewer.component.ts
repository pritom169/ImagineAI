import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../../core/services/api.service';
import { AnalysisResult } from '../../../core/models/analysis.model';

@Component({
  selector: 'app-analysis-viewer',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MatCardModule, MatButtonModule,
    MatIconModule, MatChipsModule, MatDividerModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="page-container">
      <button mat-button (click)="goBack()"><mat-icon>arrow_back</mat-icon> Back</button>

      @if (loading()) {
        <div class="loading-container"><mat-spinner></mat-spinner></div>
      } @else if (analysis()) {
        <h1>Image Analysis</h1>

        <div class="analysis-layout">
          <!-- Left: Image with defect overlay -->
          <mat-card class="image-panel">
            <div class="image-container">
              <div class="image-placeholder">
                <mat-icon>image</mat-icon>
                <span>Product Image</span>
              </div>
              <!-- Defect bounding boxes overlay -->
              @for (defect of analysis()!.detected_defects; track defect.id) {
                @if (defect.bounding_box) {
                  <div class="defect-box"
                       [style.left.%]="defect.bounding_box.x * 100"
                       [style.top.%]="defect.bounding_box.y * 100"
                       [style.width.%]="defect.bounding_box.width * 100"
                       [style.height.%]="defect.bounding_box.height * 100"
                       [class]="'severity-border-' + defect.severity">
                    <span class="defect-label">{{ defect.defect_type }}</span>
                  </div>
                }
              }
            </div>
          </mat-card>

          <!-- Right: Results panel -->
          <div class="results-panel">
            <!-- Classification -->
            <mat-card class="result-section">
              <h3><mat-icon>category</mat-icon> Classification</h3>
              <div class="classification-main">
                <span class="main-label">{{ analysis()!.classification_label | titlecase }}</span>
                <div class="confidence-display">
                  <div class="confidence-bar">
                    <div class="confidence-fill"
                         [class.high]="(analysis()!.classification_confidence || 0) > 0.8"
                         [class.medium]="(analysis()!.classification_confidence || 0) > 0.5"
                         [class.low]="(analysis()!.classification_confidence || 0) <= 0.5"
                         [style.width.%]="(analysis()!.classification_confidence || 0) * 100">
                    </div>
                  </div>
                  <span class="confidence-pct">{{ ((analysis()!.classification_confidence || 0) * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <div class="model-info">Model: {{ analysis()!.model_version }}</div>
            </mat-card>

            <!-- Attributes -->
            <mat-card class="result-section">
              <h3><mat-icon>label</mat-icon> Attributes</h3>
              <div class="attributes-list">
                @for (attr of analysis()!.extracted_attributes; track attr.id) {
                  <div class="attribute-row">
                    <span class="attr-key">{{ attr.attribute_name | titlecase }}</span>
                    <span class="attr-val">{{ attr.attribute_value }}</span>
                    @if (attr.confidence) {
                      <span class="attr-conf">{{ (attr.confidence * 100).toFixed(0) }}%</span>
                    }
                  </div>
                } @empty {
                  <p class="no-data">No attributes extracted</p>
                }
              </div>
            </mat-card>

            <!-- Defects -->
            <mat-card class="result-section">
              <h3><mat-icon>warning</mat-icon> Defects ({{ analysis()!.detected_defects.length }})</h3>
              @for (defect of analysis()!.detected_defects; track defect.id) {
                <div class="defect-detail">
                  <div class="defect-header">
                    <span class="defect-type">{{ defect.defect_type | titlecase }}</span>
                    <span class="status-badge" [ngClass]="defect.severity">{{ defect.severity }}</span>
                  </div>
                  @if (defect.description) {
                    <p class="defect-desc">{{ defect.description }}</p>
                  }
                </div>
              } @empty {
                <p class="no-data success-text">No defects detected</p>
              }
            </mat-card>

            <!-- Description -->
            @if (analysis()!.description_text) {
              <mat-card class="result-section">
                <h3><mat-icon>auto_awesome</mat-icon> AI Generated Description</h3>
                <p class="ai-description">{{ analysis()!.description_text }}</p>
                <div class="desc-meta">
                  Generated by {{ analysis()!.description_model }}
                </div>
              </mat-card>
            }

            <div class="processing-meta">
              Processed in {{ analysis()!.processing_time_ms }}ms
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .loading-container { display: flex; justify-content: center; padding: 60px; }
    .analysis-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 20px; }
    .image-panel { padding: 0; border-radius: 12px; overflow: hidden; }
    .image-container { position: relative; min-height: 400px; background: #f0f0f0; }
    .image-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; color: #999; }
    .image-placeholder mat-icon { font-size: 64px; width: 64px; height: 64px; }
    .defect-box { position: absolute; border: 2px solid; border-radius: 4px; pointer-events: none; }
    .severity-border-low { border-color: #ff9800; }
    .severity-border-medium { border-color: #f44336; }
    .severity-border-high { border-color: #b71c1c; }
    .defect-label { position: absolute; top: -20px; left: 0; font-size: 10px; background: rgba(0,0,0,0.7); color: white; padding: 2px 6px; border-radius: 3px; }
    .results-panel { display: flex; flex-direction: column; gap: 16px; }
    .result-section { padding: 20px; border-radius: 12px; }
    .result-section h3 { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; margin-bottom: 16px; }
    .classification-main { display: flex; align-items: center; gap: 16px; }
    .main-label { font-size: 24px; font-weight: 700; text-transform: capitalize; }
    .confidence-display { flex: 1; display: flex; align-items: center; gap: 8px; }
    .confidence-pct { font-weight: 600; }
    .model-info { margin-top: 8px; font-size: 12px; color: #999; font-family: monospace; }
    .attributes-list { display: flex; flex-direction: column; gap: 8px; }
    .attribute-row { display: flex; align-items: center; padding: 8px 12px; background: #f5f5f5; border-radius: 6px; }
    .attr-key { width: 100px; font-weight: 500; color: #666; text-transform: capitalize; }
    .attr-val { flex: 1; font-weight: 500; text-transform: capitalize; }
    .attr-conf { font-size: 12px; color: #999; }
    .defect-detail { padding: 12px; background: #fff8e1; border-radius: 8px; margin-bottom: 8px; }
    .defect-header { display: flex; justify-content: space-between; align-items: center; }
    .defect-type { font-weight: 600; }
    .defect-desc { font-size: 13px; color: #666; margin-top: 4px; }
    .no-data { color: #999; font-style: italic; }
    .success-text { color: #4caf50; }
    .ai-description { line-height: 1.7; color: #444; }
    .desc-meta { margin-top: 12px; font-size: 12px; color: #999; }
    .processing-meta { text-align: right; font-size: 12px; color: #999; }
  `],
})
export class AnalysisViewerComponent implements OnInit {
  analysis = signal<AnalysisResult | null>(null);
  loading = signal(true);

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
  ) {}

  ngOnInit(): void {
    const imageId = this.route.snapshot.paramMap.get('imageId')!;
    this.api.getAnalysis(imageId).subscribe({
      next: (result) => {
        this.analysis.set(result);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  goBack(): void {
    history.back();
  }
}
