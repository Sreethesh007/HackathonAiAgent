import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-medical-spinner',
  standalone: true,
  templateUrl: './medical-spinner.component.html',
  styleUrls: ['./medical-spinner.component.scss']
})
export class MedicalSpinnerComponent {
  @Input() message: string = 'Loading...';
}
