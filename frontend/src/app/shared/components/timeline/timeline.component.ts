import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, transition, style, animate, query } from '@angular/animations';

@Component({
  selector: 'app-timeline',
  standalone: true,
  imports: [CommonModule],
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
    <div class="timeline" [@list]="steps.length">
      <div class="step" *ngFor="let step of steps; let i = index; let last = last">
        <div class="line" *ngIf="!last"></div>
        <div class="dot" [class.dot--last]="last">{{ i + 1 }}</div>
        <p class="text">{{ step }}</p>
      </div>
    </div>
  `,
  styles: [`
    .timeline { display: flex; flex-direction: column; }
    .step { display: flex; align-items: flex-start; gap: 12px; position: relative; padding-bottom: 14px; }
    .line { position: absolute; left: 14px; top: 26px; width: 2px; height: calc(100% - 10px); background: linear-gradient(to bottom, #6366f1, transparent); }
    .dot { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: #6366f1; color: #fff; font-size: 0.72rem; font-weight: 700; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(99,102,241,0.4); z-index: 1; }
    .dot--last { background: #14b8a6; }
    .text { margin: 4px 0 0; font-size: 0.82rem; color: #94a3b8; line-height: 1.5; flex: 1; }
  `]
})
export class TimelineComponent {
  @Input() steps: string[] = [];
}
