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
        <h2 class="page-title">
          <mat-icon>calendar_month</mat-icon> Appointments
        </h2>
        <p class="page-sub">All booked patient appointments.</p>
      </div>

      <mat-card class="table-card" appFadeIn>
        @if (appointments.length > 0) {
          <table mat-table [dataSource]="appointments" class="appt-table">

            <ng-container matColumnDef="date">
              <th mat-header-cell *matHeaderCellDef>Date & Time</th>
              <td mat-cell *matCellDef="let row">
                @if (row.datetime_iso?.startsWith('Requested')) {
                  <span class="date-requested">{{ row.datetime_iso }}</span>
                } @else {
                  <span class="date-value">{{ row.datetime_iso | date:'EEE, MMM d · h:mm a' }}</span>
                }
              </td>
            </ng-container>

            <ng-container matColumnDef="patient">
              <th mat-header-cell *matHeaderCellDef>Patient</th>
              <td mat-cell *matCellDef="let row">
                <span class="patient-name">{{ row.patient_name }}</span>
              </td>
            </ng-container>

            <ng-container matColumnDef="age">
              <th mat-header-cell *matHeaderCellDef>Age</th>
              <td mat-cell *matCellDef="let row">
                <span class="age-value">{{ row.patient_age }}</span>
              </td>
            </ng-container>

            <ng-container matColumnDef="gender">
              <th mat-header-cell *matHeaderCellDef>Gender</th>
              <td mat-cell *matCellDef="let row">
                <span class="age-value">{{ row.gender || '—' }}</span>
              </td>
            </ng-container>

            <ng-container matColumnDef="clinician">
              <th mat-header-cell *matHeaderCellDef>Clinician</th>
              <td mat-cell *matCellDef="let row">{{ row.provider }}</td>
            </ng-container>

            <ng-container matColumnDef="location">
              <th mat-header-cell *matHeaderCellDef>Location</th>
              <td mat-cell *matCellDef="let row">
                <span class="location-cell">
                  <mat-icon class="loc-icon">place</mat-icon>
                  {{ row.location }}
                </span>
              </td>
            </ng-container>

            <ng-container matColumnDef="reason">
              <th mat-header-cell *matHeaderCellDef>Reason</th>
              <td mat-cell *matCellDef="let row">
                @if (row.primary_concern || row.reason) {
                  <span class="reason-pill">{{ row.primary_concern || row.reason }}</span>
                } @else {
                  <span class="reason-empty">—</span>
                }
              </td>
            </ng-container>

            <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
            <tr mat-row *matRowDef="let row; columns: displayedColumns;" class="data-row"></tr>
          </table>
        } @else {
          <div class="no-data">
            <div class="no-data-icon-wrap">
              <mat-icon>calendar_today</mat-icon>
            </div>
            <p class="no-data-title">No appointments yet</p>
            <p class="no-data-sub">Booked appointments will appear here.</p>
          </div>
        }
      </mat-card>
    </div>
  `,
  styles: [`
    .page-container {
      padding: 28px 24px;
      max-width: 1200px;
      margin: 0 auto;
      color: #f1f5f9;
    }

    /* Header */
    .page-header { margin-bottom: 24px; }
    .page-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1.4rem;
      font-weight: 700;
      color: #f1f5f9;
      margin: 0 0 5px;
    }
    .page-title mat-icon { color: #14b8a6; font-size: 22px; }
    .page-sub { color: #64748b; margin: 0; font-size: 13px; }

    /* Card */
    .table-card {
      background: #111827 !important;
      border: 1px solid rgba(255,255,255,0.07) !important;
      border-radius: 12px !important;
      overflow: hidden;
      padding: 0 !important;
      box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
    }

    /* Table */
    .appt-table { width: 100%; background: transparent; }

    th.mat-header-cell {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.7px;
      text-transform: uppercase;
      color: #475569;
      border-bottom: 1px solid rgba(255,255,255,0.06) !important;
      padding: 13px 18px;
      background: rgba(0,0,0,0.15);
    }

    td.mat-cell {
      color: #94a3b8;
      font-size: 13.5px;
      border-bottom: 1px solid rgba(255,255,255,0.04) !important;
      padding: 14px 18px;
      vertical-align: middle;
    }

    tr.data-row { transition: background 120ms ease; }
    tr.data-row:hover td { background: rgba(255,255,255,0.025); cursor: default; }
    tr.data-row:last-child td { border-bottom: none !important; }

    /* Date cell */
    .date-value { color: #475569; font-weight: 500; }
    .date-requested {
      color: #f59e0b;
      font-size: 12px;
      font-weight: 600;
      background: rgba(245,158,11,0.1);
      padding: 3px 8px;
      border-radius: 6px;
    }

    /* Patient cell */
    .patient-name { font-weight: 600; color: #475569; font-size: 14px; }

    /* Age cell */
    .age-value { color: #475569; font-weight: 500; font-size: 13.5px; }

    /* Location cell */
    .location-cell {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #475569;
    }
    .loc-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
      color: #475569;
    }

    /* Reason pill */
    .reason-pill {
      display: inline-block;
      background: rgba(99,102,241,0.1);
      color: #a5b4fc;
      font-size: 12px;
      font-weight: 500;
      padding: 4px 10px;
      border-radius: 20px;
      border: 1px solid rgba(99,102,241,0.2);
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .reason-empty { color: #334155; }

    /* Empty state */
    .no-data {
      padding: 56px 24px;
      text-align: center;
    }
    .no-data-icon-wrap {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.06);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;
    }
    .no-data-icon-wrap mat-icon {
      font-size: 28px;
      width: 28px;
      height: 28px;
      color: #334155;
    }
    .no-data-title {
      font-size: 15px;
      font-weight: 600;
      color: #475569;
      margin: 0 0 6px;
    }
    .no-data-sub {
      font-size: 13px;
      color: #334155;
      margin: 0;
    }
  `]
})
export class AppointmentsPageComponent implements OnInit {
  appointments: any[] = [];
  displayedColumns: string[] = ['date', 'patient', 'age', 'gender', 'clinician', 'location', 'reason'];

  constructor(private api: TriageApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.api.getAppointments().subscribe({
      next: (res: any) => {
        this.appointments = res.appointments || [];
        this.cdr.markForCheck();
      },
      error: () => console.error('Failed to load appointments')
    });
  }
}