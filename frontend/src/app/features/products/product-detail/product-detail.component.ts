import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { ApiService } from '../../../core/services/api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Product } from '../../../core/models/product.model';
import { AnalysisResult } from '../../../core/models/analysis.model';

@Component({
  selector: 'app-product-detail',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MatCardModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatTabsModule, MatProgressBarModule, MatProgressSpinnerModule,
    MatDividerModule,
  ],
  template: `
    <div class="page-container">
      @if (loading()) {
        <div class="loading-container"><mat-spinner></mat-spinner></div>
      } @else if (product()) {
        <div class="page-header">
          <div>
            <button mat-button routerLink="/products"><mat-icon>arrow_back</mat-icon> Back</button>
            <h1>{{ product()!.title || 'Untitled Product' }}</h1>
          </div>
          <span class="status-badge" [ngClass]="product()!.status">{{ product()!.status }}</span>
        </div>

        <mat-tab-group>
          <!-- Details Tab -->
          <mat-tab label="Details">
            <div class="tab-content">
              <div class="detail-grid">
                <mat-card class="detail-card">
                  <h3>Product Info</h3>
                  <div class="detail-row"><span>Category</span><strong>{{ product()!.category || 'Pending' | titlecase }}</strong></div>
                  <div class="detail-row"><span>Subcategory</span><strong>{{ product()!.subcategory || '-' }}</strong></div>
                  <div class="detail-row"><span>Images</span><strong>{{ product()!.images.length }}</strong></div>
                  <div class="detail-row"><span>Created</span><strong>{{ product()!.created_at | date:'medium' }}</strong></div>
                </mat-card>

                @if (product()!.ai_description) {
                  <mat-card class="detail-card description-card">
                    <h3><mat-icon>auto_awesome</mat-icon> AI Description</h3>
                    <p>{{ product()!.ai_description }}</p>
                    <button mat-stroked-button (click)="copyDescription()">
                      <mat-icon>content_copy</mat-icon> Copy
                    </button>
                  </mat-card>
                }
              </div>
            </div>
          </mat-tab>

          <!-- Analysis Tab -->
          <mat-tab label="Analysis Results">
            <div class="tab-content">
              @for (analysis of analyses(); track analysis.id) {
                <mat-card class="analysis-card">
                  <div class="analysis-header">
                    <span class="status-badge" [ngClass]="analysis.status">{{ analysis.status }}</span>
                    <span class="model-version">{{ analysis.model_version }}</span>
                  </div>

                  @if (analysis.status === 'completed') {
                    <div class="analysis-content">
                      <div class="classification-section">
                        <h4>Classification</h4>
                        <div class="classification-result">
                          <span class="classification-label">{{ analysis.classification_label | titlecase }}</span>
                          <div class="confidence-bar">
                            <div class="confidence-fill"
                                 [class.high]="(analysis.classification_confidence || 0) > 0.8"
                                 [class.medium]="(analysis.classification_confidence || 0) > 0.5 && (analysis.classification_confidence || 0) <= 0.8"
                                 [class.low]="(analysis.classification_confidence || 0) <= 0.5"
                                 [style.width.%]="(analysis.classification_confidence || 0) * 100">
                            </div>
                          </div>
                          <span>{{ ((analysis.classification_confidence || 0) * 100).toFixed(1) }}%</span>
                        </div>
                      </div>

                      <mat-divider></mat-divider>

                      <div class="attributes-section">
                        <h4>Attributes</h4>
                        <div class="attributes-grid">
                          @for (attr of analysis.extracted_attributes; track attr.id) {
                            <div class="attribute-chip">
                              <span class="attr-name">{{ attr.attribute_name | titlecase }}</span>
                              <span class="attr-value">{{ attr.attribute_value }}</span>
                            </div>
                          }
                        </div>
                      </div>

                      @if (analysis.detected_defects.length > 0) {
                        <mat-divider></mat-divider>
                        <div class="defects-section">
                          <h4>Defects ({{ analysis.detected_defects.length }})</h4>
                          @for (defect of analysis.detected_defects; track defect.id) {
                            <div class="defect-item">
                              <mat-icon [class]="'severity-' + defect.severity">warning</mat-icon>
                              <div>
                                <strong>{{ defect.defect_type | titlecase }}</strong>
                                <span class="defect-severity">{{ defect.severity }} severity</span>
                                @if (defect.description) {
                                  <p>{{ defect.description }}</p>
                                }
                              </div>
                              <span class="defect-confidence">{{ ((defect.confidence || 0) * 100).toFixed(0) }}%</span>
                            </div>
                          }
                        </div>
                      }

                      <div class="processing-time">
                        Processed in {{ analysis.processing_time_ms }}ms
                      </div>
                    </div>
                  } @else if (analysis.status === 'failed') {
                    <div class="error-message">
                      <mat-icon>error</mat-icon>
                      {{ analysis.error_message || 'Analysis failed' }}
                      <button mat-stroked-button (click)="retryAnalysis(analysis.product_image_id)">
                        <mat-icon>refresh</mat-icon> Retry
                      </button>
                    </div>
                  }
                </mat-card>
              } @empty {
                <div class="empty-state">
                  <mat-icon>analytics</mat-icon>
                  <p>No analysis results yet. Upload an image to start processing.</p>
                </div>
              }
            </div>
          </mat-tab>
        </mat-tab-group>
      }
    </div>
  `,
  styles: [`
    .loading-container { display: flex; justify-content: center; padding: 60px; }
    .tab-content { padding: 24px 0; }
    .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .detail-card { padding: 24px; border-radius: 12px; }
    .detail-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
    .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
    .detail-row span { color: #666; font-size: 14px; }
    .description-card p { line-height: 1.6; color: #444; margin-bottom: 12px; }
    .analysis-card { padding: 24px; border-radius: 12px; margin-bottom: 16px; }
    .analysis-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .model-version { font-size: 12px; color: #999; font-family: monospace; }
    .classification-result { display: flex; align-items: center; gap: 12px; margin-top: 8px; }
    .classification-label { font-size: 18px; font-weight: 600; text-transform: capitalize; min-width: 120px; }
    .attributes-section, .defects-section, .classification-section { padding: 16px 0; }
    h4 { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #333; }
    .attributes-grid { display: flex; gap: 8px; flex-wrap: wrap; }
    .attribute-chip { background: #e8eaf6; border-radius: 16px; padding: 6px 14px; font-size: 13px; }
    .attr-name { color: #666; margin-right: 4px; }
    .attr-value { font-weight: 500; }
    .defect-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px; background: #fff8e1; border-radius: 8px; margin-bottom: 8px; }
    .defect-severity { color: #888; font-size: 12px; margin-left: 8px; }
    .defect-confidence { font-weight: 600; color: #666; }
    .severity-low { color: #ff9800; }
    .severity-medium { color: #f44336; }
    .severity-high { color: #b71c1c; }
    .processing-time { text-align: right; font-size: 12px; color: #999; margin-top: 12px; }
    .error-message { display: flex; align-items: center; gap: 12px; padding: 16px; background: #ffebee; border-radius: 8px; color: #c62828; }
    .empty-state { text-align: center; padding: 40px; color: #999; }
    .empty-state mat-icon { font-size: 48px; width: 48px; height: 48px; color: #ccc; }
  `],
})
export class ProductDetailComponent implements OnInit {
  product = signal<Product | null>(null);
  analyses = signal<AnalysisResult[]>([]);
  loading = signal(true);

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private notification: NotificationService,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.api.getProduct(id).subscribe({
      next: (product) => {
        this.product.set(product);
        this.loading.set(false);
        this.loadAnalysis(id);
      },
      error: () => this.loading.set(false),
    });
  }

  loadAnalysis(productId: string): void {
    this.api.getProductAnalysis(productId).subscribe({
      next: (analyses) => this.analyses.set(analyses),
    });
  }

  copyDescription(): void {
    const desc = this.product()?.ai_description;
    if (desc) {
      navigator.clipboard.writeText(desc);
      this.notification.success('Description copied to clipboard');
    }
  }

  retryAnalysis(imageId: string): void {
    this.api.retryAnalysis(imageId).subscribe({
      next: () => this.notification.success('Analysis retry started'),
      error: () => this.notification.error('Failed to retry analysis'),
    });
  }
}
