import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  // ── Public ──────────────────────────────────────────────────────────────────
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login-page/login-page.component')
        .then(m => m.LoginPageComponent)
  },
  {
    path: 'signup',
    loadComponent: () =>
      import('./features/auth/signup-page/signup-page.component')
        .then(m => m.SignupPageComponent)
  },
  {
    path: 'verify-otp',
    loadComponent: () =>
      import('./features/auth/verify-otp-page/verify-otp-page.component')
        .then(m => m.VerifyOtpPageComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () =>
      import('./features/auth/forgot-password-page/forgot-password-page.component')
        .then(m => m.ForgotPasswordPageComponent)
  },
  {
    path: 'reset-password',
    loadComponent: () =>
      import('./features/auth/reset-password-page/reset-password-page.component')
        .then(m => m.ResetPasswordPageComponent)
  },

  // ── Patient (shell wraps children) ───────────────────────────────────────────
  {
    path: 'patient',
    canActivate: [authGuard, roleGuard],
    data: { role: 'patient' },
    loadComponent: () =>
      import('./features/patient/patient-shell/patient-shell.component')
        .then(m => m.PatientShellComponent),
    children: [
      { path: '', redirectTo: 'triage', pathMatch: 'full' },
      {
        path: 'triage',
        loadComponent: () =>
          import('./features/patient/triage-page/triage-page.component')
            .then(m => m.TriagePageComponent)
      }
    ]
  },

  // ── Clinician (shell wraps children) ─────────────────────────────────────────
  {
    path: 'clinician',
    canActivate: [authGuard, roleGuard],
    data: { role: 'clinician' },
    loadComponent: () =>
      import('./features/clinician/clinician-shell/clinician-shell.component')
        .then(m => m.ClinicianShellComponent),
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      {
        path: 'overview',
        loadComponent: () =>
          import('./features/clinician/overview-page/overview-page.component')
            .then(m => m.OverviewPageComponent)
      },
      {
        path: 'pending',
        loadComponent: () =>
          import('./features/clinician/pending-review-page/pending-review-page.component')
            .then(m => m.PendingReviewPageComponent)
      },
      {
        path: 'appointments',
        loadComponent: () =>
          import('./features/clinician/appointments-page/appointments-page.component')
            .then(m => m.AppointmentsPageComponent)
      }
    ]
  },

  // ── Defaults ─────────────────────────────────────────────────────────────────
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' }
];
