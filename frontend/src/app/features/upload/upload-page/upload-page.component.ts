import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatStepperModule } from '@angular/material/stepper';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../../core/services/api.service';
import { WebSocketService } from '../../../core/services/websocket.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ProcessingUpdate } from '../../../core/models/pipeline.model';

interface UploadedFile {
  file: File;
  preview: string;
  uploading: boolean;
  progress: number;
}

interface PipelineStep {
  name: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  data?: Record<string, unknown>;
}

@Component({
  selector: 'app-upload-page',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatCardModule, MatButtonModule,
    MatIconModule, MatFormFieldModule, MatInputModule, MatSelectModule,
    MatProgressBarModule, MatStepperModule, MatChipsModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>Upload Product Images</h1>
      </div>

      <mat-stepper [linear]="true" #stepper>
        <!-- Step 1: Product Info -->
        <mat-step [stepControl]="productForm">
          <ng-template matStepLabel>Product Info</ng-template>
          <mat-card class="step-card">
            <form [formGroup]="productForm">
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Product Title</mat-label>
                <input matInput formControlName="title" placeholder="e.g., Vintage Leather Jacket">
              </mat-form-field>
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Description (optional)</mat-label>
                <textarea matInput formControlName="description" rows="3"
                          placeholder="Brief product description..."></textarea>
              </mat-form-field>
              <mat-form-field appearance="outline">
                <mat-label>Category (optional - AI will detect)</mat-label>
                <mat-select formControlName="category">
                  <mat-option value="">Let AI detect</mat-option>
                  <mat-option value="electronics">Electronics</mat-option>
                  <mat-option value="clothing">Clothing</mat-option>
                  <mat-option value="footwear">Footwear</mat-option>
                  <mat-option value="furniture">Furniture</mat-option>
                  <mat-option value="jewelry">Jewelry</mat-option>
                  <mat-option value="sports">Sports</mat-option>
                  <mat-option value="other">Other</mat-option>
                </mat-select>
              </mat-form-field>
              <button mat-raised-button color="primary" matStepperNext
                      [disabled]="productForm.invalid">
                Next <mat-icon>arrow_forward</mat-icon>
              </button>
            </form>
          </mat-card>
        </mat-step>

        <!-- Step 2: Upload Images -->
        <mat-step>
          <ng-template matStepLabel>Upload Images</ng-template>
          <mat-card class="step-card">
            <div class="upload-zone" (click)="fileInput.click()"
                 (dragover)="onDragOver($event)" (dragleave)="onDragLeave($event)"
                 (drop)="onDrop($event)" [class.dragover]="isDragging()">
              <mat-icon class="upload-icon">cloud_upload</mat-icon>
              <div class="upload-text">Drag & drop images here or click to browse</div>
              <div class="upload-hint">Supports JPG, PNG, WebP (max 50MB each)</div>
            </div>
            <input #fileInput type="file" hidden multiple accept="image/*"
                   (change)="onFilesSelected($event)">

            @if (files().length > 0) {
              <div class="file-list">
                @for (f of files(); track f.file.name; let i = $index) {
                  <div class="file-item">
                    <img [src]="f.preview" class="file-preview" alt="Preview">
                    <div class="file-info">
                      <span class="file-name">{{ f.file.name }}</span>
                      <span class="file-size">{{ formatSize(f.file.size) }}</span>
                    </div>
                    <button mat-icon-button (click)="removeFile(i)">
                      <mat-icon>close</mat-icon>
                    </button>
                  </div>
                }
              </div>
            }

            <div class="step-actions">
              <button mat-button matStepperPrevious>Back</button>
              <button mat-raised-button color="primary" (click)="startUpload()"
                      [disabled]="files().length === 0 || uploading()">
                @if (uploading()) {
                  Uploading...
                } @else {
                  Upload & Analyze ({{ files().length }} images)
                }
              </button>
            </div>
          </mat-card>
        </mat-step>

        <!-- Step 3: Processing -->
        <mat-step>
          <ng-template matStepLabel>Processing</ng-template>
          <mat-card class="step-card">
            <div class="processing-view">
              <h3>AI Analysis in Progress</h3>
              <div class="pipeline-steps">
                @for (step of pipelineSteps(); track step.name) {
                  <div class="pipeline-step" [class]="step.status">
                    <div class="step-indicator">
                      @if (step.status === 'completed') {
                        <mat-icon>check_circle</mat-icon>
                      } @else if (step.status === 'running') {
                        <mat-icon class="spinning">sync</mat-icon>
                      } @else if (step.status === 'failed') {
                        <mat-icon>error</mat-icon>
                      } @else {
                        <mat-icon>radio_button_unchecked</mat-icon>
                      }
                    </div>
                    <div class="step-info">
                      <span class="step-label">{{ step.label }}</span>
                      @if (step.status === 'running') {
                        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
                      }
                    </div>
                  </div>
                }
              </div>

              @if (jobCompleted()) {
                <div class="completion-message">
                  <mat-icon class="success-icon">celebration</mat-icon>
                  <h3>Analysis Complete!</h3>
                  <button mat-raised-button color="primary"
                          [routerLink]="['/products', createdProductId()]">
                    View Results
                  </button>
                </div>
              }
            </div>
          </mat-card>
        </mat-step>
      </mat-stepper>
    </div>
  `,
  styles: [`
    .step-card { padding: 32px; margin-top: 16px; border-radius: 12px; }
    .full-width { width: 100%; }
    .step-actions { display: flex; justify-content: space-between; margin-top: 24px; }
    .file-list { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
    .file-item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: #f5f5f5; border-radius: 8px; }
    .file-preview { width: 48px; height: 48px; object-fit: cover; border-radius: 6px; }
    .file-info { flex: 1; display: flex; flex-direction: column; }
    .file-name { font-size: 14px; font-weight: 500; }
    .file-size { font-size: 12px; color: #999; }
    .processing-view { text-align: center; }
    .pipeline-steps { max-width: 400px; margin: 32px auto; text-align: left; }
    .pipeline-step { display: flex; align-items: center; gap: 12px; padding: 12px 0; }
    .pipeline-step.completed .step-indicator mat-icon { color: #4caf50; }
    .pipeline-step.running .step-indicator mat-icon { color: #2196f3; }
    .pipeline-step.failed .step-indicator mat-icon { color: #f44336; }
    .pipeline-step.pending .step-indicator mat-icon { color: #ccc; }
    .step-info { flex: 1; }
    .step-label { font-size: 14px; font-weight: 500; }
    .spinning { animation: spin 1s linear infinite; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .completion-message { margin-top: 32px; }
    .success-icon { font-size: 48px; width: 48px; height: 48px; color: #4caf50; }
    .completion-message h3 { margin: 12px 0 20px; }
  `],
})
export class UploadPageComponent {
  productForm: FormGroup;
  files = signal<UploadedFile[]>([]);
  uploading = signal(false);
  isDragging = signal(false);
  jobCompleted = signal(false);
  createdProductId = signal('');
  pipelineSteps = signal<PipelineStep[]>([
    { name: 'preprocess', label: 'Preprocessing Image', status: 'pending' },
    { name: 'classify', label: 'Product Classification', status: 'pending' },
    { name: 'extract_attributes', label: 'Attribute Extraction', status: 'pending' },
    { name: 'detect_defects', label: 'Defect Detection', status: 'pending' },
    { name: 'generate_description', label: 'AI Description Generation', status: 'pending' },
  ]);

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private ws: WebSocketService,
    private notification: NotificationService,
    private router: Router,
  ) {
    this.productForm = this.fb.group({
      title: ['', Validators.required],
      description: [''],
      category: [''],
    });
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    const files = event.dataTransfer?.files;
    if (files) this.addFiles(Array.from(files));
  }

  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) this.addFiles(Array.from(input.files));
  }

  addFiles(newFiles: File[]): void {
    const imageFiles = newFiles.filter((f) => f.type.startsWith('image/'));
    const uploadedFiles: UploadedFile[] = imageFiles.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      uploading: false,
      progress: 0,
    }));
    this.files.update((current) => [...current, ...uploadedFiles]);
  }

  removeFile(index: number): void {
    this.files.update((current) => {
      const updated = [...current];
      URL.revokeObjectURL(updated[index].preview);
      updated.splice(index, 1);
      return updated;
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  startUpload(): void {
    this.uploading.set(true);

    // Create product first
    const formValue = this.productForm.value;
    const productData: any = { title: formValue.title };
    if (formValue.description) productData.description = formValue.description;
    if (formValue.category) productData.category = formValue.category;

    this.api.createProduct(productData).subscribe({
      next: (product) => {
        this.createdProductId.set(product.id);
        // Upload first file via direct upload
        const file = this.files()[0].file;
        this.api.directUpload(product.id, file).subscribe({
          next: (result) => {
            this.uploading.set(false);
            this.notification.success('Upload complete! Processing started.');
            // Connect WebSocket for real-time updates
            this.connectWebSocket(result.job_id);
          },
          error: () => {
            this.uploading.set(false);
            this.notification.error('Upload failed');
          },
        });
      },
      error: () => {
        this.uploading.set(false);
        this.notification.error('Failed to create product');
      },
    });
  }

  private connectWebSocket(jobId: string): void {
    this.ws.connect(jobId).subscribe({
      next: (update: ProcessingUpdate) => {
        if (update.type === 'step_update' && update.step) {
          this.pipelineSteps.update((steps) =>
            steps.map((s) => ({
              ...s,
              status: s.name === update.step ? (update.status as any) : s.status,
              data: s.name === update.step ? update.data : s.data,
            })),
          );
        } else if (update.type === 'job_complete') {
          this.jobCompleted.set(true);
          this.notification.success('Analysis complete!');
        } else if (update.type === 'job_failed') {
          this.notification.error('Processing failed');
        }
      },
      error: () => {
        this.notification.info('WebSocket disconnected. Check results on the product page.');
        this.jobCompleted.set(true);
      },
    });
  }
}
