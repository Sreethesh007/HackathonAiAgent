import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { UrgencyLevel, URGENCY_CONFIG } from '../../../core/models/triage.models';

@Component({
  selector: 'app-severity-badge',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="badge" [style.background-color]="cfg.color">
      <mat-icon class="badge-icon">{{ cfg.icon }}</mat-icon>
      <span class="badge-label">{{ cfg.label }}</span>
      <span class="badge-score" *ngIf="score !== null">&middot; {{ score }}/10</span>
    </span>
  `,
  styles: [`
    .badge {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 14px; border-radius: 20px;
      color: #fff; font-weight: 700; font-size: 0.78rem;
      letter-spacing: 0.06em; text-transform: uppercase;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    .badge-icon { font-size: 15px; height: 15px; width: 15px; }
    .badge-score { opacity: 0.85; font-weight: 400; }
  `]
})
export class SeverityBadgeComponent {
  @Input() level: UrgencyLevel = 'unknown';
  @Input() score: number | null = null;
  get cfg() { return URGENCY_CONFIG[this.level] ?? URGENCY_CONFIG['unknown']; }
}
