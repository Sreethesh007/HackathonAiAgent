import { Injectable, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { createClient, SupabaseClient, User, Session } from '@supabase/supabase-js';
import { environment } from '../../../environments/environment';
import { UserRole } from '../models/user.models';

/** Key used to persist the "remember me" preference across tabs/restarts */
const REMEMBER_ME_KEY = 'hta_remember_me';
const MOCK_USER_KEY   = 'hta_user';
const MOCK_TOKEN_KEY  = 'hta_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  public supabase: SupabaseClient;

  private _session = signal<Session | null>(null);
  private _user    = signal<User | null>(null);

  /**
   * Resolves once the initial session check is complete.
   * Guards await this before deciding whether to allow or redirect,
   * preventing the race condition where the guard fires before
   * getSession() has returned on a page refresh.
   */
  readonly sessionReady$: Promise<void>;
  private _resolveSessionReady!: () => void;

  readonly isAuthenticated  = computed(() => !!this._session());
  readonly currentUser      = computed(() => this._user());
  readonly currentRole      = computed(() => (this._user()?.user_metadata?.['role'] as UserRole) ?? 'patient');
  readonly currentUsername  = computed(() => this._user()?.email ?? null);
  readonly currentName      = computed(() => this._user()?.user_metadata?.['name'] || this._user()?.email || null);
  readonly currentAge       = computed(() => this._user()?.user_metadata?.['age'] ?? null);
  readonly currentGender    = computed(() => this._user()?.user_metadata?.['gender'] ?? '');

  constructor(private router: Router) {
    // Create the ready promise up-front so guards can await it immediately.
    this.sessionReady$ = new Promise<void>(resolve => {
      this._resolveSessionReady = resolve;
    });

    // Determine storage based on "remember me" preference.
    const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
    const storage    = rememberMe ? localStorage : sessionStorage;

    this.supabase = createClient(environment.supabaseUrl, environment.supabaseKey, {
      auth: {
        persistSession  : true,
        autoRefreshToken: true,
        storage         : storage,
        // Bypass navigator.locks to prevent lock-contention errors during HMR
        // and when multiple tabs are open. The signature changed in supabase-js
        // v2.60+: 3 args (name, acquireTimeout, fn) — fn is the 3rd arg, not 2nd.
        lock: (_name: string, _acquireTimeout: number, fn: () => Promise<any>) => fn(),
      }
    } as any);

    // Restore session on startup (handles both Supabase and mock sessions).
    this.supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        this.updateState(session, session.user);
      } else {
        // Fall back to mock-clinician session if one was persisted.
        this.checkMockSession();
      }
      // Signal guards that the session check is complete.
      this._resolveSessionReady();
    });

    // Keep signals in sync with Supabase auth events (token refresh, etc.).
    this.supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        this.updateState(session, session.user);
      } else {
        // Only clear state when it's not a mock clinician session.
        const isMock = this._user()?.email === 'clinician@gmail.com';
        if (!isMock) {
          this.clearState();
        }
      }
    });
  }

  // ── State helpers ──────────────────────────────────────────────────────────

  private updateState(session: any, user: any) {
    this._session.set(session);
    this._user.set(user);
  }

  private clearState() {
    this._session.set(null);
    this._user.set(null);
    sessionStorage.removeItem(MOCK_USER_KEY);
    sessionStorage.removeItem(MOCK_TOKEN_KEY);
    localStorage.removeItem(MOCK_USER_KEY);
    localStorage.removeItem(MOCK_TOKEN_KEY);
  }

  /**
   * Restores a mock clinician session from whichever storage it was saved in.
   * Only applies when Supabase returns no real session.
   */
  private checkMockSession() {
    const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
    const storage    = rememberMe ? localStorage : sessionStorage;

    const htaUser  = storage.getItem(MOCK_USER_KEY);
    const htaToken = storage.getItem(MOCK_TOKEN_KEY);

    if (htaUser && htaToken) {
      try {
        const user = JSON.parse(htaUser);
        if (user.email === 'clinician@gmail.com' || user.sub === 'clinician') {
          this._session.set({ access_token: htaToken, user } as any);
          this._user.set(user);
        }
      } catch (e) { /* malformed JSON — ignore */ }
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  async logout(): Promise<void> {
    localStorage.removeItem(REMEMBER_ME_KEY);
    this.clearState();
    await this.supabase.auth.signOut();
    this.router.navigate(['/login']);
  }

  /**
   * Signs the user in.
   * @param rememberMe  When true the session survives browser restarts
   *                    (persisted in localStorage); when false it lives only
   *                    for the current tab (sessionStorage).
   */
  async signIn(email: string, password: string, rememberMe = false): Promise<any> {
    // Persist the preference BEFORE creating the Supabase client storage reference
    // so that checkMockSession() and future page loads use the right storage.
    if (rememberMe) {
      localStorage.setItem(REMEMBER_ME_KEY, 'true');
    } else {
      localStorage.removeItem(REMEMBER_ME_KEY);
    }

    const storage = rememberMe ? localStorage : sessionStorage;

    // ── Mock clinician bypass ──────────────────────────────────────────────
    if (email === 'clinician@gmail.com' && password === 'clinician') {
      const mockUser = {
        id           : 'clinician-mock-id',
        email        : 'clinician@gmail.com',
        user_metadata: { role: 'clinician', name: 'Dr. Smith' }
      } as any;
      const mockSession = { access_token: 'mock-clinician-token', user: mockUser } as any;

      // Persist mock session in the correct storage.
      storage.setItem(MOCK_USER_KEY,  JSON.stringify(mockUser));
      storage.setItem(MOCK_TOKEN_KEY, mockSession.access_token);

      this.updateState(mockSession, mockUser);
      return { user: mockUser, session: mockSession };
    }

    // ── Real Supabase sign-in ──────────────────────────────────────────────
    const { data, error } = await this.supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if (data.session) {
      this.updateState(data.session, data.user);
    }
    return data;
  }

  async signUp(email: string, password: string, metadata: any): Promise<any> {
    const { data, error } = await this.supabase.auth.signUp({
      email, password, options: { data: metadata }
    });
    if (error) throw error;
    return data;
  }

  async resetPasswordForEmail(email: string): Promise<any> {
    const { data, error } = await this.supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`
    });
    if (error) throw error;
    return data;
  }

  async updatePassword(password: string): Promise<any> {
    const { data, error } = await this.supabase.auth.updateUser({ password });
    if (error) throw error;
    return data;
  }

  getToken(): string | null { return this._session()?.access_token ?? null; }
  getRole(): UserRole | null { return this.currentRole(); }
}
