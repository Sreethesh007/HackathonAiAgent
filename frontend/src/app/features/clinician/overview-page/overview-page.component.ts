import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { TriageApiService } from '../../../core/services/triage-api.service';
import { ChartCardComponent } from '../../../shared/components/chart-card/chart-card.component';
import { ChartData, ChartOptions } from 'chart.js';

@Component({
  selector: 'app-overview-page',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, ChartCardComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title"><mat-icon>dashboard</mat-icon> Clinician Overview</h2>
        <p class="page-sub">Real-time system health and triage activity.</p>
      </div>

      <div class="stat-grid">
        <mat-card class="stat-card" *ngFor="let s of stats">
          <mat-card-content class="stat-body">
            <mat-icon [style.color]="s.color" class="stat-icon">{{ s.icon }}</mat-icon>
            <div>
              <div class="stat-val">{{ s.value }}</div>
              <div class="stat-lbl">{{ s.label }}</div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <div class="chart-grid">
        <app-chart-card title="Urgency Distribution" icon="donut_large"
          type="doughnut" [data]="urgencyData" [options]="doughnutOpts">
        </app-chart-card>
        <app-chart-card title="Agent Latency (ms)" subtitle="Average per agent" icon="monitor_heart"
          type="bar" [data]="latencyData" [options]="barOpts">
        </app-chart-card>
      </div>
    </div>
  `,
  styles: [`
    .page-container { padding: 24px; max-width: 1200px; margin: 0 auto; }
    .page-header { margin-bottom: 24px; }
    .page-title { display: flex; align-items: center; gap: 10px; font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0 0 6px; }
    .page-title mat-icon { color: #14b8a6; }
    .page-sub { color: #94a3b8; margin: 0; }
    .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .stat-card { background: #111827 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; }
    .stat-body { display: flex; align-items: center; gap: 14px; padding: 18px 14px; }
    .stat-icon { font-size: 34px; width: 34px; height: 34px; }
    .stat-val { font-size: 1.6rem; font-weight: 700; color: #f1f5f9; line-height: 1; }
    .stat-lbl { font-size: 0.78rem; color: #94a3b8; margin-top: 4px; }
    .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    @media (max-width: 768px) { .chart-grid { grid-template-columns: 1fr; } }
  `]
})
export class OverviewPageComponent implements OnInit {
  stats = [
    { label: 'Pipeline',    value: '…', icon: 'hub',       color: '#6366f1' },
    { label: 'LLM Model',   value: '…', icon: 'smart_toy', color: '#14b8a6' },
    { label: 'Environment', value: '…', icon: 'cloud',     color: '#f59e0b' },
    { label: 'Uptime',      value: '…', icon: 'timer',     color: '#10b981' }
  ];

  urgencyData: ChartData = {
    labels: ['Emergency', 'Urgent', 'Routine', 'Low'],
    datasets: [{ data: [15, 25, 45, 15], backgroundColor: ['#e53935','#fb8c00','#43a047','#1e88e5'] }]
  };

  latencyData: ChartData = {
    labels: ['Triage', 'Research', 'Critic', 'Scheduler', 'Synthesizer'],
    datasets: [{
      label: 'Avg ms', data: [120, 450, 80, 95, 60],
      backgroundColor: 'rgba(99,102,241,0.7)', borderColor: '#6366f1',
      borderWidth: 2, borderRadius: 6
    }]
  };

  doughnutOpts: ChartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } };
  barOpts: ChartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } };

  constructor(private api: TriageApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.api.healthCheck().subscribe({
      next: h => {
        this.stats[0].value = h.pipeline_ready ? '✅ Ready' : '❌ Down';
        this.stats[1].value = h.llm_model || 'Unknown';
        this.stats[2].value = h.environment || 'N/A';
        this.stats[3].value = `${Math.floor(h.uptime_seconds / 60)}m`;
        this.cdr.markForCheck();
      },
      error: () => { /* backend might be down, show defaults */ }
    });
  }
}
