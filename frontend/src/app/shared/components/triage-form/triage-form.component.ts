import { Component, Output, EventEmitter, ChangeDetectionStrategy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { TriageRequest } from '../../../core/models/triage.models';

@Component({
  selector: 'app-triage-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()" class="triage-form">
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Patient ID</mat-label>
        <mat-icon matPrefix>badge</mat-icon>
        <input matInput formControlName="patient_id" placeholder="e.g. P12345" id="patientId">
        <mat-error *ngIf="form.get('patient_id')?.hasError('required')">Patient ID is required</mat-error>
      </mat-form-field>

      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Describe your symptoms</mat-label>
        <mat-icon matPrefix>medical_services</mat-icon>
        <textarea matInput formControlName="message" rows="5" id="symptoms"
          placeholder="e.g. I have been experiencing severe chest pain for the last hour…">
        </textarea>
        <mat-hint align="end">{{ form.get('message')?.value?.length || 0 }} / 2000</mat-hint>
        <mat-error *ngIf="form.get('message')?.hasError('required')">Please describe your symptoms</mat-error>
        <mat-error *ngIf="form.get('message')?.hasError('minlength')">Minimum 10 characters required</mat-error>
      </mat-form-field>

      <button mat-raised-button color="primary" type="submit" id="submitTriage"
              [disabled]="form.invalid || submitting" class="submit-btn">
        <mat-icon>{{ submitting ? 'hourglass_top' : 'send' }}</mat-icon>
        {{ submitting ? 'Analysing…' : 'Submit Triage' }}
      </button>
    </form>
  `,
  styles: [`
    .triage-form { display: flex; flex-direction: column; gap: 16px; padding: 8px 0; }
    .full-width { width: 100%; }
    .submit-btn { height: 48px; font-size: 1rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  `]
})
export class TriageFormComponent implements OnInit {
  @Output() submitted = new EventEmitter<TriageRequest>();

  form!: FormGroup;
  submitting = false;

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.form = this.fb.group({
      patient_id: ['', [Validators.required, Validators.maxLength(64)]],
      message:    ['', [Validators.required, Validators.minLength(10), Validators.maxLength(2000)]]
    });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.submitted.emit(this.form.value as TriageRequest);
  }

  setSubmitting(value: boolean): void {
    this.submitting = value;
    value ? this.form.disable() : this.form.enable();
  }
}
