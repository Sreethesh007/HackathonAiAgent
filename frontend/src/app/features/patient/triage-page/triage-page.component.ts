import { Component, ChangeDetectionStrategy, ChangeDetectorRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { trigger, transition, style, animate } from '@angular/animations';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';
import { TriageApiService } from '../../../core/services/triage-api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { TriageRequest, TriageResponse } from '../../../core/models/triage.models';
import { TriageFormComponent } from '../../../shared/components/triage-form/triage-form.component';
import { SeverityBadgeComponent } from '../../../shared/components/severity-badge/severity-badge.component';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner/loading-spinner.component';
import { TimelineComponent } from '../../../shared/components/timeline/timeline.component';

@Component({
  selector: 'app-triage-page',
  standalone: true,
  imports: [
    CommonModule, MatCardModule, MatChipsModule, MatIconModule,
    TriageFormComponent, SeverityBadgeComponent,
    LoadingSpinnerComponent, TimelineComponent
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('cardIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.96) translateY(8px)' }),
        animate('320ms cubic-bezier(0.4,0,0.2,1)', style({ opacity: 1, transform: 'scale(1) translateY(0)' }))
      ])
    ])
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title"><mat-icon>medical_services</mat-icon> Symptom Triage</h2>
        <p class="page-sub">Describe your symptoms and our AI agents will assess urgency.</p>
      </div>

      <div class="triage-layout">
        <mat-card class="panel">
          <mat-card-header><mat-card-title>Describe Your Symptoms</mat-card-title></mat-card-header>
          <mat-card-content>
            <app-triage-form #triageForm (submitted)="onSubmit($event)"></app-triage-form>
          </mat-card-content>
        </mat-card>

        <div class="result-panel" *ngIf="result" [@cardIn]>
          <mat-card class="panel">
            <mat-card-content class="sev-content">
              <app-severity-badge [level]="result.urgency_level" [score]="result.severity_score"></app-severity-badge>
              <p class="concern">{{ result.primary_concern }}</p>
            </mat-card-content>
          </mat-card>

          <mat-card class="panel">
            <mat-card-header>
              <mat-icon mat-card-avatar>smart_toy</mat-icon>
              <mat-card-title>Clinical Assessment</mat-card-title>
              <mat-card-subtitle>Quality: {{ (result.quality_score * 100) | number:'1.0-0' }}%</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content><p class="resp-text">{{ result.response }}</p></mat-card-content>
          </mat-card>

          <mat-card class="panel review-card" *ngIf="result.requires_human_review">
            <mat-card-content class="review-content">
              <mat-icon class="pulse">pending</mat-icon>
              <div>
                <strong>Under Clinical Review</strong>
                <p style="margin:4px 0 0">A clinician is reviewing your case. We'll update you shortly.</p>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="panel appt-card" *ngIf="result.appointment_booked">
            <mat-card-header>
              <mat-icon mat-card-avatar>event_available</mat-icon>
              <mat-card-title>Appointment Booked</mat-card-title>
              <mat-card-subtitle>{{ result.appointment_datetime | date:'full' }}</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <p><mat-icon inline>person</mat-icon> {{ result.appointment_provider }}</p>
              <p><mat-icon inline>confirmation_number</mat-icon> {{ result.appointment_id }}</p>
            </mat-card-content>
          </mat-card>

          <mat-card class="panel" *ngIf="result.guidelines_applied.length">
            <mat-card-header><mat-card-title>Guidelines Applied</mat-card-title></mat-card-header>
            <mat-card-content>
              <mat-chip-set>
                <mat-chip *ngFor="let g of result.guidelines_applied">{{ g }}</mat-chip>
              </mat-chip-set>
            </mat-card-content>
          </mat-card>

          <mat-card class="panel" *ngIf="result.reasoning_trace.length">
            <mat-card-header>
              <mat-card-title>Agent Reasoning</mat-card-title>
              <mat-card-subtitle>{{ result.iteration_count }} iteration(s)</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <app-timeline [steps]="result.reasoning_trace"></app-timeline>
            </mat-card-content>
          </mat-card>
        </div>
      </div>
    </div>
    <app-loading-spinner [loading]="loading" message="AI agents analysing symptoms…"></app-loading-spinner>
  `,
  styles: [`
    .page-container { padding: 24px; max-width: 1200px; margin: 0 auto; }
    .page-header { margin-bottom: 24px; }
    .page-title { display: flex; align-items: center; gap: 10px; font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0 0 6px; }
    .page-title mat-icon { color: #6366f1; }
    .page-sub { color: #94a3b8; margin: 0; }
    .triage-layout { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 24px; align-items: start; }
    @media (max-width: 768px) { .triage-layout { grid-template-columns: 1fr; } }
    .panel { background: #111827 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; }
    .result-panel { display: flex; flex-direction: column; gap: 16px; }
    .sev-content { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
    .concern { margin: 0; font-size: 1rem; font-weight: 500; color: #f1f5f9; }
    .resp-text { line-height: 1.7; color: #94a3b8; white-space: pre-line; }
    .review-content { display: flex; align-items: center; gap: 14px; background: rgba(251,140,0,0.08); border-radius: 8px; padding: 14px; }
    .pulse { color: #fb8c00; animation: pulse 1.5s infinite; font-size: 30px; width: 30px; height: 30px; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }
    .appt-card { border-left: 4px solid #14b8a6 !important; }
  `]
})
export class TriagePageComponent {
  @ViewChild('triageForm') triageForm!: TriageFormComponent;
  loading = false;
  result: TriageResponse | null = null;
  private poll?: Subscription;

  constructor(
    private api: TriageApiService,
    private notify: NotificationService,
    private cdr: ChangeDetectorRef
  ) {}

  onSubmit(req: TriageRequest): void {
    this.loading = true;
    this.result = null;
    this.triageForm?.setSubmitting(true);
    this.cdr.markForCheck();

    this.api.startTriage(req).subscribe({
      next: res => {
        this.result = res;
        this.loading = false;
        this.triageForm?.setSubmitting(false);
        this.cdr.markForCheck();
        res.urgency_level === 'emergency'
          ? this.notify.error('⚠️ EMERGENCY — Call 911 immediately!')
          : this.notify.success('Triage complete!');
        if (res.requires_human_review) this.startPoll(res.session_id);
      },
      error: err => {
        this.loading = false;
        this.triageForm?.setSubmitting(false);
        this.cdr.markForCheck();
        this.notify.error(err?.error?.detail ?? 'Triage failed. Please retry.');
      }
    });
  }

  private startPoll(sid: string): void {
    this.poll?.unsubscribe();
    this.poll = interval(10000).pipe(
      switchMap(() => this.api.getSessionStatus(sid)),
      takeWhile(s => s.requires_human_review, true)
    ).subscribe(s => {
      if (!s.requires_human_review && this.result) {
        this.result = { ...this.result, requires_human_review: false };
        this.cdr.markForCheck();
        this.notify.success('Your case has been reviewed by a clinician!');
      }
    });
  }
}
