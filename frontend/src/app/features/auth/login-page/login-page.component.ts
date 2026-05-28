import { Component, ChangeDetectionStrategy, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { trigger, transition, style, animate } from '@angular/animations';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('cardIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.95) translateY(12px)' }),
        animate('350ms cubic-bezier(0.4,0,0.2,1)', style({ opacity: 1, transform: 'scale(1) translateY(0)' }))
      ])
    ])
  ],
  template: `
    <div class="login-wrapper">
      <div class="login-bg"></div>
      <mat-card class="login-card" [@cardIn]>
        <div class="login-logo">
          <mat-icon class="logo-icon">local_hospital</mat-icon>
          <h1 class="logo-title">Healthcare Triage</h1>
          <p class="logo-sub">AI-Powered Clinical Decision Support</p>
        </div>

        <mat-card-content>
          <form [formGroup]="form" (ngSubmit)="submit()" class="login-form">
            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Username</mat-label>
              <mat-icon matPrefix>person</mat-icon>
              <input matInput formControlName="username" id="username" autocomplete="username">
              <mat-error>Username is required</mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Password</mat-label>
              <mat-icon matPrefix>lock</mat-icon>
              <input matInput [type]="hide ? 'password' : 'text'"
                     formControlName="password" id="password" autocomplete="current-password">
              <button mat-icon-button matSuffix type="button" (click)="hide = !hide">
                <mat-icon>{{ hide ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
              <mat-error>Password is required</mat-error>
            </mat-form-field>

            <div class="role-hint">
              <mat-icon>info</mat-icon>
              <span>Use <strong>patient</strong> / <strong>clinician</strong> as username &amp; any password (dev mode)</span>
            </div>

            <button mat-raised-button color="primary" type="submit" id="loginBtn"
                    [disabled]="form.invalid || loading" class="login-btn">
              <mat-icon *ngIf="!loading">login</mat-icon>
              <mat-progress-spinner *ngIf="loading" mode="indeterminate" [diameter]="20" color="accent"></mat-progress-spinner>
              {{ loading ? 'Signing in…' : 'Sign In' }}
            </button>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .login-wrapper {
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
      position: relative; overflow: hidden; background: #f4f7fb;
    }
    .login-bg {
      position: absolute; inset: 0; pointer-events: none;
      background: radial-gradient(ellipse at 20% 50%, rgba(0,150,136,0.1) 0%, transparent 60%),
                  radial-gradient(ellipse at 80% 20%, rgba(38,166,154,0.1) 0%, transparent 50%);
    }
    .login-card {
      width: 420px; max-width: 95vw;
      background: #ffffff !important; border: 1px solid #e8edf2 !important;
      border-radius: 20px !important; padding: 8px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.08) !important;
      position: relative; z-index: 1;
    }
    .login-logo { text-align: center; padding: 28px 16px 8px; }
    .logo-icon { font-size: 48px; width: 48px; height: 48px; color: #009688; display: block; margin: 0 auto 8px; }
    .logo-title { margin: 0 0 4px; font-size: 1.6rem; font-weight: 700; color: #212121; }
    .logo-sub   { margin: 0; font-size: 0.85rem; color: #616161; }
    .login-form { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }
    .full-w { width: 100%; }
    .role-hint {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 14px; border-radius: 8px;
      background: rgba(0,150,136,0.1); color: #616161; font-size: 0.8rem;
    }
    .role-hint mat-icon { font-size: 16px; width: 16px; height: 16px; color: #009688; }
    .login-btn {
      height: 48px; font-size: 1rem; font-weight: 600;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      background: #009688 !important; color: #ffffff !important;
    }
  `]
})
export class LoginPageComponent implements OnInit {
  form!: FormGroup;
  loading = false;
  hide = true;

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private notify: NotificationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    if (this.auth.isAuthenticated()) this.redirect();
    this.form = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.cdr.markForCheck();
    this.auth.login(this.form.value).subscribe({
      next: () => this.redirect(),
      error: err => {
        this.loading = false;
        this.cdr.markForCheck();
        this.notify.error(err?.error?.detail ?? 'Login failed');
      }
    });
  }

  private redirect(): void {
    this.router.navigate([this.auth.getRole() === 'clinician' ? '/clinician' : '/patient']);
  }
}
