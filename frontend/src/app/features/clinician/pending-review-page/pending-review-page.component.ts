import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { trigger, transition, style, animate, query } from '@angular/animations';
import { interval, Subscription, startWith, switchMap, of } from 'rxjs';
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
          <mat-icon>pending_actions</mat-icon> HITL Review Queue
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
          <mat-card-header>
            <mat-icon mat-card-avatar>person_alert</mat-icon>
            <mat-card-title>{{ s.session_id | slice:0:8 }}…</mat-card-title>
            <mat-card-subtitle>{{ s.flow_status }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <app-severity-badge [level]="s.urgency_level" [score]="s.severity_score"></app-severity-badge>
            <p class="meta"><mat-icon inline>repeat</mat-icon> {{ s.iteration_count }} iterations</p>
          </mat-card-content>
          <mat-card-actions class="actions">
            <button mat-raised-button color="primary" (click)="approve(s.session_id)" [disabled]="busy[s.session_id]" id="approveBtn">
              <mat-icon>check</mat-icon> Approve
            </button>
            <button mat-stroked-button color="warn" (click)="reject(s.session_id)" [disabled]="busy[s.session_id]">
              <mat-icon>close</mat-icon> Reject
            </button>
          </mat-card-actions>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .page-container { padding: 24px; max-width: 1200px; margin: 0 auto; }
    .page-header { margin-bottom: 24px; }
    .page-title { display: flex; align-items: center; gap: 10px; font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0 0 6px; }
    .page-title mat-icon { color: #fb8c00; }
    .badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; color: #fff; font-size: 0.75rem; font-weight: 700; }
    .page-sub { color: #94a3b8; margin: 0; }
    .empty { text-align: center; padding: 60px 24px; color: #94a3b8; }
    .empty mat-icon { font-size: 60px; width: 60px; height: 60px; color: #10b981; display: block; margin: 0 auto 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
    .session-card { background: #111827 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-left: 4px solid #fb8c00 !important; border-radius: 16px !important; }
    .meta { margin: 10px 0 0; font-size: 0.8rem; color: #94a3b8; display: flex; align-items: center; gap: 4px; }
    .actions { display: flex; gap: 12px; padding: 8px 16px 16px; }
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
    // Poll every 10s — in production, call GET /sessions?requires_human_review=true
    this.sub = interval(10000).pipe(
      startWith(0),
      switchMap(() => of([] as SessionStatusResponse[]))
    ).subscribe(s => { this.sessions = s; this.cdr.markForCheck(); });
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
