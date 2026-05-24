import { inject } from '@angular/core';
import { CanActivateFn, ActivatedRouteSnapshot, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { UserRole } from '../models/user.models';

export const roleGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const auth   = inject(AuthService);
  const router = inject(Router);
  const need   = route.data['role'] as UserRole;
  const role   = auth.getRole();
  if (role === need || role === 'admin') return true;
  const target = role === 'clinician' ? '/clinician' : role === 'patient' ? '/patient' : '/login';
  return router.createUrlTree([target]);
};
