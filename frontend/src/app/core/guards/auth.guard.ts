import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Awaits the async session restore (getSession) before deciding to allow or
 * redirect. Without this await, on a hard refresh the guard runs synchronously
 * before the Supabase/mock session has been loaded from storage, causing a
 * spurious redirect to /login even when the user has a valid session.
 */
export const authGuard: CanActivateFn = async () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  // Wait for the initial session check to complete.
  await auth.sessionReady$;

  if (auth.isAuthenticated()) return true;
  return router.createUrlTree(['/login']);
};
