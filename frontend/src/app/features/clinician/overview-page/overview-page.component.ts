import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';
import { TriageApiService } from '../../../core/services/triage-api.service';
import { FadeInDirective } from '../../../shared/directives/fade-in.directive';

@Component({
  selector: 'app-overview-page',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, FadeInDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title"><mat-icon>dashboard</mat-icon> Dashboard</h2>
        <p class="page-sub">Real-time triage queue and appointment stats.</p>
      </div>

      <div class="stat-grid">

        <mat-card class="stat-card u-hover-lift" appFadeIn tabindex="0" (click)="navigateToPending()" role="button">
          <mat-card-content class="stat-body">
            <div class="stat-icon-wrap warn">
              <mat-icon>task_alt</mat-icon>
            </div>
            <div class="stat-text">
              <div class="stat-val">{{ pendingCount }}</div>
              <div class="stat-lbl">Pending Approvals</div>
            </div>
            @if (pendingCount > 0) {
              <span class="stat-badge">Action needed</span>
            }
          </mat-card-content>
        </mat-card>

        <mat-card class="stat-card u-hover-lift" appFadeIn tabindex="0" (click)="navigateToAppointments()" role="button">
          <mat-card-content class="stat-body">
            <div class="stat-icon-wrap success">
              <mat-icon>calendar_month</mat-icon>
            </div>
            <div class="stat-text">
              <div class="stat-val">{{ appointmentsCount }}</div>
              <div class="stat-lbl">Total Appointments</div>
            </div>
          </mat-card-content>
        </mat-card>

      </div>

      <div class="info-section" appFadeIn>
        <mat-card class="info-card">
          <mat-card-content>
            <p>Welcome to the Triage Admin dashboard.</p>
            <ul>
              <li><strong>Approvals:</strong> Review and approve AI-generated triage responses before they reach patients.</li>
              <li><strong>Appointments:</strong> View details of patients who have successfully booked a slot.</li>
            </ul>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .page-container { padding: 28px 24px; max-width: 1200px; margin: 0 auto; }

    .page-header { margin-bottom: 24px; }
    .page-title {
      display: flex; align-items: center; gap: 10px;
      font-size: 1.4rem; font-weight: 700; color: #f1f5f9; margin: 0 0 5px;
    }
    .page-title mat-icon { color: #14b8a6; font-size: 22px; }
    .page-sub { color: #64748b; margin: 0; font-size: 13px; }

    /* Stat grid */
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: #111827 !important;
      border: 1px solid rgba(255,255,255,0.07) !important;
      border-radius: 12px !important;
      box-shadow: 0 4px 24px rgba(0,0,0,0.25) !important;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .stat-card:hover {
      border-color: rgba(255,255,255,0.15) !important;
      box-shadow: 0 6px 32px rgba(0,0,0,0.35) !important;
      transform: translateY(-2px);
    }
    .stat-card:focus-visible {
      outline: 2px solid #14b8a6;
      outline-offset: 2px;
    }
    .stat-body {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px 18px !important;
    }
    .stat-icon-wrap {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .stat-icon-wrap.warn {
      background: rgba(245,158,11,0.12);
      border: 1px solid rgba(245,158,11,0.2);
    }
    .stat-icon-wrap.warn mat-icon { color: #f59e0b; }
    .stat-icon-wrap.success {
      background: rgba(16,185,129,0.12);
      border: 1px solid rgba(16,185,129,0.2);
    }
    .stat-icon-wrap.success mat-icon { color: #10b981; }
    .stat-icon-wrap mat-icon { font-size: 22px; width: 22px; height: 22px; }

    .stat-text { flex: 1; min-width: 0; }
    .stat-val { font-size: 2rem; font-weight: 700; color: #212121; line-height: 1; }
    .stat-lbl { font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.4px; font-weight: 500; }

    .stat-badge {
      font-size: 10px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 20px;
      background: rgba(239,68,68,0.12);
      color: #f87171;
      border: 1px solid rgba(239,68,68,0.2);
      white-space: nowrap;
      letter-spacing: 0.3px;
      text-transform: uppercase;
    }

    /* Info card */
    .info-section { margin-top: 8px; }
    .info-card {
      background: #111827 !important;
      border: 1px solid rgba(255,255,255,0.07) !important;
      border-radius: 12px !important;
      color: #94a3b8;
    }
    .info-card h3 {
      display: flex; align-items: center; gap: 8px;
      color: #212121; margin: 0 0 10px; font-size: 15px;
    }
    .info-card h3 mat-icon { color: #3b82f6; font-size: 18px; }
    .info-card p { font-size: 15px; line-height: 1.6; margin: 0 0 10px; color: #212121; }
    .info-card ul { margin: 0; padding-left: 18px; line-height: 1.7; }
    .info-card li { margin-bottom: 6px; font-size: 13.5px; color: #212121; }
    .info-card strong { color: #212121; }
  `]
})
export class OverviewPageComponent implements OnInit, OnDestroy {
  pendingCount = 0;
  appointmentsCount = 0;
  private pollTimer: any;

  constructor(private api: TriageApiService, private cdr: ChangeDetectorRef, private router: Router) {}

  ngOnInit(): void {
    this.fetchData();
    this.pollTimer = setInterval(() => this.fetchData(), 10000);
  }

  ngOnDestroy(): void {
    clearInterval(this.pollTimer);
  }

  fetchData() {
    this.api.getPendingReviews().subscribe({
      next: (res: any) => {
        this.pendingCount = (res.sessions || []).length;
        this.cdr.markForCheck();
      }
    });
    this.api.getAppointments().subscribe({
      next: (res: any) => {
        this.appointmentsCount = (res.appointments || []).length;
        this.cdr.markForCheck();
      }
    });
  }

  navigateToPending(): void {
    this.router.navigate(['clinician', 'pending']);
  }

  navigateToAppointments(): void {
    this.router.navigate(['clinician', 'appointments']);
  }
}