import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';

export type NotifType = 'success' | 'error' | 'warning' | 'info';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  constructor(private snack: MatSnackBar) {}

  show(message: string, type: NotifType = 'info', duration = 4000): void {
    const cfg: MatSnackBarConfig = {
      duration,
      horizontalPosition: 'end',
      verticalPosition: 'top',
      panelClass: [`snack-${type}`]
    };
    this.snack.open(message, '✕', cfg);
  }

  success(m: string) { this.show(m, 'success'); }
  error(m: string)   { this.show(m, 'error', 6000); }
  warning(m: string) { this.show(m, 'warning'); }
  info(m: string)    { this.show(m, 'info'); }
}
