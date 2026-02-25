import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'auth',
    loadChildren: () =>
      import('./features/auth/auth.routes').then((m) => m.AUTH_ROUTES),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'products',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/products/products.routes').then((m) => m.PRODUCTS_ROUTES),
  },
  {
    path: 'upload',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/upload/upload.routes').then((m) => m.UPLOAD_ROUTES),
  },
  {
    path: 'analysis',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/analysis/analysis.routes').then((m) => m.ANALYSIS_ROUTES),
  },
  {
    path: 'exports',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/exports/exports.component').then((m) => m.ExportsComponent),
  },
  {
    path: 'settings',
    canActivate: [authGuard],
    children: [
      {
        path: 'webhooks',
        loadComponent: () =>
          import('./features/settings/webhooks/webhooks.component').then((m) => m.WebhooksComponent),
      },
      {
        path: 'organization',
        loadComponent: () =>
          import('./features/settings/organization/organization-settings.component').then(
            (m) => m.OrganizationSettingsComponent
          ),
      },
    ],
  },
  {
    path: 'admin',
    canActivate: [authGuard],
    children: [
      {
        path: 'ab-testing',
        loadComponent: () =>
          import('./features/admin/ab-testing/ab-testing.component').then(
            (m) => m.ABTestingComponent
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
