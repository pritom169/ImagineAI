import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Product, ProductCreate, ProductListResponse } from '../models/product.model';
import { AnalysisResult } from '../models/analysis.model';
import { ProcessingJob, DashboardStats, CategoryDistribution } from '../models/pipeline.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // --- Products ---
  getProducts(params?: Record<string, string>): Observable<ProductListResponse> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value) httpParams = httpParams.set(key, value);
      });
    }
    return this.http.get<ProductListResponse>(`${this.apiUrl}/products`, { params: httpParams });
  }

  getProduct(id: string): Observable<Product> {
    return this.http.get<Product>(`${this.apiUrl}/products/${id}`);
  }

  createProduct(data: ProductCreate): Observable<Product> {
    return this.http.post<Product>(`${this.apiUrl}/products`, data);
  }

  updateProduct(id: string, data: Partial<ProductCreate>): Observable<Product> {
    return this.http.patch<Product>(`${this.apiUrl}/products/${id}`, data);
  }

  deleteProduct(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/products/${id}`);
  }

  getProductAnalysis(productId: string): Observable<AnalysisResult[]> {
    return this.http.get<AnalysisResult[]>(`${this.apiUrl}/products/${productId}/analysis`);
  }

  // --- Uploads ---
  getPresignedUrl(data: {
    product_id: string;
    filename: string;
    content_type: string;
    file_size_bytes: number;
  }): Observable<{ upload_url: string; image_id: string; s3_key: string; expires_in: number }> {
    return this.http.post<any>(`${this.apiUrl}/uploads/presigned-url`, data);
  }

  confirmUpload(imageId: string): Observable<{ image_id: string; job_id: string; status: string }> {
    return this.http.post<any>(`${this.apiUrl}/uploads/confirm`, { image_id: imageId });
  }

  directUpload(productId: string, file: File): Observable<{ image_id: string; job_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.apiUrl}/uploads/direct?product_id=${productId}`, formData);
  }

  // --- Analysis ---
  getAnalysis(imageId: string): Observable<AnalysisResult> {
    return this.http.get<AnalysisResult>(`${this.apiUrl}/analysis/${imageId}`);
  }

  retryAnalysis(imageId: string): Observable<{ job_id: string }> {
    return this.http.post<any>(`${this.apiUrl}/analysis/${imageId}/retry`, {});
  }

  // --- Batch ---
  createBatch(productId: string, imageIds: string[]): Observable<ProcessingJob> {
    return this.http.post<ProcessingJob>(`${this.apiUrl}/batch`, {
      product_id: productId,
      image_ids: imageIds,
    });
  }

  getBatchStatus(jobId: string): Observable<ProcessingJob> {
    return this.http.get<ProcessingJob>(`${this.apiUrl}/batch/${jobId}`);
  }

  // --- Jobs ---
  getJobs(params?: Record<string, string>): Observable<{ items: ProcessingJob[]; total: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value) httpParams = httpParams.set(key, value);
      });
    }
    return this.http.get<any>(`${this.apiUrl}/jobs`, { params: httpParams });
  }

  getJob(id: string): Observable<ProcessingJob> {
    return this.http.get<ProcessingJob>(`${this.apiUrl}/jobs/${id}`);
  }

  // --- Dashboard ---
  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.apiUrl}/dashboard/stats`);
  }

  getRecentActivity(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/dashboard/recent`);
  }

  getCategoryDistribution(): Observable<CategoryDistribution[]> {
    return this.http.get<CategoryDistribution[]>(`${this.apiUrl}/dashboard/category-distribution`);
  }

  // --- Webhooks ---
  getWebhooks(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/webhooks`);
  }

  createWebhook(data: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/webhooks`, data);
  }

  updateWebhook(id: string, data: any): Observable<any> {
    return this.http.patch<any>(`${this.apiUrl}/webhooks/${id}`, data);
  }

  deleteWebhook(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/webhooks/${id}`);
  }

  testWebhook(id: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/webhooks/${id}/test`, {});
  }

  getWebhookDeliveries(id: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/webhooks/${id}/deliveries`);
  }

  // --- Exports ---
  createExport(data: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/exports`, data);
  }

  getExports(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/exports`);
  }

  getExport(id: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/exports/${id}`);
  }

  deleteExport(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/exports/${id}`);
  }

  // --- A/B Testing (Admin) ---
  getExperiments(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/admin/ab-testing/experiments`);
  }

  createExperiment(data: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/admin/ab-testing/experiments`, data);
  }

  updateExperiment(id: string, data: any): Observable<any> {
    return this.http.patch<any>(`${this.apiUrl}/admin/ab-testing/experiments/${id}`, data);
  }

  deleteExperiment(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/admin/ab-testing/experiments/${id}`);
  }

  getExperimentResults(id: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/admin/ab-testing/experiments/${id}/results`);
  }

  // --- Rate Limits (Admin) ---
  getRateLimits(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/admin/rate-limits`);
  }

  createRateLimit(data: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/admin/rate-limits`, data);
  }

  updateRateLimit(id: string, data: any): Observable<any> {
    return this.http.patch<any>(`${this.apiUrl}/admin/rate-limits/${id}`, data);
  }

  deleteRateLimit(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/admin/rate-limits/${id}`);
  }
}
