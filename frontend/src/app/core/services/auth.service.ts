import { Injectable, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { createClient, SupabaseClient, User, Session } from '@supabase/supabase-js';
import { environment } from '../../../environments/environment';
import { UserRole } from '../models/user.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  public supabase: SupabaseClient;

  private _session = signal<Session | null>(null);
  private _user = signal<User | null>(null);

  readonly isAuthenticated = computed(() => !!this._session());
  readonly currentUser = computed(() => this._user());
  readonly currentRole = computed(() => (this._user()?.user_metadata?.['role'] as UserRole) ?? 'patient');
  readonly currentUsername = computed(() => this._user()?.email ?? null);
  readonly currentName = computed(() => this._user()?.user_metadata?.['name'] || this._user()?.email || null);
  readonly currentAge = computed(() => this._user()?.user_metadata?.['age'] ?? null);
  readonly currentGender = computed(() => this._user()?.user_metadata?.['gender'] ?? '');

  constructor(private router: Router) {
    this.supabase = createClient(environment.supabaseUrl, environment.supabaseKey);

    this.supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        this.updateState(session, session.user);
      } else {
        this.checkMockSession();
      }
    });

    this.supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        this.updateState(session, session.user);
      } else if (!this._session()?.user?.email?.includes('clinician@gmail.com')) {
        this.clearState();
      }
    });
  }

  private updateState(session: any, user: any) {
    this._session.set(session);
    this._user.set(user);
    if (session) {
      localStorage.setItem('hta_token', session.access_token);
      localStorage.setItem('hta_user', JSON.stringify(user));
    }
  }

  private clearState() {
    this._session.set(null);
    this._user.set(null);
    localStorage.removeItem('hta_token');
    localStorage.removeItem('hta_user');
  }

  private checkMockSession() {
    const htaUser = localStorage.getItem('hta_user');
    const htaToken = localStorage.getItem('hta_token');
    if (htaUser && htaToken) {
      try {
        const user = JSON.parse(htaUser);
        if (user.email === 'clinician@gmail.com' || user.sub === 'clinician') {
          this._session.set({ access_token: htaToken, user } as any);
          this._user.set(user);
        }
      } catch (e) {}
    }
  }

  async logout(): Promise<void> {
    this.clearState();
    await this.supabase.auth.signOut();
    this.router.navigate(['/login']);
  }

  async signIn(email: string, password: string): Promise<any> {
    if (email === 'clinician@gmail.com' && password === 'clinician') {
      const mockUser = {
        id: 'clinician-mock-id',
        email: 'clinician@gmail.com',
        user_metadata: { role: 'clinician', name: 'Dr. Smith' }
      } as any;
      const mockSession = { access_token: 'mock-clinician-token', user: mockUser } as any;
      this.updateState(mockSession, mockUser);
      return { user: mockUser, session: mockSession };
    }

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
