import { Routes } from '@angular/router';

export const CLINICIAN_ROUTES: Routes = [
  { path: '', redirectTo: 'overview', pathMatch: 'full' },
  {
    path: 'overview',
    loadComponent: () =>
      import('./overview-page/overview-page.component').then(m => m.OverviewPageComponent)
  },
  {
    path: 'pending',
    loadComponent: () =>
      import('./pending-review-page/pending-review-page.component').then(m => m.PendingReviewPageComponent)
  },
  {
    path: 'appointments',
    loadComponent: () =>
      import('./appointments-page/appointments-page.component').then(m => m.AppointmentsPageComponent)
  }
];
