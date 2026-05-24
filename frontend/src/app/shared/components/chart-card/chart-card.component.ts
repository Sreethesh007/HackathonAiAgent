import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { BaseChartDirective } from 'ng2-charts';
import { ChartData, ChartOptions, ChartType } from 'chart.js';

@Component({
  selector: 'app-chart-card',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, BaseChartDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-card class="chart-card">
      <mat-card-header>
        <mat-icon mat-card-avatar>{{ icon }}</mat-icon>
        <mat-card-title>{{ title }}</mat-card-title>
        <mat-card-subtitle *ngIf="subtitle">{{ subtitle }}</mat-card-subtitle>
      </mat-card-header>
      <mat-card-content class="chart-content">
        <canvas baseChart [type]="type" [data]="data" [options]="options"></canvas>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`.chart-card{height:100%} .chart-content{padding:16px;height:240px;position:relative} canvas{max-height:220px !important}`]
})
export class ChartCardComponent {
  @Input() title = '';
  @Input() subtitle = '';
  @Input() icon = 'bar_chart';
  @Input() type: ChartType = 'doughnut';
  @Input() data: ChartData = { labels: [], datasets: [] };
  @Input() options: ChartOptions = { responsive: true, maintainAspectRatio: false };
}
