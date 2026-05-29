import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-verify-otp-page',
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
      <mat-card class="auth-card">
        <div class="auth-header">
          <mat-icon class="auth-icon">verified_user</mat-icon>
          <h1 class="auth-title">Verify Email</h1>
          <p class="auth-sub">Enter the 6-digit code sent to {{ email || 'your email' }}</p>
        </div>

        <mat-card-content>
          <form [formGroup]="form" (ngSubmit)="submit()" class="auth-form">
            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Verification Code</mat-label>
              <mat-icon matPrefix>pin</mat-icon>
              <input matInput formControlName="token" type="text" maxlength="6" autocomplete="one-time-code">
            </mat-form-field>

            <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading" class="auth-btn">
              <mat-progress-spinner *ngIf="loading" mode="indeterminate" [diameter]="20" color="accent"></mat-progress-spinner>
              {{ loading ? 'Verifying…' : 'Verify' }}
            </button>
            
            <div class="auth-prompt">
              Didn't receive it? <a href="#" (click)="$event.preventDefault(); resendOtp()">Resend code</a>
            </div>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['../auth.shared.scss']
})
export class VerifyOtpPageComponent implements OnInit {
  form: FormGroup;
  loading = false;
  email = '';

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private notify: NotificationService,
    private cdr: ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      token: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      if (params['email']) {
        this.email = params['email'];
      }
      this.cdr.markForCheck();
    });
  }

  async submit(): Promise<void> {
    if (this.form.invalid || !this.email) return;
    this.loading = true;
    this.cdr.markForCheck();

    try {
      await this.auth.verifyOtp(this.email, this.form.value.token, 'signup');
      this.notify.success('Email verified successfully! You are now logged in.');
      this.router.navigate([this.auth.getRole() === 'clinician' ? '/clinician' : '/patient']);
    } catch (err: any) {
      this.loading = false;
      this.cdr.markForCheck();
      this.notify.error(err.message || 'Verification failed. Invalid or expired OTP.');
    }
  }

  async resendOtp(): Promise<void> {
    if (!this.email) {
      this.notify.error('Email is missing.');
      return;
    }
    // Note: Supabase has resend function, or we can just call signUp without password again if it's a magic link,
    // but the `resend` method in supabase-js v2 allows sending OTP again.
    // We'll just show a generic message or implement resend if needed.
    try {
      await this.auth.supabase.auth.resend({
        type: 'signup',
        email: this.email,
      });
      this.notify.success('Verification code resent.');
    } catch (err: any) {
      this.notify.error(err.message || 'Failed to resend code.');
    }
  }
}
