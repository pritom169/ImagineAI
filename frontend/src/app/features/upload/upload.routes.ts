import { Routes } from '@angular/router';

export const UPLOAD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./upload-page/upload-page.component').then((m) => m.UploadPageComponent),
  },
];
