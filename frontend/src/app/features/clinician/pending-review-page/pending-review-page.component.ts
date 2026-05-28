import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { trigger, transition, style, animate, query } from '@angular/animations';
import { interval, Subscription, startWith, switchMap } from 'rxjs';
import { TriageApiService } from '../../../core/services/triage-api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { SeverityBadgeComponent } from '../../../shared/components/severity-badge/severity-badge.component';
import { SessionStatusResponse } from '../../../core/models/triage.models';

@Component({
  selector: 'app-pending-review-page',
  standalone: true,
  imports: [
    CommonModule, MatCardModule, MatButtonModule,
    MatIconModule, MatBadgeModule, SeverityBadgeComponent
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('list', [
      transition('* => *', [
        query(':enter', [
          style({ opacity: 0, transform: 'translateY(10px)' }),
          animate('280ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
        ], { optional: true })
      ])
    ])
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title">
          <mat-icon>pending_actions</mat-icon> Approval Queue
          <span class="badge" *ngIf="sessions.length" [style.background]="'#e53935'">{{ sessions.length }}</span>
        </h2>
        <p class="page-sub">Sessions awaiting human clinical review. Auto-refreshes every 10s.</p>
      </div>

      <div class="empty" *ngIf="!sessions.length">
        <mat-icon>check_circle</mat-icon>
        <h3>All Clear!</h3>
        <p>No sessions currently require human review.</p>
      </div>

      <div class="grid" [@list]="sessions.length">
        <mat-card class="session-card" *ngFor="let s of sessions">
          <div class="top-row">
            <app-severity-badge [level]="s.urgency_level || 'unknown'" [score]="s.severity_score ?? null"></app-severity-badge>
          </div>
          <mat-card-header>
            <mat-card-title>
              {{ s.patient_name || 'Unknown patient' }}
              <span class="header-age">&nbsp;·&nbsp;{{ s.patient_age ? (s.patient_age + ' yrs') : 'Age unknown' }}</span>
            </mat-card-title>
            <mat-card-subtitle>{{ s.primary_concern || 'No concern available' }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <div class="patient-meta">
              <span class="status-pill">{{ s.flow_status }}</span>
            </div>
            <p class="concern"><strong>AI recommendation</strong></p>
            <p class="response">{{ s.final_response || 'No clinician-facing recommendation available.' }}</p>
          </mat-card-content>
          <mat-card-actions class="actions">
            <button mat-raised-button class="btn-approve" (click)="approve(s.session_id)" [disabled]="busy[s.session_id]" id="approveBtn">
              <mat-icon>check</mat-icon> Approve
            </button>
            <button mat-stroked-button class="btn-reject" (click)="reject(s.session_id)" [disabled]="busy[s.session_id]">
              <mat-icon>close</mat-icon> Reject
            </button>
          </mat-card-actions>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .page-container { padding: 28px 24px; max-width: 1200px; margin: 0 auto; }
    
    .page-header { margin-bottom: 24px; }
    
    .page-title { 
      display: flex; 
      align-items: center; 
      gap: 10px; 
      font-size: 1.4rem; 
      font-weight: 700; 
      color: #f1f5f9; 
      margin: 0 0 5px; 
    }
    
    .page-title mat-icon { color: #14b8a6; font-size: 22px; }
    
    .badge { 
      display: inline-flex; 
      align-items: center; 
      justify-content: center; 
      width: 24px; 
      height: 24px; 
      border-radius: 50%; 
      background: #ef4444;
      color: #fff; 
      font-size: 0.7rem; 
      font-weight: 700;
      margin-left: 8px;
    }
    
    .page-sub { color: #64748b; margin: 0; font-size: 13px; }
    
    /* Empty State */
    .empty { 
      text-align: center; 
      padding: 80px 24px; 
      color: #94a3b8; 
    }
    
    .empty mat-icon { 
      font-size: 64px; 
      width: 64px; 
      height: 64px; 
      color: #14b8a6; 
      display: block; 
      margin: 0 auto 16px;
      opacity: 0.8;
    }
    
    .empty h3 {
      font-size: 18px;
      font-weight: 600;
      color: #f1f5f9;
      margin: 0 0 8px;
    }
    
    .empty p {
      font-size: 14px;
      color: #64748b;
      margin: 0;
    }
    
    /* Grid */
    .grid { 
      display: grid; 
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); 
      gap: 20px; 
    }
    
    /* Session Card (light) */
    .session-card { 
      background: #ffffff !important; 
      border: 1px solid rgba(15,23,42,0.06) !important; 
      border-left: 4px solid rgba(15,23,42,0.04) !important; 
      border-radius: 12px !important;
      box-shadow: 0 4px 24px rgba(0,0,0,0.18) !important;
      overflow: hidden;
      transition: all 180ms ease;
      color: #0f1724;
    }
    
    .session-card:hover {
      border-left-color: rgba(15,23,42,0.08) !important;
      box-shadow: 0 6px 32px rgba(0,0,0,0.22) !important;
    }

    /* Force all text inside the session card to dark tones to match white-card aesthetic */
    .session-card, .session-card * {
      color: #0f1724 !important;
    }

    .patient-meta {
      margin: 8px 0 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: #0f1724;
      font-size: 13px;
      align-items: center;
    }

    .top-row { padding: 12px 16px 0; display: flex; align-items: center; gap: 12px; }

    .patient-meta span { display: inline-flex; align-items: center; }

    .divider { opacity: 0.45; }

    .status-pill {
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(20, 184, 166, 0.12);
      color: #a7f3d0;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }

    .concern {
      margin: 0 0 4px;
      font-size: 13px;
      color: #475569;
    }

    .response {
      margin: 0;
      color: #0f1724;
      font-size: 14px;
      line-height: 1.6;
      max-height: 6.5em;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      -webkit-box-orient: vertical;
    }
    
    ::ng-deep .session-card .mat-mdc-card-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      background: transparent;
      border-bottom: 1px solid rgba(15,23,42,0.04);
    }
    
    ::ng-deep .session-card .mat-mdc-card-header-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    
    ::ng-deep .session-card .mat-mdc-card-avatar {
      color: #14b8a6;
      font-size: 24px;
      width: 24px;
      height: 24px;
      background: rgba(20, 184, 166, 0.1);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0;
    }
    
    ::ng-deep .session-card .mat-mdc-card-title {
      font-size: 18px;
      font-weight: 700;
      color: #0f1724;
      margin: 0;
      letter-spacing: 0.3px;
      font-family: 'Monaco', 'Courier New', monospace;
    }

    .header-age { font-weight: 500; color: #475569; font-size: 14px; }
    
    ::ng-deep .session-card .mat-mdc-card-subtitle {
      font-size: 12px;
      color: #475569;
      margin: 0;
      text-transform: capitalize;
    }
    
    /* Card Content */
    ::ng-deep .session-card .mat-mdc-card-content {
      padding: 16px;
    }
    
    .meta { 
      margin: 12px 0 0; 
      font-size: 13px; 
      color: #94a3b8; 
      display: flex; 
      align-items: center; 
      gap: 6px;
      font-weight: 500;
    }
    
    .meta mat-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
    }
    
    /* Card Actions */
    .actions { 
      display: flex; 
      gap: 10px; 
      padding: 12px 16px 16px;
      border-top: 1px solid rgba(15,23,42,0.04);
    }
    
    /* Buttons */
    .btn-approve, .btn-reject {
      flex: 1;
      height: 36px;
      font-size: 13px;
      font-weight: 600;
      border-radius: 8px;
      transition: all 180ms ease;
    }
    
    .btn-approve {
      background: #14b8a6 !important;
      color: #111827 !important;
    }
    
    .btn-approve:hover:not(:disabled) {
      background: #0d9488 !important;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25) !important;
    }
    
    .btn-approve:disabled {
      background: rgba(20, 184, 166, 0.3) !important;
      color: rgba(17, 24, 39, 0.5) !important;
    }
    
    .btn-reject {
      border: 1.5px solid rgba(239, 68, 68, 0.4) !important;
      color: #ef4444 !important;
      background: rgba(239, 68, 68, 0.08) !important;
    }
    
    .btn-reject:hover:not(:disabled) {
      border-color: #ef4444 !important;
      color: #ffffff !important;
      background: #ef4444 !important;
    }
    
    .btn-reject:disabled {
      border-color: rgba(255,255,255,0.1) !important;
      color: rgba(255,255,255,0.3) !important;
      background: transparent !important;
    }
    
    .btn-approve mat-icon, .btn-reject mat-icon {
      margin-right: 6px;
      font-size: 18px;
      width: 18px;
      height: 18px;
    }
  `]
})
export class PendingReviewPageComponent implements OnInit, OnDestroy {
  sessions: SessionStatusResponse[] = [];
  busy: Record<string, boolean> = {};
  private sub?: Subscription;

  constructor(
    private api: TriageApiService,
    private notify: NotificationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Poll every 10s — calls GET /clinician/pending
    this.sub = interval(10000).pipe(
      startWith(0),
      switchMap(() => this.api.getPendingReviews())
    ).subscribe({
      next: (res) => {
        this.sessions = res.sessions || [];
        this.cdr.markForCheck();
      },
      error: () => {
        // Silently fail on polling errors (auth may not be set up for clinician role)
        this.sessions = [];
        this.cdr.markForCheck();
      }
    });
  }

  approve(id: string): void { this.decide(id, true); }
  reject(id: string):  void { this.decide(id, false); }

  private decide(id: string, approval: boolean): void {
    this.busy[id] = true;
    this.cdr.markForCheck();
    this.api.continueTriage(id, { human_approval: approval }).subscribe({
      next: () => {
        approval ? this.notify.success('Session approved.') : this.notify.warning('Session rejected.');
        this.sessions = this.sessions.filter(s => s.session_id !== id);
        delete this.busy[id];
        this.cdr.markForCheck();
      },
      error: () => {
        this.notify.error('Action failed.');
        delete this.busy[id];
        this.cdr.markForCheck();
      }
    });
  }

  ngOnDestroy(): void { this.sub?.unsubscribe(); }
}
