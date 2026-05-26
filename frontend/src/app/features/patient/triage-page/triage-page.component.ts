import { Component, ChangeDetectionStrategy, ChangeDetectorRef, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { TriageApiService } from '../../../core/services/triage-api.service';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';
import { TriageRequest, ContinueRequest } from '../../../core/models/triage.models';

interface ThinkingStep {
  node: string;
  label: string;
  icon: string;
  content: string;
  done: boolean;
}
interface ChatMessage {
  role: 'user' | 'agent' | 'system';
  content: string;
}

const NODE_META: Record<string, { label: string; icon: string }> = {
  orchestrator:  { label: 'Planning',              icon: 'hub' },
  triage:        { label: 'Assessing Symptoms',    icon: 'monitor_heart' },
  research:      { label: 'Researching Guidelines',icon: 'find_in_page' },
  scheduler:     { label: 'Booking Appointment',   icon: 'calendar_month' },
  critic:        { label: 'Quality Review',        icon: 'verified' },
  human_review:  { label: 'Human Review',          icon: 'person_search' },
  synthesizer:   { label: 'Composing Reply',       icon: 'edit_note' },
};

@Component({
  selector: 'app-triage-page',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="app-layout">

<!-- ── Sidebar ── -->
<aside class="sidebar" [class.collapsed]="sidebarCollapsed">

  <!-- Brand -->
  <div class="sidebar-brand">

    <!-- Left Section -->
    <ng-container *ngIf="!sidebarCollapsed">

      <div class="brand-left">

        <div class="brand-icon">
          <mat-icon>health_and_safety</mat-icon>
        </div>

        <div class="brand-text">
          <span class="brand-name">MediTriage</span>
          <span class="brand-sub">AI Assistant</span>
        </div>

      </div>

    </ng-container>

    <!-- Hamburger RIGHT -->
    <button
      class="sidebar-toggle-btn"
      (click)="toggleSidebar()"
      [title]="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">

        <mat-icon>
          menu
        </mat-icon>

    </button>

  </div>

  <!-- New Chat -->
  <div class="sidebar-new-chat" *ngIf="!sidebarCollapsed">

    <button
      class="new-chat-btn"
      (click)="newSession()"
      id="newChatBtn">

      <mat-icon>add</mat-icon>
      New Conversation

    </button>

  </div>

  <div class="sidebar-new-chat" *ngIf="sidebarCollapsed">

    <button
      class="icon-only-btn"
      (click)="newSession()"
      title="New Conversation">

      <mat-icon>add</mat-icon>

    </button>

  </div>

  <!-- Session List -->
  <ng-container *ngIf="!sidebarCollapsed">

    <div class="sidebar-section-label">
      Recent Chats
    </div>

    <div class="session-list">

      <div
        class="session-item"
        *ngFor="let s of sessions"
        [class.active]="s.session_id === activeSessionId"
        (click)="loadSession(s.session_id)">

        <mat-icon class="session-icon">
          chat_bubble_outline
        </mat-icon>

        <div class="session-info">

          <div class="session-summary">
            {{ s.summary || 'New session' }}
          </div>

          <div class="session-date">
            {{ s.created_at | date:'MMM d, h:mm a' }}
          </div>

        </div>

      </div>

      <div *ngIf="sessions.length === 0" class="no-sessions">

        <mat-icon>forum</mat-icon>

        <span>No conversations yet</span>

      </div>

    </div>

  </ng-container>

<!-- No session list when collapsed -->
<ng-container *ngIf="sidebarCollapsed">
</ng-container>

  <!-- Footer -->
<div class="sidebar-footer" *ngIf="!sidebarCollapsed">

  <div class="user-info">

    <div class="user-avatar">
      <mat-icon>account_circle</mat-icon>
    </div>

    <span class="user-name">
      {{ auth.currentUsername() }}
    </span>

  </div>

  <button
    class="logout-btn"
    (click)="auth.logout()"
    title="Sign out">

    <mat-icon>logout</mat-icon>

  </button>

</div>

</aside>

      <!-- ── Main Chat Area ── -->
      <main class="chat-main">
        <!-- Header — height matches sidebar brand row -->
        <div class="chat-header">
          <div class="header-center">
            <div class="header-title">
              <mat-icon>medical_services</mat-icon> AI Triage Assistant
            </div>
            <!-- Subtitle line — aligns with sidebar-sub -->
            <div class="header-sub">Powered by multi-agent reasoning</div>
          </div>

          <div class="header-status" *ngIf="requiresHumanReview">
            <mat-icon class="pulse">pending</mat-icon> Pending Clinician Review
          </div>
          <!-- placeholder so flex stays balanced when no status -->
          <div class="header-status-placeholder" *ngIf="!requiresHumanReview"></div>
        </div>

        <div class="chat-messages" #chatScroll>

          <div class="welcome-banner" *ngIf="messages.length === 0 && thinkingSteps.length === 0">
            <div class="welcome-orb"><mat-icon>health_and_safety</mat-icon></div>
            <h1>How can I help you today?</h1>
            <p>Describe your symptoms clearly. I will assess urgency and recommend next steps.</p>
            <div class="welcome-chips">
              <span class="welcome-chip" (click)="inputText='I have a headache and fever'">🤕 Headache &amp; fever</span>
              <span class="welcome-chip" (click)="inputText='I have chest pain'">💔 Chest pain</span>
              <span class="welcome-chip" (click)="inputText='I need to book an appointment'">📅 Book appointment</span>
            </div>
          </div>

          <ng-container *ngFor="let msg of messages">
            <div class="message-wrapper" [ngClass]="msg.role">
              <div class="avatar" *ngIf="msg.role === 'agent' || msg.role === 'system'">
                <mat-icon>smart_toy</mat-icon>
              </div>
              <div class="message-content">
                <p>{{ msg.content }}</p>
              </div>
              <div class="avatar" *ngIf="msg.role === 'user'">
                <mat-icon>person</mat-icon>
              </div>
            </div>
          </ng-container>

          <!-- ── Thinking Panel ── -->
          <div class="thinking-panel" *ngIf="thinkingSteps.length > 0 || isStreaming">
            <div class="thinking-panel-header" (click)="toggleThinking()">
              <div class="thinking-panel-left">
                <div class="thinking-orb" [class.active]="isStreaming">
                  <mat-icon>psychology</mat-icon>
                </div>
                <span class="thinking-title">{{ isStreaming ? 'Thinking...' : 'Thought for a moment' }}</span>
                <div class="step-pills">
                  <span class="step-pill" *ngFor="let step of thinkingSteps" [class.active]="!step.done">
                    <mat-icon>{{ step.icon }}</mat-icon>
                    {{ step.label }}
                  </span>
                </div>
              </div>
              <mat-icon class="chevron" [class.rotated]="thinkingExpanded">expand_more</mat-icon>
            </div>

            <div class="thinking-panel-body" [class.expanded]="thinkingExpanded">
              <div class="thinking-step" *ngFor="let step of thinkingSteps; let i = index">
                <div class="step-connector" *ngIf="i > 0"></div>
                <div class="step-header">
                  <div class="step-icon-wrap" [class.done]="step.done" [class.running]="!step.done">
                    <mat-icon class="step-spin" *ngIf="!step.done">autorenew</mat-icon>
                    <mat-icon *ngIf="step.done">check</mat-icon>
                  </div>
                  <span class="step-label">{{ step.label }}</span>
                  <span class="step-badge" *ngIf="step.done">Done</span>
                  <span class="step-badge running" *ngIf="!step.done">Running</span>
                </div>
                <div class="step-content" *ngIf="formatThinkingContent(step.content) as display">
                  <p class="step-text">{{ display }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="reply-preview" *ngIf="agentReplyPreview && !isStreaming">
            <div class="reply-preview-content">
              <pre>{{ agentReplyPreview }}</pre>
            </div>
          </div>

          <!-- Interactive block for appointments -->
          <div class="interactive-block" *ngIf="offerAppointment && !isStreaming">
            <p>Would you like me to book an appointment for you?</p>
            <div class="actions">
              <button class="btn-yes" (click)="sendReply('Yes, please book an appointment.')">Yes</button>
              <button class="btn-no" (click)="sendReply('No, thank you.')">No</button>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-wrapper">
            <input type="text" [(ngModel)]="inputText" (keyup.enter)="sendMessage()"
                   placeholder="Describe your symptoms or reply..." [disabled]="isStreaming" />
            <button class="send-btn" (click)="sendMessage()" [disabled]="isStreaming || !inputText.trim()">
              <mat-icon>send</mat-icon>
            </button>
          </div>
          <div class="disclaimer">
            This AI is for informational purposes only. In an emergency, call 911 immediately.
          </div>
        </div>
      </main>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100vh; }
    .app-layout {
      display: flex; height: 100%; background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif;
    }

/* ───────────────── Sidebar ───────────────── */

.sidebar {
  width: 280px;
  background: #111827;

  border-right: 1px solid #1e293b;

  display: flex;
  flex-direction: column;

  flex-shrink: 0;

  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);

  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;

  height: 73px;

  padding: 0 13px;

  border-bottom: 1px solid #1e293b;

  flex-shrink: 0;
}

/* Left Brand Content */
.brand-left {
  display: flex;
  align-items: center;

  gap: 12px;

  min-width: 0;
}

.brand-icon {
  width: 38px;
  height: 38px;

  border-radius: 10px;

  flex-shrink: 0;

  background: linear-gradient(135deg, #6366f1, #8b5cf6);

  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-icon mat-icon {
  font-size: 22px;
  width: 22px;
  height: 22px;

  color: white;
}

.brand-text {
  display: flex;
  flex-direction: column;

  white-space: nowrap;
  overflow: hidden;
}

.brand-name {
  font-size: 1rem;
  font-weight: 700;

  color: #f1f5f9;

  line-height: 1.2;
}

.brand-sub {
  font-size: 0.72rem;

  color: #64748b;

  margin-top: 2px;
}

/* Toggle Button */
.sidebar-toggle-btn {
  width: 40px;
  height: 40px;

  flex-shrink: 0;

  background: none;
  border: none;

  cursor: pointer;

  border-radius: 8px;

  color: #64748b;

  display: flex;
  align-items: center;
  justify-content: center;

  transition: color 0.2s, background 0.2s;
}

.sidebar-toggle-btn:hover {
  color: #e2e8f0;
  background: rgba(255,255,255,0.06);
}

.sidebar-toggle-btn mat-icon {
  font-size: 22px;
  width: 22px;
  height: 22px;

  transition: font-size 0.2s, width 0.2s, height 0.2s;
}

/* Slightly bigger when collapsed */
.sidebar.collapsed .sidebar-toggle-btn mat-icon {
  font-size: 26px;
  width: 26px;
  height: 26px;
}

/* New Chat */
.sidebar-new-chat {
  padding: 16px 12px 8px;
}

.new-chat-btn {
  width: 100%;

  padding: 10px 16px;

  background: linear-gradient(135deg, #6366f1, #8b5cf6);

  border: none;
  border-radius: 10px;

  color: white;
  font-weight: 600;

  cursor: pointer;

  display: flex;
  align-items: center;
  justify-content: center;

  gap: 8px;

  font-size: 0.875rem;

  transition: opacity 0.2s, transform 0.2s;

  white-space: nowrap;
}

.new-chat-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.icon-only-btn {
  width: 40px;
  height: 40px;

  background: linear-gradient(135deg, #6366f1, #8b5cf6);

  border: none;
  border-radius: 10px;

  color: white;

  cursor: pointer;

  display: flex;
  align-items: center;
  justify-content: center;

  margin: 0 auto;

  transition: opacity 0.2s;
}

.icon-only-btn:hover {
  opacity: 0.85;
}

/* Section Label */
.sidebar-section-label {
  padding: 10px 16px 4px;

  font-size: 0.7rem;
  font-weight: 700;

  letter-spacing: 0.08em;
  text-transform: uppercase;

  color: #475569;

  white-space: nowrap;
}

/* Session List */
.session-list {
  flex: 1;

  overflow-y: auto;

  padding: 4px 8px;
}

.session-item {
  display: flex;
  align-items: center;

  gap: 10px;

  padding: 10px 12px;

  border-radius: 8px;

  cursor: pointer;

  margin-bottom: 2px;

  transition: background 0.15s;

  border: 1px solid transparent;
}

.session-item:hover {
  background: #1e293b;
}

.session-item.active {
  background: #1e293b;
  border-color: #334155;
}

.session-icon {
  font-size: 18px;
  width: 18px;
  height: 18px;

  color: #475569;

  flex-shrink: 0;
}

.session-info {
  min-width: 0;
}

.session-summary {
  font-size: 0.85rem;
  font-weight: 500;

  color: #cbd5e1;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-date {
  font-size: 0.72rem;

  color: #475569;

  margin-top: 2px;
}

.no-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px 12px;
  min-height: 160px;
  color: #94a3b8;
  text-align: center;
}

.no-sessions mat-icon {
  font-size: 34px;
  width: 34px;
  height: 34px;
  color: #64748b;
}

.no-sessions span {
  font-size: 0.95rem;
}

/* Footer */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 14px 12px;

  border-top: 1px solid #1e293b;

  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;

  gap: 10px;

  min-width: 0;
}

.user-avatar mat-icon {
  font-size: 28px;
  width: 28px;
  height: 28px;

  color: #6366f1;
}

.user-name {
  font-size: 0.85rem;
  font-weight: 500;

  color: #94a3b8;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  background: none;
  border: none;

  cursor: pointer;

  padding: 6px;

  border-radius: 6px;

  color: #475569;

  transition: color 0.2s, background 0.2s;

  display: flex;
  align-items: center;
}

.logout-btn:hover {
  color: #f87171;
  background: rgba(248,113,113,0.08);
}

    /* ── Main Chat ──────────────────────────────────────────────── */
    .chat-main { flex: 1; display: flex; flex-direction: column; background: #0f172a; position: relative; min-width: 0; }

    /* BUG FIX 2: header height matches sidebar brand height (73px) */
    .chat-header {
      height: 73px;
      padding: 0 24px;
      border-bottom: 1px solid #1e293b;
      display: flex;
      align-items: center;
      gap: 16px;
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(8px);
      z-index: 10;
      flex-shrink: 0;
    }

    /* Hamburger toggle — lives inside sidebar-brand */
    .sidebar-toggle-btn {
      width: 40px; height: 40px; flex-shrink: 0;
      background: none; border: none; cursor: pointer; border-radius: 8px;
      color: #64748b; display: flex; align-items: center; justify-content: center;
      transition: color 0.2s, background 0.2s;
    }
    .sidebar-toggle-btn:hover { color: #e2e8f0; background: rgba(255,255,255,0.06); }
    .sidebar-toggle-btn mat-icon { font-size: 22px; width: 22px; height: 22px; }

    /* BUG FIX 2: centre-column holding title + sub, mirrors sidebar brand-text */
    .header-center { display: flex; flex-direction: column; flex: 1; }
    .header-title {
      display: flex; align-items: center; gap: 10px;
      font-size: 1.1rem; font-weight: 600; color: #e2e8f0; line-height: 1.2;
    }
    .header-title mat-icon { color: #6366f1; }
    /* mirrors brand-sub */
    .header-sub { font-size: 0.72rem; color: #64748b; margin-top: 2px; }

    .header-status {
      display: flex; align-items: center; gap: 8px;
      color: #f59e0b; font-size: 0.9rem; font-weight: 500;
      background: rgba(245, 158, 11, 0.1); padding: 6px 12px; border-radius: 16px;
      flex-shrink: 0;
    }
    .header-status-placeholder { width: 0; }
    .pulse { animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

    /* Messages */
    .chat-messages { flex: 1; overflow-y: auto; padding: 32px; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth; }
    .welcome-banner { margin: auto; text-align: center; color: #94a3b8; max-width: 480px; padding: 20px; }
    .welcome-orb {
      width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 20px;
      background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
      border: 1px solid rgba(99,102,241,0.3);
      display: flex; align-items: center; justify-content: center;
    }
    .welcome-orb mat-icon { font-size: 36px; width: 36px; height: 36px; color: #6366f1; }
    .welcome-banner h1 { color: #e2e8f0; font-size: 1.5rem; margin-bottom: 10px; }
    .welcome-banner p { margin-bottom: 20px; font-size: 0.95rem; }
    .welcome-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
    .welcome-chip {
      padding: 8px 16px; border-radius: 20px; background: rgba(51,65,85,0.6);
      border: 1px solid #334155; font-size: 0.82rem; color: #cbd5e1;
      cursor: pointer; transition: all 0.2s; user-select: none;
    }
    .welcome-chip:hover { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.4); color: #a5b4fc; transform: translateY(-1px); }

    .message-wrapper { display: flex; gap: 16px; max-width: 85%; }
    .message-wrapper.user { align-self: flex-end; flex-direction: row-reverse; }
    .message-wrapper.agent { align-self: flex-start; }
    .avatar {
      width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; background: #1e293b; border: 1px solid #334155;
    }
    .user .avatar { background: #6366f1; border-color: #8b5cf6; }
    .avatar mat-icon { font-size: 20px; width: 20px; height: 20px; color: #e2e8f0; }
    .message-content {
      padding: 16px 20px; border-radius: 16px; line-height: 1.6; font-size: 1rem; position: relative;
    }
    .message-content p { margin: 0; white-space: pre-wrap; }
    .user .message-content {
      background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white;
      border-bottom-right-radius: 4px; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }
    .agent .message-content {
      background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
      border-bottom-left-radius: 4px;
    }

    /* ── Thinking Panel ─────────────────────────────────────────── */
    .thinking-panel {
      align-self: flex-start; width: calc(100% - 56px); margin-left: 56px;
      background: rgba(30, 41, 59, 0.6); border: 1px solid #334155;
      border-radius: 12px;
      overflow: visible;
      transition: border-color 0.3s;
    }
    .thinking-panel:hover { border-color: #475569; }
    .thinking-panel-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 16px; cursor: pointer; user-select: none; transition: background 0.2s;
      border-radius: 12px;
      backdrop-filter: blur(8px);
    }
    .thinking-panel-header:hover { background: rgba(255,255,255,0.03); }
    .thinking-panel-left { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; flex: 1; }
    .thinking-orb {
      width: 32px; height: 32px; border-radius: 50%;
      background: linear-gradient(135deg, #1e293b, #334155);
      border: 1px solid #475569;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.3s;
    }
    .thinking-orb.active {
      background: linear-gradient(135deg, #4f46e5, #7c3aed); border-color: #6366f1;
      box-shadow: 0 0 12px rgba(99,102,241,0.4);
      animation: orb-pulse 2s ease-in-out infinite;
    }
    .thinking-orb mat-icon { font-size: 18px; width: 18px; height: 18px; color: #e2e8f0; }
    @keyframes orb-pulse { 0%,100%{box-shadow:0 0 8px rgba(99,102,241,0.3)} 50%{box-shadow:0 0 20px rgba(99,102,241,0.6)} }
    .thinking-title { font-size: 0.9rem; font-weight: 600; color: #cbd5e1; white-space: nowrap; }
    .step-pills { display: flex; gap: 6px; flex-wrap: wrap; }
    .step-pill {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 3px 10px 3px 6px; border-radius: 20px;
      background: rgba(71,85,105,0.4); border: 1px solid #475569;
      font-size: 0.75rem; color: #94a3b8; transition: all 0.2s;
    }
    .step-pill mat-icon { font-size: 14px; width: 14px; height: 14px; }
    .step-pill.active { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.4); color: #a5b4fc; }
    .chevron { color: #64748b; transition: transform 0.3s ease; flex-shrink: 0; }
    .chevron.rotated { transform: rotate(180deg); }

    /* BUG FIX 3: panel body — remove max-height cap so content never cuts off;
       use a large enough value during expand so all content shows */
    .thinking-panel-body {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
      border-top: 0px solid transparent;
      border-radius: 0 0 12px 12px;
    }
    .thinking-panel-body.expanded {
      /* Grow to full content height — outer chat-messages scrolls, so no inner cap needed */
      max-height: 10000px;
      overflow: visible;
      border-top: 1px solid #1e293b;
    }

    .thinking-step { padding: 16px 20px; position: relative; }
    .thinking-step:not(:last-child) { border-bottom: 1px solid rgba(51,65,85,0.5); }
    .step-connector {
      position: absolute; top: 0; left: 36px; width: 1px; height: 16px;
      background: linear-gradient(to bottom, #334155, transparent);
    }
    .step-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .step-icon-wrap {
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
      border: 1px solid #334155; background: #1e293b;
    }
    .reply-preview {
      align-self: flex-start;
      width: calc(100% - 56px);
      margin-left: 56px;
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid #334155;
      border-radius: 14px;
      padding: 18px 20px;
      margin-top: 18px;
      color: #e2e8f0;
    }
    .reply-preview-label {
      font-size: 0.85rem;
      font-weight: 600;
      color: #cbd5e1;
      margin-bottom: 8px;
    }
    .reply-preview-content pre {
      margin: 0;
      white-space: pre-wrap;
      font-family: 'Inter', sans-serif;
      line-height: 1.7;
      color: #f8fafc;
      background: transparent;
      border: none;
    }
    .step-icon-wrap.done { background: rgba(20,184,166,0.1); border-color: #14b8a6; }
    .step-icon-wrap.done mat-icon { color: #14b8a6; }
    .step-icon-wrap.running { background: rgba(99,102,241,0.1); border-color: #6366f1; }
    .step-icon-wrap.running mat-icon { color: #818cf8; }
    .step-icon-wrap mat-icon { font-size: 16px; width: 16px; height: 16px; color: #94a3b8; }
    .step-spin { animation: spin 1.2s linear infinite; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .step-label { font-size: 0.875rem; font-weight: 600; color: #e2e8f0; flex: 1; }
    .step-badge {
      font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 10px;
      background: rgba(20,184,166,0.15); color: #14b8a6; border: 1px solid rgba(20,184,166,0.3);
    }
    .step-badge.running {
      background: rgba(99,102,241,0.15); color: #818cf8; border-color: rgba(99,102,241,0.3);
      animation: badge-pulse 1.5s ease-in-out infinite;
    }
    @keyframes badge-pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

    /* BUG FIX 1 + 3: step content — <p> wraps naturally, no truncation */
    .step-content {
      padding: 10px 12px;
      background: rgba(15,23,42,0.6);
      border-radius: 8px;
      border: 1px solid #1e293b;
    }
    .step-text {
      margin: 0;
      font-size: 0.85rem;
      color: #cbd5e1;
      font-family: 'Inter', sans-serif;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.7;
    }

    /* Interactive block */
    .interactive-block {
      align-self: flex-start; margin-left: 56px; background: rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 20px; border-radius: 16px; display: flex; flex-direction: column; gap: 16px;
    }
    .interactive-block p { margin: 0; font-weight: 500; color: #e2e8f0; }
    .actions { display: flex; gap: 12px; }
    .actions button { padding: 10px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; border: none; }
    .btn-yes { background: #14b8a6; color: white; }
    .btn-yes:hover { background: #0d9488; transform: translateY(-1px); }
    .btn-no { background: #334155; color: #e2e8f0; }
    .btn-no:hover { background: #475569; transform: translateY(-1px); }

    /* Input Area */
    .chat-input-area { padding: 24px 32px; background: linear-gradient(to top, #0f172a 80%, transparent); }
    .input-wrapper {
      display: flex; gap: 12px; background: #1e293b; padding: 8px; border-radius: 24px;
      border: 1px solid #334155; box-shadow: 0 8px 24px rgba(0,0,0,0.2); transition: border-color 0.2s;
    }
    .input-wrapper:focus-within { border-color: #6366f1; }
    .input-wrapper input {
      flex: 1; background: transparent; border: none; color: #f8fafc; padding: 8px 16px;
      font-size: 1rem; outline: none; font-family: inherit;
    }
    .input-wrapper input::placeholder { color: #64748b; }
    .send-btn {
      width: 40px; height: 40px; border-radius: 50%; background: #6366f1; color: white;
      border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: background 0.2s; flex-shrink: 0;
    }
    .send-btn:hover:not(:disabled) { background: #4f46e5; }
    .send-btn:disabled { background: #334155; color: #64748b; cursor: not-allowed; }
    .disclaimer { text-align: center; margin-top: 12px; font-size: 0.75rem; color: #64748b; }
  `]
})
export class TriagePageComponent implements OnInit {
  @ViewChild('chatScroll') private chatScroll!: ElementRef;

  sessions: any[] = [];
  activeSessionId: string | null = null;
  messages: ChatMessage[] = [];
  thinkingSteps: ThinkingStep[] = [];
  thinkingExpanded = true;
  inputText = '';
  isStreaming = false;
  offerAppointment = false;
  appointmentOfferAnswered = false;
  requiresHumanReview = false;
  agentMessageReceived = false;
  agentReplyPreview: string | null = null;

  // BUG FIX 2: sidebar toggle state
  sidebarCollapsed = false;

  constructor(
    private api: TriageApiService,
    private notify: NotificationService,
    public auth: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() { this.fetchSessions(); }

  // BUG FIX 2
  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    this.cdr.markForCheck();
  }

  fetchSessions() {
    this.api.getSessions().subscribe({
      next: (res) => {
        this.sessions = res.sessions || [];
        this.sessions.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        this.cdr.markForCheck();
      }
    });
  }

  toggleThinking() {
    this.thinkingExpanded = !this.thinkingExpanded;
    this.cdr.markForCheck();
  }

  // BUG FIX 1 + 3: extract only human-readable text; return null/empty to hide the block entirely
  formatThinkingContent(raw: string): string | null {
    if (!raw) return null;
    const cleaned = this.extractHumanReadable(raw);
    const trimmed = cleaned.trim();
    return trimmed.length > 0 ? trimmed : null;
  }

  newSession() {
    this.activeSessionId = null;
    this.messages = [];
    this.thinkingSteps = [];
    this.thinkingExpanded = true;
    this.offerAppointment = false;
    this.appointmentOfferAnswered = false;
    this.requiresHumanReview = false;
    this.agentMessageReceived = false;
    this.agentReplyPreview = null;
    this.cdr.markForCheck();
  }

  loadSession(sessionId: string) {
    this.activeSessionId = sessionId;
    this.messages = [];
    this.thinkingSteps = [];
    this.thinkingExpanded = true;
    this.offerAppointment = false;
    this.appointmentOfferAnswered = false;
    this.agentMessageReceived = false;
    this.agentReplyPreview = null;
    this.notify.success('Session loaded. You can continue the chat.');
    this.cdr.markForCheck();
  }

  sendReply(text: string) {
    this.appointmentOfferAnswered = true;
    this.offerAppointment = false;
    this.inputText = text;
    this.sendMessage();
  }

  sendMessage() {
    if (!this.inputText.trim() || this.isStreaming) return;
    const text = this.inputText.trim();
    this.inputText = '';
    this.messages.push({ role: 'user', content: text });
    this.thinkingSteps = [];
    this.thinkingExpanded = true;
    this.isStreaming = true;
    this.offerAppointment = false;
    this.appointmentOfferAnswered = false;
    this.agentReplyPreview = null;
    this.scrollToBottom();
    this.cdr.markForCheck();

    const streamObserver = {
      next: (event: any) => this.handleStreamEvent(event),
      error: (err: any) => {
        this.thinkingSteps.forEach(s => s.done = true);
        this.notify.error('Connection error. Please try again.');
        this.isStreaming = false;
        this.cdr.markForCheck();
      },
      complete: () => {
        this.thinkingSteps.forEach(s => s.done = true);
        this.isStreaming = false;
        this.fetchSessions();
        this.cdr.markForCheck();
      }
    };

    this.agentMessageReceived = false;
    if (this.activeSessionId) {
      const req: ContinueRequest = { message: text, patient_id: null, human_approval: null };
      this.api.streamContinue(this.activeSessionId, req).subscribe(streamObserver);
    } else {
      const req: TriageRequest = { message: text, patient_id: null, session_id: null };
      this.api.streamTriage(req).subscribe(streamObserver);
    }
  }

  private formatStructuredReasoning(obj: any): string {
    const lines: string[] = [];
    if (typeof obj.reasoning === 'string' && obj.reasoning.trim()) {
      lines.push(obj.reasoning.trim());
    }
    const severity = obj.severity_score ?? obj.severity;
    const urgency = obj.urgency_level ?? obj.urgency;
    const concern = obj.primary_concern ?? obj.concern;
    if (severity !== undefined || urgency !== undefined || concern !== undefined) {
      if (severity !== undefined) {
        const numericSeverity = Number(severity);
        const severityLabel = Number.isNaN(numericSeverity) ? severity : `${numericSeverity}/10`;
        lines.push(`Severity: ${severityLabel}`);
      }
      if (urgency !== undefined) {
        lines.push(`Urgency: ${urgency}`);
      }
      if (concern !== undefined) {
        lines.push(`Primary concern: ${concern}`);
      }
    }
    if (typeof obj.summary === 'string' && obj.summary.trim()) {
      lines.push(obj.summary.trim());
    }
    if (lines.length) {
      return lines.join('\n');
    }
    const vals = Object.values(obj)
      .filter(v => typeof v === 'string')
      .map(v => v.trim())
      .filter(Boolean);
    return vals.join(' \n ');
  }

  private extractHumanReadable(raw: any): string {
    if (raw === null || raw === undefined) return '';
    if (typeof raw === 'object') {
      return this.formatStructuredReasoning(raw);
    }
    if (typeof raw === 'string') {
      const s = raw.trim();
      if (!s) return '';
      if ((s.startsWith('{') && s.endsWith('}')) || (s.startsWith('[') && s.endsWith(']'))) {
        try {
          const parsed = JSON.parse(s);
          if (parsed && typeof parsed === 'object') {
            return this.formatStructuredReasoning(parsed);
          }
        } catch (e) {
          // not json, fall through
        }
      }
      // Convert common separator patterns into newlines for better readability.
      return s.replace(/\s*·\s*/g, '\n').replace(/\s*—\s*/g, '\n');
    }
    return String(raw);
  }

  private buildFallbackReply(severity: number | string | null, urgency: string | null, concern: string | null, offerAppointment: boolean): string {
    const severityNum = typeof severity === 'string' ? Number(severity) : severity;
    const lines: string[] = [];

    if (concern) {
      lines.push(`Primary concern: ${concern}`);
    }
    if (severityNum !== null && !Number.isNaN(severityNum)) {
      lines.push(`Severity: ${severityNum}/10`);
    } else if (severity) {
      lines.push(`Severity: ${severity}`);
    }
    if (urgency) {
      lines.push(`Urgency: ${urgency}`);
    }

    if (severityNum !== null && !Number.isNaN(severityNum)) {
      if (severityNum >= 8) {
        lines.push('This appears high severity; please seek medical attention promptly.');
      } else if (severityNum >= 5) {
        lines.push('This appears moderate severity; I recommend following up with a clinician soon.');
      } else {
        lines.push('This appears low severity; monitor your symptoms and rest, but seek care if things worsen.');
      }
    } else {
      lines.push('I have assessed your symptoms and will provide the best next steps.');
    }

    if (offerAppointment) {
      lines.push('I can help book an appointment now if you would like.');
    }

    return lines.join('\n');
  }

  private handleStreamEvent(event: any) {
    if (!event || !event.type) return;

    if (event.type === 'step_start') {
      if (event.node === 'critic') {
        return;
      }
      const meta = NODE_META[event.node] || { label: event.node, icon: 'smart_toy' };
      if (this.thinkingSteps.length > 0) {
        this.thinkingSteps[this.thinkingSteps.length - 1].done = true;
      }
      const existingCount = this.thinkingSteps.filter(s => s.node === event.node).length;
      const label = existingCount > 0 ? `${meta.label} (pass ${existingCount + 1})` : meta.label;
      this.thinkingSteps.push({ node: event.node, label, icon: meta.icon, content: '', done: false });
      this.cdr.markForCheck();
      this.scrollToBottom();
      return;
    }

    if (event.type === 'thinking') {
      // Suppress interim streamed JSON for nodes that provide final human-readable step_content.
      const structuredNodes = ['triage', 'research', 'critic', 'scheduler'];
      if (event.node && structuredNodes.includes(event.node)) {
        return;
      }
      if (this.thinkingSteps.length > 0) {
        const target = event.node
          ? [...this.thinkingSteps].reverse().find(s => s.node === event.node)
          : this.thinkingSteps[this.thinkingSteps.length - 1];
        if (target) target.content += event.content;
      }
      this.cdr.markForCheck();
      return;
    }

    if (event.type === 'step_content') {
      if (event.node === 'critic') {
        return;
      }
      // Final per-node content — parse structured JSON blobs and prefer 'reasoning' or 'summary'
      const target = event.node
        ? [...this.thinkingSteps].reverse().find(s => s.node === event.node)
        : null;
      if (target) { target.content = this.extractHumanReadable(event.content); target.done = true; }
      this.cdr.markForCheck();
      return;
    }

    if (event.type === 'error') {
      this.thinkingSteps.forEach(s => s.done = true);
      this.messages.push({ role: 'system', content: `⚠️ Error: ${event.content}` });
      this.isStreaming = false;
      this.cdr.markForCheck();
      this.scrollToBottom();
      return;
    }

    if (event.type === 'message') {
      const content = this.extractHumanReadable(event.content);
      this.agentMessageReceived = true;
      this.agentReplyPreview = (this.agentReplyPreview ? this.agentReplyPreview + content : content);
      this.cdr.markForCheck();
      this.scrollToBottom();
      return;
    }

    if (event.type === 'metadata') {
      if (event.offer_appointment && !this.appointmentOfferAnswered) {
        this.offerAppointment = true;
      }
      this.requiresHumanReview = event.requires_human_review;
      if (event.session_id && !this.activeSessionId) {
        this.activeSessionId = event.session_id;
      }
      if (!this.agentMessageReceived) {
        this.agentReplyPreview = this.buildFallbackReply(
          event.triage_severity,
          event.triage_urgency,
          event.triage_concern,
          event.offer_appointment
        );
        this.agentMessageReceived = true;
      }
      this.thinkingSteps.forEach(s => s.done = true);
      this.thinkingExpanded = false;
      this.cdr.markForCheck();
      return;
    }
  }

  private scrollToBottom() {
    setTimeout(() => {
      try {
        this.chatScroll.nativeElement.scrollTop = this.chatScroll.nativeElement.scrollHeight;
      } catch(err) {}
    }, 50);
  }
}