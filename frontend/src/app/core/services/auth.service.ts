import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { LoginRequest, LoginResponse, JwtPayload, UserRole } from '../models/user.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'hta_token';
  private readonly USER_KEY  = 'hta_user';

  private _token = signal<string | null>(this.loadToken());
  private _user  = signal<JwtPayload | null>(this.loadUser());

  readonly isAuthenticated = computed(() => {
    const u = this._user();
    if (!u) return false;
    return u.exp * 1000 > Date.now();
  });

  readonly currentUser     = computed(() => this._user());
  readonly currentRole     = computed(() => this._user()?.role ?? null);
  readonly currentUsername = computed(() => this._user()?.sub ?? null);

  constructor(private http: HttpClient, private router: Router) {}

  login(req: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>('/api/auth/login', req).pipe(
      tap(res => this.storeSession(res.access_token)),
      catchError(err => throwError(() => err))
    );
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this._token.set(null);
    this._user.set(null);
    this.router.navigate(['/login']);
  }

  getToken(): string | null { return this._token(); }
  getRole(): UserRole | null { return this.currentRole(); }

  private storeSession(token: string): void {
    const payload = this.decodeJwt(token);
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(payload));
    this._token.set(token);
    this._user.set(payload);
  }

  private loadToken(): string | null { return localStorage.getItem(this.TOKEN_KEY); }
  private loadUser(): JwtPayload | null {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  private decodeJwt(token: string): JwtPayload {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  }
}
