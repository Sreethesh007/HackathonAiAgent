import { Routes } from '@angular/router';

/**
 * Landing feature routes.
 * Registered directly in app.routes.ts via lazy loadComponent.
 * This barrel file is provided for future route-level guards or children.
 */
export const landingRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./landing-page/landing-page.component').then(
        m => m.LandingPageComponent
      ),
  },
];
