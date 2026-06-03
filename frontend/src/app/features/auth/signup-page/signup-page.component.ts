import { Component, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-signup-page',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule,
    MatSelectModule
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
          <mat-icon class="auth-icon">person_add</mat-icon>
          <h1 class="auth-title">Create Account</h1>
          <p class="auth-sub">Register as a new patient</p>
        </div>

        <mat-card-content>
          <form [formGroup]="form" (ngSubmit)="submit()" class="auth-form">
            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Email</mat-label>
              <mat-icon matPrefix>email</mat-icon>
              <input matInput formControlName="email" type="email" autocomplete="email">
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Password</mat-label>
              <mat-icon matPrefix>lock</mat-icon>
              <input matInput [type]="hide ? 'password' : 'text'" formControlName="password">
              <button mat-icon-button matSuffix type="button" (click)="hide = !hide">
                <mat-icon>{{ hide ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-w">
              <mat-label>Full Name</mat-label>
              <mat-icon matPrefix>badge</mat-icon>
              <input matInput formControlName="name">
            </mat-form-field>

            <div class="row">
              <mat-form-field appearance="outline" class="half-w">
                <mat-label>Age</mat-label>
                <input matInput formControlName="age" type="number">
              </mat-form-field>

              <mat-form-field appearance="outline" class="half-w">
                <mat-label>Gender</mat-label>
                <mat-select formControlName="gender">
                  <mat-option value="male">Male</mat-option>
                  <mat-option value="female">Female</mat-option>
                  <mat-option value="other">Other</mat-option>
                </mat-select>
              </mat-form-field>
            </div>

            <div class="row">
              <mat-form-field appearance="outline" class="half-w">
                <mat-label>Weight (kg)</mat-label>
                <input matInput formControlName="weight" type="number">
              </mat-form-field>

              <mat-form-field appearance="outline" class="half-w">
                <mat-label>Height (cm)</mat-label>
                <input matInput formControlName="height" type="number">
              </mat-form-field>
            </div>

            <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading" class="auth-btn">
              <mat-progress-spinner *ngIf="loading" mode="indeterminate" [diameter]="20" color="accent"></mat-progress-spinner>
              {{ loading ? 'Creating Account…' : 'Sign Up' }}
            </button>
            
            <div class="auth-prompt">
              Already have an account? <a routerLink="/login">Log in</a>
            </div>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['../auth.shared.scss']
})
export class SignupPageComponent {
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
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      name: ['', Validators.required],
      age: ['', [Validators.required, Validators.min(0)]],
      gender: ['', Validators.required],
      weight: [''],
      height: ['']
    });
  }

  async submit(): Promise<void> {
    if (this.form.invalid) return;
    this.loading = true;
    this.cdr.markForCheck();

    const { email, password, name, age, gender, weight, height } = this.form.value;
    
    try {
      await this.auth.signUp(email, password, { 
        name, age, gender, weight, height, role: 'patient' 
      });
      this.notify.success('Check your email for the confirmation link');
      this.router.navigate(['/login']);
    } catch (err: any) {
      this.loading = false;
      this.cdr.markForCheck();
      this.notify.error(err.message || 'Signup failed');
    }
  }
}
