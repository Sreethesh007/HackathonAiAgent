import { Component, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-reset-password-page',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="auth-wrapper">
      <div class="auth-bg"></div>
      <mat-card class="auth-card">
        <div class="auth-header">
          <mat-icon class="auth-icon">password</mat-icon>
          <h1 class="auth-title">Set New Password</h1>
          <p class="auth-sub">Enter your new password below</p>
        </div>

        <mat-card-content>
          <form [formGroup]="form" (ngSubmit)="submit()" class="auth-form">
            <mat-form-field appearance="outline" class="full-w">
              <mat-label>New Password</mat-label>
              <mat-icon matPrefix>lock</mat-icon>
              <input matInput [type]="hide ? 'password' : 'text'" formControlName="password">
              <button mat-icon-button matSuffix type="button" (click)="hide = !hide">
                <mat-icon>{{ hide ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
            </mat-form-field>

            <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading" class="auth-btn">
              <mat-progress-spinner *ngIf="loading" mode="indeterminate" [diameter]="20" color="accent"></mat-progress-spinner>
              {{ loading ? 'Saving…' : 'Update Password' }}
            </button>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['../auth.shared.scss']
})
export class ResetPasswordPageComponent {
  form: FormGroup;
  loading = false;
  hide = true;

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private notify: NotificationService,
    private cdr: ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  async submit(): Promise<void> {
    if (this.form.invalid) return;
    this.loading = true;
    this.cdr.markForCheck();

    try {
      await this.auth.updatePassword(this.form.value.password);
      this.notify.success('Password updated successfully! You can now log in.');
      this.router.navigate(['/login']);
    } catch (err: any) {
      this.loading = false;
      this.cdr.markForCheck();
      this.notify.error(err.message || 'Failed to update password.');
    }
  }
}
