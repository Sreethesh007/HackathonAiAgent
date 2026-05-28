import {
  Component,
  ChangeDetectionStrategy,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AuthService } from '../../../core/services/auth.service';
import { TriageApiService } from '../../../core/services/triage-api.service';

@Component({
  selector: 'app-clinician-shell',
  standalone: true,

  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatIconModule,
    MatTooltipModule,
  ],

  changeDetection: ChangeDetectionStrategy.OnPush,

  template: `
    <div
      class="shell-layout"
      [class.sidebar-collapsed]="sidebarCollapsed">

      <!-- ═════════════════ SIDEBAR ═════════════════ -->
      <aside class="sidebar">

        <!-- Sidebar Header -->
        <div class="sidebar-brand">

          <div class="brand-left">

            <div class="brand-icon-wrap">
              <mat-icon class="brand-icon">
                local_hospital
              </mat-icon>
            </div>

            <div class="brand-text">

              <span class="brand-title">
                Healthcare
              </span>

              <span class="brand-sub">
                Triage Agent
              </span>

            </div>

          </div>

        </div>

        <!-- Navigation -->
        <nav class="sidebar-nav">

          <a
            class="nav-item"
            routerLink="overview"
            routerLinkActive="nav-item--active"
            id="navOverview"
            matTooltip="Overview">

            <mat-icon class="nav-icon">
              dashboard
            </mat-icon>

            <span class="nav-label">
              Dashboard
            </span>

          </a>

          <a
            class="nav-item"
            routerLink="appointments"
            routerLinkActive="nav-item--active"
            id="navAppointments"
            matTooltip="Appointments">

            <mat-icon class="nav-icon">
              event
            </mat-icon>

            <span class="nav-label">
              Appointments
            </span>

          </a>

          <!-- Approvals -->
          <a
            class="nav-item approvals-nav"
            routerLink="pending"
            routerLinkActive="nav-item--active"
            id="navPending"
            matTooltip="Approvals">

            <mat-icon
              class="nav-icon"
              *ngIf="!sidebarCollapsed">

              check_circle

            </mat-icon>

            <span
              class="nav-label"
              *ngIf="!sidebarCollapsed">

              Approvals

            </span>

            <span
              class="nav-badge"
              *ngIf="pendingCount > 0">

              {{ pendingCount }}

            </span>

          </a>

        </nav>

        <div class="sidebar-spacer"></div>

        <!-- Footer -->
        <div class="sidebar-footer">

          <div class="user-row">

            <div class="user-avatar">
              {{ initials }}
            </div>

            <div class="user-info">

              <span class="user-name">
                Dr. {{ auth.currentUsername() }}
              </span>

              <span class="user-role">
                Lead Clinician
              </span>

            </div>

          </div>

          <button
            class="logout-btn"
            (click)="auth.logout()"
            matTooltip="Sign out">

            Log Out

          </button>

        </div>

      </aside>

      <!-- ═════════════════ MAIN CONTENT ═════════════════ -->
      <div class="main-content">

        <!-- Navbar -->
        <header class="top-bar">

          <div class="top-bar-left">

            <button
              class="hamburger-btn"
              (click)="toggleSidebar()"
              matTooltip="Toggle sidebar"
              aria-label="Toggle navigation sidebar">

              <mat-icon>
                menu
              </mat-icon>

            </button>

            <div class="top-title-wrap">

              <h1 class="top-app-title">
                Healthcare Triage Agent
              </h1>

            </div>

          </div>

        </header>

        <!-- Page Content -->
        <div class="page-area">
          <router-outlet />
        </div>

      </div>

    </div>
  `,

  styles: [`
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :host {
      display: block;
      height: 100vh;
      font-family: 'Inter', 'Roboto', sans-serif;
    }

    * {
      box-sizing: border-box;
    }

    /* ═════════════════ LAYOUT ═════════════════ */

    .shell-layout {
      display: flex;
      height: 100vh;
      overflow: hidden;
      background: #f4f7fb;
    }

    /* ═════════════════ SIDEBAR ═════════════════ */

    .sidebar {
      width: 248px;

      flex-shrink: 0;

      display: flex;
      flex-direction: column;

      background: linear-gradient(
        180deg,
        #26A69A 0%,
        #009688 100%
      );

      box-shadow: 4px 0 24px rgba(0, 105, 92, 0.18);

      position: relative;
      z-index: 10;

      transition:
        width 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    .shell-layout.sidebar-collapsed .sidebar {
      width: 72px;
    }

    /* Sidebar Header */

    .sidebar-brand {
      height: 72px;
      min-height: 72px;

      display: flex;
      align-items: center;

      padding: 0 16px;

      border-bottom: 1px solid rgba(255,255,255,0.14);

      overflow: hidden;
    }

    .brand-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .brand-icon-wrap {
      width: 42px;
      height: 42px;

      border-radius: 12px;

      background: rgba(255,255,255,0.16);

      display: flex;
      align-items: center;
      justify-content: center;

      flex-shrink: 0;
    }

    .brand-icon {
      color: #ffffff;

      font-size: 22px !important;
      width: 22px !important;
      height: 22px !important;
    }

    .brand-text {
      display: flex;
      flex-direction: column;

      overflow: hidden;

      white-space: nowrap;

      transition:
        opacity 180ms ease,
        width 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    .shell-layout.sidebar-collapsed .brand-text {
      opacity: 0;
      width: 0;
    }

    .brand-title {
      font-size: 15px;
      font-weight: 600;
      color: #ffffff;
    }

    .brand-sub {
      margin-top: 2px;

      font-size: 11px;
      font-weight: 400;

      color: rgba(255,255,255,0.72);
    }

    /* Navigation */

    .sidebar-nav {
      padding: 18px 12px;

      display: flex;
      flex-direction: column;

      gap: 6px;
    }

    .nav-item {
      height: 48px;

      display: flex;
      align-items: center;

      gap: 12px;

      padding: 0 14px;

      border-radius: 12px;

      text-decoration: none;

      color: rgba(255,255,255,0.82);

      font-size: 14px;
      font-weight: 500;

      position: relative;

      overflow: hidden;

      transition:
        background 180ms ease,
        transform 180ms ease,
        color 180ms ease;
    }

    .nav-item:hover {
      background: rgba(255,255,255,0.12);
      transform: translateX(2px);
      color: #ffffff;
    }

    .nav-item--active {
      background: rgba(255,255,255,0.18);
      color: #ffffff;
    }

    .shell-layout.sidebar-collapsed .nav-item {
      justify-content: center;
      align-items: center;
      padding: 0;
      width: 48px;
      gap: 0;
    }

    .nav-icon {
      font-size: 20px !important;
      width: 20px !important;
      height: 20px !important;
      flex-shrink: 0;
    }

    .nav-label {
      white-space: nowrap;

      transition:
        opacity 180ms ease,
        width 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    .shell-layout.sidebar-collapsed .nav-label {
      opacity: 0;
      width: 0;
    }

    /* Approval Badge */

    .nav-badge {
      min-width: 24px;
      height: 24px;

      padding: 0 8px;

      border-radius: 999px;

      display: flex;
      align-items: center;
      justify-content: center;

      font-size: 11px;
      font-weight: 700;

      background: #ffffff;
      color: #009688;

      margin-left: auto;

      box-shadow: 0 4px 12px rgba(0,0,0,0.18);
    }

    .shell-layout.sidebar-collapsed .approvals-nav {
      gap: 0;
    }

    .shell-layout.sidebar-collapsed .approvals-nav .nav-badge {
      margin-left: 0;
      min-width: 20px;
      height: 20px;
      padding: 0;
      font-size: 10px;
    }

    /* Spacer */

    .sidebar-spacer {
      flex: 1;
    }

    /* Footer */

    .sidebar-footer {
      padding: 18px;

      border-top: 1px solid rgba(255,255,255,0.12);
    }

    .user-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .shell-layout.sidebar-collapsed .user-row {
      justify-content: center;
    }

    .user-avatar {
      width: 40px;
      height: 40px;

      border-radius: 50%;

      background: rgba(255,255,255,0.16);

      border: 2px solid rgba(255,255,255,0.24);

      display: flex;
      align-items: center;
      justify-content: center;

      color: #ffffff;

      font-size: 13px;
      font-weight: 600;

      flex-shrink: 0;
    }

    .user-info {
      display: flex;
      flex-direction: column;

      overflow: hidden;
    }

    .shell-layout.sidebar-collapsed .user-info,
    .shell-layout.sidebar-collapsed .logout-btn {
      display: none;
    }

    .user-name {
      color: #ffffff;

      font-size: 14px;
      font-weight: 500;
    }

    .user-role {
      margin-top: 2px;

      color: rgba(255,255,255,0.72);

      font-size: 12px;
      font-weight: 400;
    }

    .logout-btn {
      width: 100%;

      margin-top: 16px;

      height: 42px;

      border: none;

      border-radius: 12px;

      background: rgba(255,255,255,0.14);

      color: #ffffff;

      font-size: 14px;
      font-weight: 500;

      cursor: pointer;

      transition:
        background 180ms ease,
        transform 180ms ease;
    }

    .logout-btn:hover {
      background: rgba(255,255,255,0.22);
      transform: translateY(-1px);
    }

    /* ═════════════════ MAIN CONTENT ═════════════════ */

    .main-content {
      flex: 1;

      display: flex;
      flex-direction: column;

      min-width: 0;

      overflow: hidden;
    }

    /* Navbar */

    .top-bar {
      height: 72px;
      min-height: 72px;

      display: flex;
      align-items: center;

      padding: 0 24px;

      background: #ffffff;

      border-bottom: 1px solid #e8edf2;

      box-shadow: 0 1px 4px rgba(0,0,0,0.04);

      z-index: 5;
    }

    .top-bar-left {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .hamburger-btn {
      width: 42px;
      height: 42px;

      border: none;
      background: transparent;

      border-radius: 50%;

      display: flex;
      align-items: center;
      justify-content: center;

      cursor: pointer;

      color: #424242;

      transition:
        background 180ms ease,
        transform 180ms ease,
        color 180ms ease;
    }

    .hamburger-btn:hover {
      background: #f3f5f7;
      color: #009688;
    }

    .hamburger-btn:active {
      transform: scale(0.96);
    }

    .hamburger-btn mat-icon {
      font-size: 24px !important;
      width: 24px !important;
      height: 24px !important;
    }

    .top-title-wrap {
      display: flex;
      align-items: center;
    }

    .top-app-title {
      margin: 0;

      color: #212121;

      font-size: 22px;
      font-weight: 600;

      line-height: 1.2;

      white-space: nowrap;
    }

    /* ═════════════════ PAGE AREA ═════════════════ */

    .page-area {
      flex: 1;

      overflow-y: auto;
    }

    .page-area::-webkit-scrollbar {
      width: 6px;
    }

    .page-area::-webkit-scrollbar-thumb {
      background: rgba(0,150,136,0.25);
      border-radius: 999px;
    }

    /* ═════════════════ TYPOGRAPHY ═════════════════ */

    .page-area ::ng-deep .page-title,
    .page-area ::ng-deep h1,
    .page-area ::ng-deep h2 {
      color: #212121 !important;

      font-size: 22px !important;
      font-weight: 600 !important;

      line-height: 1.3;
    }

    .page-area ::ng-deep .page-sub {
      color: #616161 !important;

      font-size: 15px !important;
      font-weight: 400 !important;
    }

    /* ═════════════════ CARDS ═════════════════ */

    .page-area ::ng-deep .mat-mdc-card,
    .page-area ::ng-deep mat-card,
    .page-area ::ng-deep .approval-card,
    .page-area ::ng-deep .session-card {
      background: #ffffff !important;

      border: 1px solid #e8edf2 !important;

      border-radius: 16px !important;

      box-shadow:
        0 2px 6px rgba(0,0,0,0.04),
        0 8px 24px rgba(0,0,0,0.04) !important;

      color: #212121 !important;

      transition:
        transform 180ms ease,
        box-shadow 180ms ease;
    }

    .page-area ::ng-deep .mat-mdc-card:hover,
    .page-area ::ng-deep .approval-card:hover,
    .page-area ::ng-deep .session-card:hover {
      transform: translateY(-2px);

      box-shadow:
        0 4px 10px rgba(0,0,0,0.06),
        0 12px 30px rgba(0,0,0,0.06) !important;
    }

    /* ═════════════════ TABLES ═════════════════ */

    .page-area ::ng-deep table.mat-mdc-table {
      background: #ffffff !important;

      border-radius: 16px !important;

      overflow: hidden;

      border: 1px solid #e8edf2 !important;
    }

    .page-area ::ng-deep th.mat-mdc-header-cell {
      background: #f8fafc !important;

      color: #424242 !important;

      font-size: 15px !important;
      font-weight: 600 !important;

      border-bottom: 1px solid #e8edf2 !important;

      padding: 18px 20px !important;
    }

    .page-area ::ng-deep td.mat-mdc-cell {
      color: #424242 !important;

      font-size: 14px !important;
      font-weight: 500 !important;

      padding: 18px 20px !important;

      border-bottom: 1px solid #eef2f7 !important;
    }

    .page-area ::ng-deep td.mat-mdc-cell:first-child {
      font-weight: 600 !important;
      color: #212121 !important;
    }

    .page-area ::ng-deep tr.mat-mdc-row:nth-child(even) td {
      background: #fbfcfd !important;
    }

    .page-area ::ng-deep tr.mat-mdc-row:hover td {
      background: #f4fffd !important;
    }

    /* ═════════════════ BUTTONS ═════════════════ */

    .page-area ::ng-deep .approve-btn,
    .page-area ::ng-deep .mat-mdc-raised-button.approve-btn {
      background: #009688 !important;
      color: #ffffff !important;

      border-radius: 10px !important;

      font-weight: 600 !important;

      transition:
        background 180ms ease,
        transform 180ms ease,
        box-shadow 180ms ease;
    }

    .page-area ::ng-deep .approve-btn:hover,
    .page-area ::ng-deep .mat-mdc-raised-button.approve-btn:hover {
      background: #00897B !important;

      transform: translateY(-1px);

      box-shadow: 0 8px 20px rgba(0,150,136,0.22) !important;
    }

    .page-area ::ng-deep .reject-btn,
    .page-area ::ng-deep .mat-mdc-raised-button.reject-btn,
    .page-area ::ng-deep .mat-mdc-raised-button.mat-warn {
      background: #FF6F61 !important;

      color: #ffffff !important;

      border-radius: 10px !important;

      font-weight: 600 !important;

      transition:
        background 180ms ease,
        transform 180ms ease,
        box-shadow 180ms ease;
    }

    .page-area ::ng-deep .reject-btn:hover,
    .page-area ::ng-deep .mat-mdc-raised-button.reject-btn:hover,
    .page-area ::ng-deep .mat-mdc-raised-button.mat-warn:hover {
      background: #f45d50 !important;

      transform: translateY(-1px);

      box-shadow: 0 8px 20px rgba(255,111,97,0.22) !important;
    }

    /* ═════════════════ RESPONSIVE ═════════════════ */

    @media (max-width: 768px) {

      .top-app-title {
        font-size: 18px;
      }

      .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        height: 100vh;
      }

      .shell-layout.sidebar-collapsed .sidebar {
        width: 0;
        overflow: hidden;
      }
    }
  `],
})
export class ClinicianShellComponent implements OnInit, OnDestroy {

  pendingCount = 0;

  sidebarCollapsed = false;

  private pollTimer: any;

  constructor(
    public auth: AuthService,
    private api: TriageApiService,
    private cdr: ChangeDetectorRef
  ) {}

  get initials(): string {
    const name = this.auth.currentUsername() ?? '';

    return (
      name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2) || 'DR'
    );
  }

  ngOnInit() {
    this.fetchPending();

    this.pollTimer = setInterval(
      () => this.fetchPending(),
      10000
    );
  }

  ngOnDestroy() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
    }
  }

  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
  }

  fetchPending() {
    this.api.getPendingReviews().subscribe({
      next: (res) => {
        this.pendingCount = (res.sessions || []).length;
        this.cdr.markForCheck();
      },
      error: () => {},
    });
  }
}