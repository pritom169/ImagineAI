import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { Product } from '../../../core/models/product.model';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [
    CommonModule, RouterModule, FormsModule, MatCardModule, MatButtonModule,
    MatIconModule, MatChipsModule, MatPaginatorModule, MatFormFieldModule,
    MatInputModule, MatSelectModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>Products</h1>
        <button mat-raised-button color="primary" routerLink="/upload">
          <mat-icon>add</mat-icon> New Product
        </button>
      </div>

      <mat-card class="filters-card">
        <div class="filters">
          <mat-form-field appearance="outline" class="search-field">
            <mat-label>Search products</mat-label>
            <input matInput [(ngModel)]="searchQuery" (keyup.enter)="loadProducts()"
                   placeholder="Search by title...">
            <mat-icon matSuffix>search</mat-icon>
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>Category</mat-label>
            <mat-select [(ngModel)]="categoryFilter" (selectionChange)="loadProducts()">
              <mat-option value="">All</mat-option>
              <mat-option value="electronics">Electronics</mat-option>
              <mat-option value="clothing">Clothing</mat-option>
              <mat-option value="footwear">Footwear</mat-option>
              <mat-option value="furniture">Furniture</mat-option>
              <mat-option value="jewelry">Jewelry</mat-option>
              <mat-option value="sports">Sports</mat-option>
              <mat-option value="other">Other</mat-option>
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>Status</mat-label>
            <mat-select [(ngModel)]="statusFilter" (selectionChange)="loadProducts()">
              <mat-option value="">All</mat-option>
              <mat-option value="draft">Draft</mat-option>
              <mat-option value="processing">Processing</mat-option>
              <mat-option value="active">Active</mat-option>
              <mat-option value="archived">Archived</mat-option>
            </mat-select>
          </mat-form-field>
        </div>
      </mat-card>

      @if (loading()) {
        <div class="loading-container"><mat-spinner></mat-spinner></div>
      } @else {
        <div class="product-grid">
          @for (product of products(); track product.id) {
            <mat-card class="product-card" [routerLink]="['/products', product.id]">
              <div class="product-image-placeholder">
                <mat-icon>image</mat-icon>
                @if (product.images.length > 0) {
                  <span class="image-count">{{ product.images.length }} image(s)</span>
                }
              </div>
              <mat-card-content>
                <h3>{{ product.title || 'Untitled Product' }}</h3>
                <div class="product-meta">
                  @if (product.category) {
                    <span class="status-badge active">{{ product.category }}</span>
                  }
                  <span class="status-badge" [ngClass]="product.status">{{ product.status }}</span>
                </div>
                <p class="product-date">{{ product.created_at | date:'mediumDate' }}</p>
              </mat-card-content>
            </mat-card>
          } @empty {
            <div class="empty-state">
              <mat-icon>inventory_2</mat-icon>
              <h3>No products found</h3>
              <p>Upload your first product image to get started</p>
              <button mat-raised-button color="primary" routerLink="/upload">Upload Image</button>
            </div>
          }
        </div>

        @if (totalProducts() > 0) {
          <mat-paginator [length]="totalProducts()" [pageSize]="pageSize"
                         [pageSizeOptions]="[10, 20, 50]" (page)="onPage($event)">
          </mat-paginator>
        }
      }
    </div>
  `,
  styles: [`
    .filters-card { margin-bottom: 20px; padding: 16px; border-radius: 12px; }
    .filters { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
    .search-field { flex: 1; min-width: 250px; }
    .loading-container { display: flex; justify-content: center; padding: 60px; }
    .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
    .product-card { cursor: pointer; border-radius: 12px; transition: transform 0.2s, box-shadow 0.2s; overflow: hidden; }
    .product-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .product-image-placeholder {
      height: 180px; background: #e8eaf6; display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 8px;
    }
    .product-image-placeholder mat-icon { font-size: 48px; width: 48px; height: 48px; color: #9fa8da; }
    .image-count { font-size: 12px; color: #666; }
    mat-card-content h3 { font-size: 16px; font-weight: 600; margin: 12px 0 8px; }
    .product-meta { display: flex; gap: 8px; flex-wrap: wrap; }
    .product-date { font-size: 12px; color: #999; margin-top: 8px; }
    .empty-state { grid-column: 1 / -1; text-align: center; padding: 60px; }
    .empty-state mat-icon { font-size: 64px; width: 64px; height: 64px; color: #ccc; }
    .empty-state h3 { margin: 16px 0 8px; color: #666; }
    .empty-state p { color: #999; margin-bottom: 16px; }
  `],
})
export class ProductListComponent implements OnInit {
  products = signal<Product[]>([]);
  totalProducts = signal(0);
  loading = signal(true);
  searchQuery = '';
  categoryFilter = '';
  statusFilter = '';
  pageSize = 20;
  currentPage = 1;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
    this.loading.set(true);
    const params: Record<string, string> = {
      page: this.currentPage.toString(),
      page_size: this.pageSize.toString(),
    };
    if (this.searchQuery) params['search'] = this.searchQuery;
    if (this.categoryFilter) params['category'] = this.categoryFilter;
    if (this.statusFilter) params['status'] = this.statusFilter;

    this.api.getProducts(params).subscribe({
      next: (res) => {
        this.products.set(res.items);
        this.totalProducts.set(res.total);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  onPage(event: PageEvent): void {
    this.currentPage = event.pageIndex + 1;
    this.pageSize = event.pageSize;
    this.loadProducts();
  }
}
