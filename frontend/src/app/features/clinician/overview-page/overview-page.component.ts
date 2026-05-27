import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
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
        <h2 class="page-title"><mat-icon>dashboard</mat-icon> Clinician Overview</h2>
        <p class="page-sub">Real-time triage queue and appointment stats.</p>
      </div>

      <div class="stat-grid">
        <mat-card class="stat-card u-hover-lift" appFadeIn tabindex="0" aria-label="Pending Reviews">
          <mat-card-content class="stat-body">
            <mat-icon style="color: #f59e0b;" class="stat-icon" aria-hidden="true">pending_actions</mat-icon>
            <div>
              <div class="stat-val">{{ pendingCount }}</div>
              <div class="stat-lbl">Pending HITL Reviews</div>
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="stat-card u-hover-lift" appFadeIn tabindex="0" aria-label="Total Appointments">
          <mat-card-content class="stat-body">
            <mat-icon style="color: #10b981;" class="stat-icon" aria-hidden="true">event_available</mat-icon>
            <div>
              <div class="stat-val">{{ appointmentsCount }}</div>
              <div class="stat-lbl">Total Appointments</div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <div class="info-section" appFadeIn>
        <mat-card class="info-card">
          <mat-card-content>
            <h3><mat-icon>info</mat-icon> Getting Started</h3>
            <p>Welcome to the new clinician dashboard.</p>
            <ul>
              <li><strong>HITL Queue:</strong> Review and approve AI-generated triage responses before they reach the patient.</li>
              <li><strong>Appointments:</strong> View details of patients who have successfully booked a slot.</li>
            </ul>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .page-container { padding: 24px; max-width: 1200px; margin: 0 auto; }
    .page-header { margin-bottom: 24px; }
    .page-title { display: flex; align-items: center; gap: 10px; font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0 0 6px; }
    .page-title mat-icon { color: #14b8a6; }
    .page-sub { color: #94a3b8; margin: 0; }
    .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: #111827 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; }
    .stat-body { display: flex; align-items: center; gap: 14px; padding: 18px 14px; }
    .stat-icon { font-size: 34px; width: 34px; height: 34px; }
    .stat-val { font-size: 2rem; font-weight: 700; color: #f1f5f9; line-height: 1; }
    .stat-lbl { font-size: 0.9rem; color: #94a3b8; margin-top: 4px; }
    
    .info-section { margin-top: 24px; }
    .info-card { background: #111827 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; color: #cbd5e1; }
    .info-card h3 { display: flex; align-items: center; gap: 8px; color: #e2e8f0; margin-top: 0; }
    .info-card h3 mat-icon { color: #3b82f6; }
    .info-card p { font-size: 0.95rem; line-height: 1.5; }
    .info-card ul { margin: 12px 0 0 20px; padding: 0; line-height: 1.6; }
    .info-card li { margin-bottom: 8px; }
  `]
})
export class OverviewPageComponent implements OnInit, OnDestroy {
  pendingCount = 0;
  appointmentsCount = 0;
  private pollTimer: any;

  constructor(private api: TriageApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.fetchData();
    this.pollTimer = setInterval(() => this.fetchData(), 10000);
  }

  ngOnDestroy(): void {
    if (this.pollTimer) clearInterval(this.pollTimer);
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
}
