import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { AuthService } from '../../core/services/auth.service';
import { OrganizationService } from '../../core/services/organization.service';
import { Organization } from '../../core/models/organization.model';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MatSidenavModule, MatToolbarModule,
    MatIconModule, MatButtonModule, MatListModule, MatMenuModule,
    MatDividerModule,
  ],
  template: `
    <mat-sidenav-container class="layout-container">
      @if (authService.isAuthenticated()) {
        <mat-sidenav mode="side" opened class="sidenav">
          <div class="logo">
            <mat-icon class="logo-icon">auto_awesome</mat-icon>
            <span class="logo-text">ImagineAI</span>
          </div>
          <mat-nav-list>
            <a mat-list-item routerLink="/dashboard" routerLinkActive="active">
              <mat-icon matListItemIcon>dashboard</mat-icon>
              <span matListItemTitle>Dashboard</span>
            </a>
            <a mat-list-item routerLink="/upload" routerLinkActive="active">
              <mat-icon matListItemIcon>cloud_upload</mat-icon>
              <span matListItemTitle>Upload</span>
            </a>
            <a mat-list-item routerLink="/products" routerLinkActive="active">
              <mat-icon matListItemIcon>inventory_2</mat-icon>
              <span matListItemTitle>Products</span>
            </a>
            <a mat-list-item routerLink="/exports" routerLinkActive="active">
              <mat-icon matListItemIcon>download</mat-icon>
              <span matListItemTitle>Exports</span>
            </a>

            <div class="nav-section-label">Settings</div>
            <a mat-list-item routerLink="/settings/webhooks" routerLinkActive="active">
              <mat-icon matListItemIcon>webhook</mat-icon>
              <span matListItemTitle>Webhooks</span>
            </a>
            <a mat-list-item routerLink="/settings/organization" routerLinkActive="active">
              <mat-icon matListItemIcon>business</mat-icon>
              <span matListItemTitle>Organization</span>
            </a>

            <div class="nav-section-label">Admin</div>
            <a mat-list-item routerLink="/admin/ab-testing" routerLinkActive="active">
              <mat-icon matListItemIcon>science</mat-icon>
              <span matListItemTitle>A/B Testing</span>
            </a>
          </mat-nav-list>
        </mat-sidenav>
      }

      <mat-sidenav-content>
        @if (authService.isAuthenticated()) {
          <mat-toolbar class="header">
            @if (orgService.organizations().length > 0) {
              <button mat-button [matMenuTriggerFor]="orgMenu" class="org-selector">
                <mat-icon>business</mat-icon>
                <span>{{ orgService.currentOrganization()?.name || 'Select Org' }}</span>
                <mat-icon>arrow_drop_down</mat-icon>
              </button>
              <mat-menu #orgMenu="matMenu">
                @for (org of orgService.organizations(); track org.id) {
                  <button mat-menu-item (click)="switchOrg(org)"
                    [class.active-org]="org.id === orgService.currentOrganization()?.id">
                    <mat-icon>{{ org.id === orgService.currentOrganization()?.id ? 'check' : 'business' }}</mat-icon>
                    <span>{{ org.name }}</span>
                  </button>
                }
                <mat-divider></mat-divider>
                <button mat-menu-item routerLink="/settings/organization">
                  <mat-icon>settings</mat-icon>
                  <span>Manage Organizations</span>
                </button>
              </mat-menu>
            }
            <span class="spacer"></span>
            <button mat-icon-button [matMenuTriggerFor]="userMenu">
              <mat-icon>account_circle</mat-icon>
            </button>
            <mat-menu #userMenu="matMenu">
              <div class="user-info" mat-menu-item disabled>
                {{ authService.user()?.email }}
              </div>
              <button mat-menu-item (click)="authService.logout()">
                <mat-icon>logout</mat-icon>
                <span>Logout</span>
              </button>
            </mat-menu>
          </mat-toolbar>
        }
        <main class="content">
          <ng-content></ng-content>
        </main>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .layout-container { height: 100vh; }
    .sidenav {
      width: 240px;
      background: #1a1a2e;
      border-right: none;
    }
    .logo {
      display: flex;
      align-items: center;
      padding: 20px 16px;
      gap: 10px;
    }
    .logo-icon { color: #7c4dff; font-size: 28px; width: 28px; height: 28px; }
    .logo-text { color: white; font-size: 20px; font-weight: 700; }
    .sidenav mat-nav-list a {
      color: #b0b0c0;
      border-radius: 8px;
      margin: 4px 8px;
    }
    .sidenav mat-nav-list a.active {
      color: white;
      background: rgba(124, 77, 255, 0.2);
    }
    .sidenav mat-nav-list a:hover {
      color: white;
      background: rgba(255, 255, 255, 0.08);
    }
    .nav-section-label {
      color: #666;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 16px 24px 4px;
    }
    .header {
      background: white;
      border-bottom: 1px solid #e0e0e0;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .spacer { flex: 1; }
    .content { padding: 0; min-height: calc(100vh - 64px); background: #f5f5f5; }
    .user-info { font-size: 13px; color: #666; }
    .org-selector {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 14px;
    }
    .active-org { background: rgba(124, 77, 255, 0.08); }
  `],
})
export class LayoutComponent {
  authService = inject(AuthService);
  orgService = inject(OrganizationService);

  switchOrg(org: Organization): void {
    this.orgService.selectOrganization(org);
    window.location.reload();
  }
}
