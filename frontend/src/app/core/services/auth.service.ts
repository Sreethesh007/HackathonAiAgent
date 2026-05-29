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

  constructor(private router: Router) {
    this.supabase = createClient(environment.supabaseUrl, environment.supabaseKey);

    this.supabase.auth.getSession().then(({ data: { session } }) => {
      this._session.set(session);
      this._user.set(session?.user ?? null);
    });

    this.supabase.auth.onAuthStateChange((_event, session) => {
      this._session.set(session);
      this._user.set(session?.user ?? null);
    });
  }

  async logout(): Promise<void> {
    await this.supabase.auth.signOut();
    this.router.navigate(['/login']);
  }

  async signIn(email: string, password: string): Promise<any> {
    const { data, error } = await this.supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
  }

  async signUp(email: string, password: string, metadata: any): Promise<any> {
    const { data, error } = await this.supabase.auth.signUp({
      email, password, options: { data: metadata }
    });
    if (error) throw error;
    return data;
  }

  async verifyOtp(email: string, token: string, type: any = 'signup'): Promise<any> {
    const { data, error } = await this.supabase.auth.verifyOtp({ email, token, type });
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
