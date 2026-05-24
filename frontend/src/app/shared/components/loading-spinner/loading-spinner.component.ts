import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="overlay" *ngIf="loading">
      <div class="box">
        <mat-progress-spinner mode="indeterminate" [diameter]="52" color="accent"></mat-progress-spinner>
        <p class="msg">{{ message }}</p>
      </div>
    </div>
  `,
  styles: [`
    .overlay {
      position: fixed; inset: 0;
      background: rgba(10,14,26,0.75);
      backdrop-filter: blur(5px);
      display: flex; align-items: center; justify-content: center;
      z-index: 9999;
    }
    .box {
      display: flex; flex-direction: column; align-items: center; gap: 16px;
      padding: 32px 48px;
      background: #111827;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    }
    .msg { margin: 0; color: #94a3b8; font-size: 0.9rem; }
  `]
})
export class LoadingSpinnerComponent {
  @Input() loading = false;
  @Input() message = 'Analysing symptoms…';
}
