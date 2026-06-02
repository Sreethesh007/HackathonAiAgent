import { Component, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-forgot-password-page',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="auth-wrapper">
      <div class="auth-bg"></div>
      <a routerLink="/" class="auth-home-btn" aria-label="Back to home" title="Back to home">
        <mat-icon>local_hospital</mat-icon>
      </a>
      <mat-card class="auth-card">
        <div class="auth-header">
          <mat-icon class="auth-icon">lock_reset</mat-icon>
          <h1 class="auth-title">Forgot Password</h1>
          <p class="auth-sub">Enter your email to receive a reset link</p>
        </div>

        <mat-card-content>
          <form [formGroup]="form" (ngSubmit)="submit()" class="auth-form">
            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Email</mat-label>
              <mat-icon matPrefix>email</mat-icon>
              <input matInput formControlName="email" type="email" autocomplete="email">
            </mat-form-field>

            <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading" class="auth-btn">
              <mat-progress-spinner *ngIf="loading" mode="indeterminate" [diameter]="20" color="accent"></mat-progress-spinner>
              {{ loading ? 'Sending…' : 'Send Reset Link' }}
            </button>
            
            <div class="auth-prompt">
              Remember your password? <a routerLink="/login">Log in</a>
            </div>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['../auth.shared.scss']
})
export class ForgotPasswordPageComponent {
  form: FormGroup;
  loading = false;

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private notify: NotificationService,
    private cdr: ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  async submit(): Promise<void> {
    if (this.form.invalid) return;
    this.loading = true;
    this.cdr.markForCheck();

    try {
      await this.auth.resetPasswordForEmail(this.form.value.email);
      this.notify.success('Password reset link sent! Please check your email.');
      this.router.navigate(['/login']);
    } catch (err: any) {
      this.loading = false;
      this.cdr.markForCheck();
      this.notify.error(err.message || 'Failed to send reset link.');
    }
  }
}
