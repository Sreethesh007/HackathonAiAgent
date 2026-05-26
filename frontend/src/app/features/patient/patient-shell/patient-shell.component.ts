import { Component, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-patient-shell',
  standalone: true,
  imports: [RouterOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div class="shell"><router-outlet /></div>`,
  styles: [`.shell { height: 100vh; background: #0a0e1a; }`]
})
export class PatientShellComponent {
  constructor(public auth: AuthService) {}
}
