import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { TriageApiService } from '../../../core/services/triage-api.service';
import { FadeInDirective } from '../../../shared/directives/fade-in.directive';

@Component({
  selector: 'app-appointments-page',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatTableModule, FadeInDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page-container">
      <div class="page-header">
        <h2 class="page-title"><mat-icon>event</mat-icon> Appointments</h2>
        <p class="page-sub">View all booked patient appointments.</p>
      </div>

      <mat-card class="table-card" appFadeIn>
        <table mat-table [dataSource]="appointments" class="mat-elevation-z0" *ngIf="appointments.length > 0; else noData">
          
          <ng-container matColumnDef="date">
            <th mat-header-cell *matHeaderCellDef> Date & Time </th>
            <td mat-cell *matCellDef="let element"> {{ element.datetime_iso | date:'MMM d, y, h:mm a' }} </td>
          </ng-container>

          <ng-container matColumnDef="patient">
            <th mat-header-cell *matHeaderCellDef> Patient </th>
            <td mat-cell *matCellDef="let element"> 
              <strong>{{ element.patient_name }}</strong> (Age: {{ element.patient_age }}) 
            </td>
          </ng-container>

          <ng-container matColumnDef="provider">
            <th mat-header-cell *matHeaderCellDef> Provider </th>
            <td mat-cell *matCellDef="let element"> {{ element.provider }} </td>
          </ng-container>

          <ng-container matColumnDef="location">
            <th mat-header-cell *matHeaderCellDef> Location </th>
            <td mat-cell *matCellDef="let element"> {{ element.location }} </td>
          </ng-container>

          <ng-container matColumnDef="reason">
            <th mat-header-cell *matHeaderCellDef> Reason </th>
            <td mat-cell *matCellDef="let element"> {{ element.reason }} </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
        </table>

        <ng-template #noData>
          <div class="no-data">
            <mat-icon>calendar_today</mat-icon>
            <p>No appointments booked yet.</p>
          </div>
        </ng-template>
      </mat-card>
    </div>
  `,
  styles: [`
    .page-container { padding: 24px; max-width: 1200px; margin: 0 auto; color: #f1f5f9; }
    .page-header { margin-bottom: 24px; }
    .page-title { display: flex; align-items: center; gap: 10px; font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0 0 6px; }
    .page-title mat-icon { color: #6366f1; }
    .page-sub { color: #94a3b8; margin: 0; }
    
    .table-card { background: #111827 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 16px !important; overflow: hidden; }
    
    table { width: 100%; background: transparent; }
    th.mat-header-cell { color: #94a3b8; font-weight: 600; border-bottom-color: #1e293b; padding: 16px; }
    td.mat-cell { color: #cbd5e1; border-bottom-color: #1e293b; padding: 16px; }
    tr.mat-row:hover { background: rgba(255,255,255,0.02); }
    
    .no-data { padding: 48px; text-align: center; color: #64748b; }
    .no-data mat-icon { font-size: 48px; width: 48px; height: 48px; margin-bottom: 16px; opacity: 0.5; }
    .no-data p { font-size: 1.1rem; margin: 0; }
  `]
})
export class AppointmentsPageComponent implements OnInit {
  appointments: any[] = [];
  displayedColumns: string[] = ['date', 'patient', 'provider', 'location', 'reason'];

  constructor(private api: TriageApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.api.getAppointments().subscribe({
      next: (res: any) => {
        this.appointments = res.appointments || [];
        this.cdr.markForCheck();
      },
      error: () => {
        console.error('Failed to load appointments');
      }
    });
  }
}
