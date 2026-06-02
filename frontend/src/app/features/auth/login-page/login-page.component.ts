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

import { MatCheckboxModule } from '@angular/material/checkbox';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule,
    MatCheckboxModule
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
              <mat-label>Email</mat-label>
              <mat-icon matPrefix>email</mat-icon>
              <input matInput formControlName="email" id="email" type="email" autocomplete="email">
              <mat-error><strong>Valid email is required</strong></mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Password</mat-label>
              <mat-icon matPrefix>lock</mat-icon>
              <input matInput [type]="hide ? 'password' : 'text'"
                     formControlName="password" id="password" autocomplete="current-password">
              <button mat-icon-button matSuffix type="button" (click)="hide = !hide">
                <mat-icon>{{ hide ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
              <mat-error><strong>Password is required</strong></mat-error>
            </mat-form-field>

            <div class="form-actions">
              <mat-checkbox formControlName="rememberMe">Remember me</mat-checkbox>
              <a routerLink="/forgot-password" class="forgot-link">Forgot password?</a>
            </div>

            <button mat-raised-button color="primary" type="submit" id="loginBtn"
                    [disabled]="form.invalid || loading" class="login-btn">
              <mat-progress-spinner *ngIf="loading" mode="indeterminate" [diameter]="20" color="accent"></mat-progress-spinner>
              {{ loading ? 'Signing in…' : 'Sign In' }}
            </button>
            <div class="signup-prompt">
              Don't have an account? <a routerLink="/signup">Sign up</a>
            </div>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
styles: [`
  .login-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    background: #eef2f5;
  }

  .login-bg {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(
        ellipse at 20% 50%,
        rgba(0,150,136,0.08) 0%,
        transparent 60%
      ),
      radial-gradient(
        ellipse at 80% 20%,
        rgba(38,166,154,0.06) 0%,
        transparent 50%
      );
  }

  .login-card {
    width: 420px;
    max-width: 95vw;
    background: #ffffff !important;
    border: 1px solid #dbe3ea !important;
    border-radius: 22px !important;
    padding: 12px;
    position: relative;
    z-index: 1;

    box-shadow:
      0 10px 30px rgba(0,0,0,0.08),
      0 4px 12px rgba(0,0,0,0.04) !important;

    backdrop-filter: blur(6px);
  }

  .login-logo {
    text-align: center;
    padding: 28px 18px 14px;
  }

  .logo-icon {
    font-size: 50px;
    width: 50px;
    height: 50px;
    color: #00897b;
    display: block;
    margin: 0 auto 10px;
  }

  .logo-title {
    margin: 0 0 6px;
    font-size: 1.65rem;
    font-weight: 700;
    color: #1f2937;
    letter-spacing: 0.2px;
  }

  .logo-sub {
    margin: 0;
    font-size: 0.9rem;
    color: #5f6b7a;
    font-weight: 400;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: 18px;
    padding: 12px 4px 8px;
  }

  .full-w {
    width: 100%;
  }

  /* Form field spacing */
  ::ng-deep .mat-mdc-form-field {
    margin-bottom: 2px;
  }

  /* Input wrapper */
  ::ng-deep .mat-mdc-text-field-wrapper {
    background: #f8fafc !important;
    border-radius: 14px !important;
    transition: all 0.25s ease;
  }

  /* REMOVE weird line issue */
  ::ng-deep .mat-mdc-form-field-flex {
    align-items: center !important;
  }

  ::ng-deep .mat-mdc-form-field-icon-prefix {
    padding-right: 6px !important;
    color: #54606e !important;
  }

  ::ng-deep .mat-mdc-form-field-infix {
    padding-left: 4px !important;
  }

  /* Placeholder */
  ::ng-deep input::placeholder {
    color: #4b5563 !important;
    opacity: 1 !important;
  }

  /* Input text */
  ::ng-deep .mat-mdc-input-element {
    color: #1f2937 !important;
    font-size: 0.96rem;
    caret-color: #009688 !important;
  }

  /* Labels */
  ::ng-deep .mdc-floating-label {
    color: #374151 !important;
    font-weight: 500;
  }

  /* Icons */
  ::ng-deep .mat-mdc-form-field-icon-prefix mat-icon,
  ::ng-deep .mat-mdc-form-field-icon-suffix mat-icon {
    color: #374151 !important;
  }

  /* Default border */
  ::ng-deep .mdc-notched-outline__leading,
  ::ng-deep .mdc-notched-outline__notch,
  ::ng-deep .mdc-notched-outline__trailing {
    border-color: #cfd8e3 !important;
    transition: border-color 0.25s ease;
  }

  /* Remove unwanted vertical outline artifact before prefix icons */
  ::ng-deep .mat-mdc-form-field .mdc-notched-outline__notch {
    border-left: none !important;
  }

  /* Remove notch artifact */
  ::ng-deep .mdc-text-field--outlined .mdc-notched-outline__notch {
    border-right: none !important;
  }

  /* Focus border */
  ::ng-deep .mat-focused .mdc-notched-outline__leading,
  ::ng-deep .mat-focused .mdc-notched-outline__notch,
  ::ng-deep .mat-focused .mdc-notched-outline__trailing {
    border-color: #009688 !important;
    border-width: 2px !important;
  }

  /* Error border */
  ::ng-deep .mat-mdc-form-field.mat-form-field-invalid .mdc-notched-outline__leading,
  ::ng-deep .mat-mdc-form-field.mat-form-field-invalid .mdc-notched-outline__notch,
  ::ng-deep .mat-mdc-form-field.mat-form-field-invalid .mdc-notched-outline__trailing {
    border-color: #e53935 !important;
  }

  /* Hover */
  ::ng-deep .mat-mdc-text-field-wrapper:hover {
    background: #f1f5f9 !important;
  }

  /* Checkbox / Remember me text */
  ::ng-deep .mat-mdc-checkbox .mdc-label {
    color: #374151 !important;
    font-weight: 500;
  }

  /* Button label flex to center spinner and text properly */
  ::ng-deep .mdc-button__label {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .role-hint {
    display: flex;
    align-items: center;
    gap: 10px;

    padding: 12px 14px;
    border-radius: 12px;

    background: rgba(0,150,136,0.08);

    color: #4b5563;
    font-size: 0.82rem;
    line-height: 1.4;
  }

  .role-hint mat-icon {
    font-size: 17px;
    width: 17px;
    height: 17px;
    color: #009688;
  }

  .form-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
  }

  .forgot-link {
    color: #009688;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .forgot-link:hover {
    text-decoration: underline;
  }

  .login-btn {
    height: 50px;
    font-size: 1rem;
    font-weight: 600;

    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    border-radius: 14px !important;

    background: #009688 !important;
    color: #ffffff !important;

    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease,
      background 0.2s ease !important;

    box-shadow: 0 6px 18px rgba(0,150,136,0.25);
  }

  .login-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    background: #00897b !important;
    box-shadow: 0 10px 22px rgba(0,150,136,0.3);
  }

  .login-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .signup-prompt {
    text-align: center;
    font-size: 0.9rem;
    color: #5f6b7a;
    margin-top: 8px;
  }

  .signup-prompt a {
    color: #009688;
    text-decoration: none;
    font-weight: 600;
  }

  .signup-prompt a:hover {
    text-decoration: underline;
  }

  mat-error {
    font-size: 0.78rem;
    margin-top: 4px;
  }

  @media (max-width: 480px) {
    .login-card {
      padding: 8px;
      border-radius: 18px !important;
    }

    .logo-title {
      font-size: 1.4rem;
    }

    .login-form {
      gap: 16px;
    }
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
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
      rememberMe: [false]
    });
  }

  async submit(): Promise<void> {
    if (this.form.invalid) return;
    this.loading = true;
    this.cdr.markForCheck();
    
    const { email, password, rememberMe } = this.form.value;

    try {
      await this.auth.signIn(email, password, rememberMe);
      this.redirect();
    } catch (err: any) {
      this.loading = false;
      this.cdr.markForCheck();
      this.notify.error(err.message || 'Login failed');
    }
  }

  private redirect(): void {
    this.router.navigate([this.auth.getRole() === 'clinician' ? '/clinician' : '/patient']);
  }
}
