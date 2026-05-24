import { Component, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-clinician-shell',
  standalone: true,
  imports: [
    RouterOutlet, RouterLink, RouterLinkActive,
    MatSidenavModule, MatListModule, MatToolbarModule,
    MatIconModule, MatButtonModule, MatTooltipModule, MatChipsModule
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-sidenav-container class="shell">
      <mat-sidenav #sidenav mode="side" opened class="shell-sidenav">
        <div class="sidenav-header">
          <mat-icon style="color:#14b8a6">local_hospital</mat-icon>
          <span class="title">Triage Admin</span>
        </div>
        <mat-nav-list>
          <a mat-list-item routerLink="overview" routerLinkActive="active-nav-link-accent" id="navOverview">
            <mat-icon matListItemIcon>dashboard</mat-icon>
            <span matListItemTitle>Overview</span>
          </a>
          <a mat-list-item routerLink="pending" routerLinkActive="active-nav-link-accent" id="navPending">
            <mat-icon matListItemIcon>pending_actions</mat-icon>
            <span matListItemTitle>HITL Queue</span>
          </a>
        </mat-nav-list>
        <div class="sidenav-footer">
          <span class="user-name">Dr. {{ auth.currentUsername() }}</span>
          <button mat-icon-button (click)="auth.logout()" matTooltip="Sign out">
            <mat-icon>logout</mat-icon>
          </button>
        </div>
      </mat-sidenav>
      <mat-sidenav-content class="main">
        <mat-toolbar class="top-bar">
          <button mat-icon-button (click)="sidenav.toggle()"><mat-icon>menu</mat-icon></button>
          <span style="flex:1"></span>
          <mat-chip color="accent" selected>Clinician</mat-chip>
        </mat-toolbar>
        <router-outlet />
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .shell { height: 100vh; background: #0a0e1a; }
    .main { background: #0a0e1a; }
    .top-bar { background: #111827 !important; border-bottom: 1px solid rgba(255,255,255,0.08) !important; }
  `]
})
export class ClinicianShellComponent {
  constructor(public auth: AuthService) {}
}
