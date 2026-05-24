import { Routes } from '@angular/router';

export const PATIENT_ROUTES: Routes = [
  { path: '', redirectTo: 'triage', pathMatch: 'full' },
  {
    path: 'triage',
    loadComponent: () =>
      import('./triage-page/triage-page.component').then(m => m.TriagePageComponent)
  }
];
