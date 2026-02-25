import { Routes } from '@angular/router';

export const ANALYSIS_ROUTES: Routes = [
  {
    path: ':imageId',
    loadComponent: () =>
      import('./analysis-viewer/analysis-viewer.component').then(
        (m) => m.AnalysisViewerComponent,
      ),
  },
];
