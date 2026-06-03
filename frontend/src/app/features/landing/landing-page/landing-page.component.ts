import {
  Component,
  ChangeDetectionStrategy,
  HostListener,
  OnInit,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { trigger, transition, style, animate, stagger, query } from '@angular/animations';
import { FadeInDirective } from '../../../shared/directives/fade-in.directive';

// ── Data models ──────────────────────────────────────────────────────────────

interface Feature {
  icon: string;
  title: string;
  description: string;
  accent: string;
  accentBg: string;
}

interface Testimonial {
  initials: string;
  name: string;
  role: string;
  institution: string;
  quote: string;
  avatarBg: string;
}

// ── Static content (swap for HTTP call to GET /api/features if needed) ───────

const FEATURES: Feature[] = [
  {
    icon: 'psychology',
    title: 'AI-Powered Triage',
    description:
      'Conversational AI assesses patient symptoms in real time, generating structured triage reports aligned with clinical protocols — reducing wait times by up to 40%.',
    accent: '#009688',
    accentBg: 'rgba(0,150,136,0.10)',
  },
  {
    icon: 'verified_user',
    title: 'Clinician Approval Workflow',
    description:
      'Every AI recommendation is reviewed and approved by a licensed clinician before reaching the patient — ensuring safety, accountability, and regulatory compliance.',
    accent: '#3b82f6',
    accentBg: 'rgba(59,130,246,0.10)',
  },
  {
    icon: 'event_available',
    title: 'Smart Appointment Booking',
    description:
      'Patients receive a tailored appointment slot based on urgency level. The system prioritises emergency cases automatically and notifies the care team in seconds.',
    accent: '#8b5cf6',
    accentBg: 'rgba(139,92,246,0.10)',
  },
  {
    icon: 'speed',
    title: 'Real-Time Dashboard',
    description:
      'Clinicians get a live overview of the triage queue, pending approvals, and appointment metrics — all in one unified, zero-refresh dashboard.',
    accent: '#f59e0b',
    accentBg: 'rgba(245,158,11,0.10)',
  },
];

const TESTIMONIALS: Testimonial[] = [
  {
    initials: 'SR',
    name: 'Dr. Sarah Richardson',
    role: 'Emergency Medicine Physician',
    institution: 'City General Hospital',
    quote:
      '"The AI triage agent has fundamentally changed how we manage patient intake. Our triage-to-treatment time dropped by 35% in the first month alone."',
    avatarBg: 'linear-gradient(135deg, #009688, #26a69a)',
  },
  {
    initials: 'MK',
    name: 'Marcus Kim',
    role: 'Head of Digital Health',
    institution: 'Northside Medical Centre',
    quote:
      '"We evaluated six triage platforms. This is the only one that genuinely integrates clinical oversight into the AI loop. The approval workflow is exactly what regulators want to see."',
    avatarBg: 'linear-gradient(135deg, #3b82f6, #6366f1)',
  },
  {
    initials: 'AP',
    name: 'Aisha Patel',
    role: 'Patient Experience Lead',
    institution: 'Riverside Community Clinic',
    quote:
      '"Patients love submitting symptoms from home and getting a confirmed appointment within minutes. Our no-show rate dropped 22% because people feel heard before they even arrive."',
    avatarBg: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

@Component({
  selector: 'app-landing-page',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, FadeInDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('heroIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(24px)' }),
        animate(
          '600ms 100ms cubic-bezier(0.4,0,0.2,1)',
          style({ opacity: 1, transform: 'translateY(0)' })
        ),
      ]),
    ]),
    trigger('subIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(16px)' }),
        animate(
          '600ms 280ms cubic-bezier(0.4,0,0.2,1)',
          style({ opacity: 1, transform: 'translateY(0)' })
        ),
      ]),
    ]),
    trigger('ctaIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(12px)' }),
        animate(
          '500ms 460ms cubic-bezier(0.4,0,0.2,1)',
          style({ opacity: 1, transform: 'translateY(0)' })
        ),
      ]),
    ]),
    trigger('badgeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.9)' }),
        animate(
          '400ms 80ms cubic-bezier(0.4,0,0.2,1)',
          style({ opacity: 1, transform: 'scale(1)' })
        ),
      ]),
    ]),
  ],
  template: `
    <div class="landing-root" [class.nav-scrolled]="scrolled()">

      <!-- ═══════════════════════ NAVBAR ═══════════════════════ -->
      <header class="navbar" role="banner" aria-label="Site navigation">
        <div class="navbar-inner">

          <a class="brand" routerLink="/" aria-label="Healthcare Triage Agent home">
            <div class="brand-icon-wrap" aria-hidden="true">
              <mat-icon class="brand-icon">local_hospital</mat-icon>
            </div>
            <div class="brand-text">
              <span class="brand-title">Healthcare</span>
              <span class="brand-sub">Triage Agent</span>
            </div>
          </a>

          <nav class="nav-links" aria-label="Primary navigation">
            <a class="nav-link" id="navFeatures" (click)="scrollTo('features')" role="button" style="cursor:pointer">Features</a>
            <a class="nav-link" id="navTestimonials" (click)="scrollTo('testimonials')" role="button" style="cursor:pointer">Testimonials</a>
            <a class="nav-link" id="navContact" (click)="scrollTo('footer')" role="button" style="cursor:pointer">Contact</a>
          </nav>

          <div class="nav-cta-group">
            <a routerLink="/login" class="nav-login-btn" id="navLogin"
               aria-label="Sign in to your account">Sign In</a>
            <a routerLink="/signup" class="nav-cta-btn" id="navGetStarted"
               aria-label="Create a free account">Get Started</a>
          </div>

          <!-- Mobile hamburger -->
          <button class="hamburger" (click)="mobileOpen.set(!mobileOpen())"
                  [attr.aria-expanded]="mobileOpen()"
                  aria-label="Toggle mobile navigation"
                  aria-controls="mobile-menu">
            <mat-icon>{{ mobileOpen() ? 'close' : 'menu' }}</mat-icon>
          </button>
        </div>

        <!-- Mobile drawer -->
        <div id="mobile-menu" class="mobile-menu" [class.mobile-menu--open]="mobileOpen()"
             role="navigation" aria-label="Mobile navigation">
          <a class="mobile-link" (click)="scrollTo('features'); mobileOpen.set(false)" role="button" style="cursor:pointer">Features</a>
          <a class="mobile-link" (click)="scrollTo('testimonials'); mobileOpen.set(false)" role="button" style="cursor:pointer">Testimonials</a>
          <a class="mobile-link" (click)="scrollTo('footer'); mobileOpen.set(false)" role="button" style="cursor:pointer">Contact</a>
          <a routerLink="/login" class="mobile-link" (click)="mobileOpen.set(false)">Sign In</a>
          <a routerLink="/signup" class="mobile-cta" (click)="mobileOpen.set(false)">Get Started →</a>
        </div>
      </header>

      <!-- ═══════════════════════ HERO ═══════════════════════ -->
      <section class="hero" aria-labelledby="heroHeadline" role="main">
        <div class="hero-bg" aria-hidden="true">
          <div class="hero-orb hero-orb--1"></div>
          <div class="hero-orb hero-orb--2"></div>
          <div class="hero-orb hero-orb--3"></div>
          <div class="hero-grid-overlay"></div>
        </div>

        <div class="hero-content">
          <div class="hero-badge" [@badgeIn] aria-label="AI-Powered Healthcare Platform">
            <mat-icon class="hero-badge-icon" aria-hidden="true">auto_awesome</mat-icon>
            AI-Powered Healthcare Platform
          </div>

          <h1 class="hero-headline" id="heroHeadline" [@heroIn]>
            Intelligent Triage.<br>
            <span class="hero-headline--accent">Faster Care.</span>
          </h1>

          <p class="hero-sub" [@subIn]>
            Healthcare Triage Agent combines conversational AI with clinical oversight
            to assess patients, prioritise urgency, and book appointments — all before
            they step through your door.
          </p>

          <div class="hero-cta-row" [@ctaIn] role="group" aria-label="Call to action buttons">
            <a routerLink="/signup" class="btn-primary" id="heroGetStarted"
               aria-label="Get started for free">
              <mat-icon aria-hidden="true">rocket_launch</mat-icon>
              Start Triage Now
            </a>
            <a (click)="scrollTo('features')" class="btn-ghost" id="heroLearnMore"
               aria-label="Learn more about features" role="button" style="cursor:pointer">
              Explore Features
              <mat-icon aria-hidden="true">arrow_downward</mat-icon>
            </a>
          </div>

          <div class="hero-stats" role="list" aria-label="Key statistics">
            <div class="hero-stat" role="listitem">
              <span class="hero-stat-num">40%</span>
              <span class="hero-stat-label">Faster Triage</span>
            </div>
            <div class="hero-stat-divider" aria-hidden="true"></div>
            <div class="hero-stat" role="listitem">
              <span class="hero-stat-num">99.9%</span>
              <span class="hero-stat-label">Uptime SLA</span>
            </div>
            <div class="hero-stat-divider" aria-hidden="true"></div>
            <div class="hero-stat" role="listitem">
              <span class="hero-stat-num">HIPAA</span>
              <span class="hero-stat-label">Compliant</span>
            </div>
          </div>
        </div>

        <div class="hero-scroll-cue" aria-hidden="true">
          <div class="scroll-dot"></div>
        </div>
      </section>

      <!-- ═══════════════════════ FEATURES ═══════════════════════ -->
      <section class="section features-section" id="features"
               aria-labelledby="featuresHeading">
        <div class="section-inner">

          <div class="section-header" appFadeIn>
            <span class="section-eyebrow" aria-hidden="true">What We Do</span>
            <h2 class="section-title" id="featuresHeading">
              Built for the Speed of Emergency Care
            </h2>
            <p class="section-sub">
              Four integrated capabilities that transform how your team triages,
              reviews, and coordinates patient care.
            </p>
          </div>

          <div class="features-grid" role="list" aria-label="Platform features">
            @for (f of features; track f.title) {
              <article class="feature-card u-hover-lift" appFadeIn role="listitem"
                       [attr.aria-label]="f.title">
                <div class="feature-icon-wrap"
                     [style.background]="f.accentBg"
                     [style.border]="'1px solid ' + f.accentBg.replace('0.10','0.25')"
                     aria-hidden="true">
                  <mat-icon class="feature-icon" [style.color]="f.accent">
                    {{ f.icon }}
                  </mat-icon>
                </div>
                <h3 class="feature-title">{{ f.title }}</h3>
                <p class="feature-desc">{{ f.description }}</p>
                <div class="feature-tag" [style.color]="f.accent"
                     [style.background]="f.accentBg" aria-hidden="true">
                  <mat-icon style="font-size:14px;width:14px;height:14px;">
                    check_circle
                  </mat-icon>
                  Included
                </div>
              </article>
            }
          </div>

        </div>
      </section>

      <!-- ═══════════════════════ WORKFLOW STRIP ═══════════════════════ -->
      <section class="workflow-strip" aria-label="How it works">
        <div class="section-inner">
          <div class="workflow-steps" appFadeIn role="list"
               aria-label="Three-step workflow">
            <div class="workflow-step" role="listitem">
              <div class="workflow-num" aria-label="Step 1">1</div>
              <div class="workflow-text">
                <strong>Patient submits symptoms</strong>
                <span>via conversational AI chat — any device, any time</span>
              </div>
            </div>
            <div class="workflow-arrow" aria-hidden="true">
              <mat-icon>east</mat-icon>
            </div>
            <div class="workflow-step" role="listitem">
              <div class="workflow-num" aria-label="Step 2">2</div>
              <div class="workflow-text">
                <strong>Clinician reviews &amp; approves</strong>
                <span>AI-generated triage report before it reaches the patient</span>
              </div>
            </div>
            <div class="workflow-arrow" aria-hidden="true">
              <mat-icon>east</mat-icon>
            </div>
            <div class="workflow-step" role="listitem">
              <div class="workflow-num" aria-label="Step 3">3</div>
              <div class="workflow-text">
                <strong>Appointment auto-booked</strong>
                <span>based on urgency — patient gets confirmation instantly</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════════════════════ TESTIMONIALS ═══════════════════════ -->
      <section class="section testimonials-section" id="testimonials"
               aria-labelledby="testimonialsHeading">
        <div class="section-inner">

          <div class="section-header" appFadeIn>
            <span class="section-eyebrow" aria-hidden="true">Testimonials</span>
            <h2 class="section-title" id="testimonialsHeading">
              Trusted Across Healthcare Settings
            </h2>
            <p class="section-sub">
              From emergency departments to community clinics — here is what
              care teams are saying.
            </p>
          </div>

          <div class="testimonials-grid" role="list"
               aria-label="Testimonials from healthcare professionals">
            @for (t of testimonials; track t.name) {
              <blockquote class="testimonial-card u-hover-lift" appFadeIn role="listitem">
                <div class="testimonial-quote-icon" aria-hidden="true">&ldquo;</div>
                <p class="testimonial-text">{{ t.quote }}</p>
                <footer class="testimonial-footer">
                  <div class="testimonial-avatar"
                       [style.background]="t.avatarBg"
                       [attr.aria-label]="t.name + ' avatar'">
                    {{ t.initials }}
                  </div>
                  <div class="testimonial-meta">
                    <span class="testimonial-name">{{ t.name }}</span>
                    <span class="testimonial-role">{{ t.role }}</span>
                    <span class="testimonial-institution">{{ t.institution }}</span>
                  </div>
                </footer>
              </blockquote>
            }
          </div>

        </div>
      </section>

      <!-- ═══════════════════════ CTA BANNER ═══════════════════════ -->
      <section class="cta-banner" aria-label="Call to action — get started">
        <div class="cta-banner-bg" aria-hidden="true">
          <div class="cta-orb cta-orb--1"></div>
          <div class="cta-orb cta-orb--2"></div>
        </div>
        <div class="cta-banner-content" appFadeIn>
          <h2 class="cta-title">Ready to Transform Patient Triage?</h2>
          <p class="cta-sub">
            Join healthcare providers already delivering faster, safer triage
            with AI-powered clinical decision support.
          </p>
          <div class="cta-actions" role="group" aria-label="Sign-up actions">
            <a routerLink="/signup" class="btn-primary btn-primary--large"
               id="ctaBannerSignup" aria-label="Create your free account">
              <mat-icon aria-hidden="true">person_add</mat-icon>
              Create Free Account
            </a>
            <a routerLink="/login" class="btn-ghost btn-ghost--light"
               id="ctaBannerLogin" aria-label="Sign in to existing account">
              Already have an account? Sign In →
            </a>
          </div>
        </div>
      </section>

      <!-- ═══════════════════════ FOOTER ═══════════════════════ -->
      <footer class="site-footer" id="footer" role="contentinfo"
              aria-label="Site footer">
        <div class="footer-inner">

          <div class="footer-brand" aria-label="Brand information">
            <div class="footer-brand-logo" aria-hidden="true">
              <div class="footer-icon-wrap">
                <mat-icon class="footer-icon">local_hospital</mat-icon>
              </div>
              <div>
                <span class="footer-brand-title">Healthcare Triage Agent</span>
                <span class="footer-brand-sub">AI-Powered Clinical Decision Support</span>
              </div>
            </div>
            <p class="footer-tagline">
              Empowering clinicians with intelligent, human-approved AI triage
              that puts patient safety first.
            </p>
            <div class="footer-badges" aria-label="Compliance badges">
              <span class="footer-badge">HIPAA Compliant</span>
              <span class="footer-badge">SOC 2 Type II</span>
            </div>
          </div>

          <nav class="footer-nav" aria-label="Footer navigation">
            <div class="footer-nav-col">
              <h3 class="footer-nav-heading">Platform</h3>
              <ul class="footer-nav-list" role="list">
                <li><a (click)="scrollTo('features')" class="footer-link" role="button" style="cursor:pointer">Features</a></li>
                <li><a (click)="scrollTo('testimonials')" class="footer-link" role="button" style="cursor:pointer">Testimonials</a></li>
                <li><a routerLink="/signup" class="footer-link">Get Started</a></li>
                <li><a routerLink="/login" class="footer-link">Sign In</a></li>
              </ul>
            </div>
            <div class="footer-nav-col">
              <h3 class="footer-nav-heading">Contact</h3>
              <ul class="footer-nav-list" role="list">
                <li>
                  <a href="mailto:support@healthcaretriage.ai"
                     class="footer-link footer-link--icon"
                     aria-label="Email support">
                    <mat-icon aria-hidden="true">email</mat-icon>
                    support&#64;healthcaretriage.ai
                  </a>
                </li>
                <li>
                  <a href="tel:+18005550199"
                     class="footer-link footer-link--icon"
                     aria-label="Call support">
                    <mat-icon aria-hidden="true">phone</mat-icon>
                    +1 800 555 0199
                  </a>
                </li>
                <li>
                  <span class="footer-link footer-link--icon footer-link--static"
                        aria-label="Office location">
                    <mat-icon aria-hidden="true">location_on</mat-icon>
                    San Francisco, CA
                  </span>
                </li>
              </ul>
            </div>
          </nav>

        </div>

        <div class="footer-bottom" aria-label="Legal and copyright">
          <span class="footer-copy">
            &copy; {{ currentYear }} Healthcare Triage Agent. All rights reserved.
          </span>
          <div class="footer-legal" role="list" aria-label="Legal links">
            <a class="footer-legal-link" href="#" role="listitem">Privacy Policy</a>
            <a class="footer-legal-link" href="#" role="listitem">Terms of Service</a>
            <a class="footer-legal-link" href="#" role="listitem">HIPAA Notice</a>
          </div>
        </div>
      </footer>

    </div>
  `,
  styles: [`
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Host ──────────────────────────────────────────────────── */
    :host {
      display: block;
      font-family: 'Inter', 'Roboto', sans-serif;
      -webkit-font-smoothing: antialiased;
    }

    .landing-root {
      min-height: 100vh;
      background: #f4f7fb;
      color: #1f2937;
      scroll-behavior: smooth;
    }

    /* ── Shared Section Layout ─────────────────────────────────── */
    .section { padding: 96px 24px; }
    .section-inner {
      max-width: 1160px;
      margin: 0 auto;
    }
    .section-header {
      text-align: center;
      margin-bottom: 56px;
    }
    .section-eyebrow {
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #009688;
      background: rgba(0,150,136,0.10);
      border: 1px solid rgba(0,150,136,0.20);
      border-radius: 999px;
      padding: 4px 14px;
      margin-bottom: 16px;
    }
    .section-title {
      font-size: clamp(1.7rem, 3vw, 2.4rem);
      font-weight: 800;
      color: #1f2937;
      line-height: 1.2;
      margin: 0 0 16px;
      letter-spacing: -0.5px;
    }
    .section-sub {
      font-size: 1.05rem;
      color: #5f6b7a;
      max-width: 560px;
      margin: 0 auto;
      line-height: 1.7;
    }

    /* ── Hover lift (matching _utilities.scss) ─────────────────── */
    .u-hover-lift {
      transition: transform 0.22s cubic-bezier(0.4,0,0.2,1),
                  box-shadow 0.22s cubic-bezier(0.4,0,0.2,1);
    }
    .u-hover-lift:hover {
      transform: translateY(-5px);
      box-shadow: 0 12px 36px rgba(0,0,0,0.10) !important;
    }

    /* ═══════════════════════════════════════════════════════════
       NAVBAR
    ═══════════════════════════════════════════════════════════ */
    .navbar {
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 1000;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(0,0,0,0.06);
      transition: box-shadow 0.25s ease, background 0.25s ease;
    }
    .nav-scrolled .navbar,
    .navbar:has(+ *) { /* fallback */ }
    .landing-root.nav-scrolled .navbar {
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
      background: rgba(255,255,255,0.98);
    }

    .navbar-inner {
      max-width: 1160px;
      margin: 0 auto;
      height: 68px;
      display: flex;
      align-items: center;
      padding: 0 24px;
      gap: 32px;
    }

    /* Brand */
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      flex-shrink: 0;
    }
    .brand-icon-wrap {
      width: 40px;
      height: 40px;
      border-radius: 11px;
      background: linear-gradient(135deg, #26a69a, #009688);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0,150,136,0.30);
    }
    .brand-icon {
      color: #ffffff;
      font-size: 20px !important;
      width: 20px !important;
      height: 20px !important;
    }
    .brand-text { display: flex; flex-direction: column; }
    .brand-title {
      font-size: 14px;
      font-weight: 700;
      color: #1f2937;
      line-height: 1;
    }
    .brand-sub {
      font-size: 10px;
      font-weight: 400;
      color: #009688;
      margin-top: 2px;
    }

    /* Nav links */
    .nav-links {
      display: flex;
      gap: 6px;
      margin-left: auto;
    }
    .nav-link {
      font-size: 0.9rem;
      font-weight: 500;
      color: #4b5563;
      text-decoration: none;
      padding: 8px 14px;
      border-radius: 10px;
      transition: color 0.18s ease, background 0.18s ease;
    }
    .nav-link:hover {
      color: #009688;
      background: rgba(0,150,136,0.07);
    }

    /* CTA group */
    .nav-cta-group {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }
    .nav-login-btn {
      font-size: 0.9rem;
      font-weight: 500;
      color: #1f2937;
      text-decoration: none;
      padding: 9px 18px;
      border-radius: 10px;
      border: 1px solid #e5e7eb;
      background: #ffffff;
      transition: all 0.18s ease;
    }
    .nav-login-btn:hover {
      border-color: #009688;
      color: #009688;
    }
    .nav-cta-btn {
      font-size: 0.9rem;
      font-weight: 600;
      color: #ffffff;
      text-decoration: none;
      padding: 9px 20px;
      border-radius: 10px;
      background: linear-gradient(135deg, #26a69a, #009688);
      box-shadow: 0 4px 14px rgba(0,150,136,0.30);
      transition: all 0.2s ease;
    }
    .nav-cta-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(0,150,136,0.40);
    }

    /* Hamburger */
    .hamburger {
      display: none;
      width: 42px;
      height: 42px;
      border: none;
      background: transparent;
      border-radius: 10px;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #374151;
      margin-left: auto;
      transition: background 0.18s ease;
    }
    .hamburger:hover { background: #f3f4f6; }
    .hamburger mat-icon { font-size: 22px !important; width: 22px !important; height: 22px !important; }

    /* Mobile menu */
    .mobile-menu {
      display: none;
      flex-direction: column;
      gap: 2px;
      padding: 12px 20px 20px;
      background: #ffffff;
      border-top: 1px solid #f3f4f6;
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
    }
    .mobile-menu--open {
      max-height: 400px;
    }
    .mobile-link {
      font-size: 0.95rem;
      font-weight: 500;
      color: #374151;
      text-decoration: none;
      padding: 11px 14px;
      border-radius: 10px;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .mobile-link:hover { background: rgba(0,150,136,0.08); color: #009688; }
    .mobile-cta {
      margin-top: 8px;
      font-size: 0.95rem;
      font-weight: 700;
      color: #ffffff;
      text-decoration: none;
      padding: 13px 14px;
      border-radius: 12px;
      background: linear-gradient(135deg, #26a69a, #009688);
      text-align: center;
    }

    /* ═══════════════════════════════════════════════════════════
       HERO
    ═══════════════════════════════════════════════════════════ */
    .hero {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      padding: 100px 24px 60px;
      background: linear-gradient(160deg, #e8f5f3 0%, #f4f7fb 50%, #eef4ff 100%);
    }

    /* Background orbs */
    .hero-bg { position: absolute; inset: 0; pointer-events: none; }
    .hero-orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(60px);
    }
    .hero-orb--1 {
      width: 640px; height: 640px;
      top: -200px; left: -200px;
      background: radial-gradient(circle, rgba(0,150,136,0.18) 0%, transparent 70%);
      animation: orbFloat 8s ease-in-out infinite;
    }
    .hero-orb--2 {
      width: 480px; height: 480px;
      bottom: -120px; right: -120px;
      background: radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%);
      animation: orbFloat 10s ease-in-out infinite reverse;
    }
    .hero-orb--3 {
      width: 320px; height: 320px;
      top: 40%; left: 55%;
      background: radial-gradient(circle, rgba(139,92,246,0.09) 0%, transparent 70%);
      animation: orbFloat 12s ease-in-out infinite;
    }
    .hero-grid-overlay {
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(0,150,136,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,150,136,0.04) 1px, transparent 1px);
      background-size: 48px 48px;
    }
    @keyframes orbFloat {
      0%, 100% { transform: translateY(0px) scale(1); }
      50%       { transform: translateY(-28px) scale(1.03); }
    }

    /* Hero content */
    .hero-content {
      position: relative;
      z-index: 1;
      text-align: center;
      max-width: 760px;
    }

    .hero-badge {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: #009688;
      background: rgba(0,150,136,0.10);
      border: 1px solid rgba(0,150,136,0.22);
      border-radius: 999px;
      padding: 6px 16px;
      margin-bottom: 28px;
    }
    .hero-badge-icon {
      font-size: 15px !important;
      width: 15px !important;
      height: 15px !important;
    }

    .hero-headline {
      font-size: clamp(2.4rem, 6vw, 4rem);
      font-weight: 800;
      color: #1f2937;
      line-height: 1.12;
      letter-spacing: -1.5px;
      margin: 0 0 24px;
    }
    .hero-headline--accent {
      background: linear-gradient(135deg, #009688, #26a69a 50%, #4db6ac);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .hero-sub {
      font-size: 1.15rem;
      color: #5f6b7a;
      line-height: 1.75;
      max-width: 600px;
      margin: 0 auto 40px;
    }

    /* CTA row */
    .hero-cta-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 56px;
    }

    /* Primary button — matches .login-btn from auth */
    .btn-primary {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      height: 52px;
      padding: 0 28px;
      font-size: 1rem;
      font-weight: 600;
      color: #ffffff;
      text-decoration: none;
      border-radius: 14px;
      background: linear-gradient(135deg, #26a69a, #009688);
      box-shadow: 0 6px 20px rgba(0,150,136,0.35);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .btn-primary mat-icon {
      font-size: 20px !important;
      width: 20px !important;
      height: 20px !important;
    }
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 28px rgba(0,150,136,0.45);
    }
    .btn-primary--large { height: 56px; font-size: 1.05rem; padding: 0 32px; }

    /* Ghost button */
    .btn-ghost {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 52px;
      padding: 0 24px;
      font-size: 0.95rem;
      font-weight: 500;
      color: #374151;
      text-decoration: none;
      border-radius: 14px;
      border: 1.5px solid #e5e7eb;
      background: rgba(255,255,255,0.8);
      backdrop-filter: blur(4px);
      transition: all 0.2s ease;
    }
    .btn-ghost mat-icon {
      font-size: 18px !important;
      width: 18px !important;
      height: 18px !important;
    }
    .btn-ghost:hover {
      border-color: #009688;
      color: #009688;
      background: rgba(0,150,136,0.05);
    }
    .btn-ghost--light {
      color: rgba(255,255,255,0.88);
      border-color: rgba(255,255,255,0.30);
      background: rgba(255,255,255,0.10);
    }
    .btn-ghost--light:hover {
      background: rgba(255,255,255,0.20);
      border-color: rgba(255,255,255,0.60);
      color: #ffffff;
    }

    /* Stats row */
    .hero-stats {
      display: inline-flex;
      align-items: center;
      gap: 28px;
      background: rgba(255,255,255,0.75);
      border: 1px solid rgba(0,0,0,0.06);
      border-radius: 16px;
      padding: 18px 32px;
      backdrop-filter: blur(8px);
    }
    .hero-stat { display: flex; flex-direction: column; align-items: center; gap: 3px; }
    .hero-stat-num {
      font-size: 1.5rem;
      font-weight: 800;
      color: #009688;
      line-height: 1;
    }
    .hero-stat-label {
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #6b7280;
    }
    .hero-stat-divider {
      width: 1px;
      height: 36px;
      background: rgba(0,0,0,0.10);
    }

    /* Scroll cue */
    .hero-scroll-cue {
      position: absolute;
      bottom: 32px;
      left: 50%;
      transform: translateX(-50%);
    }
    .scroll-dot {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 2px solid rgba(0,150,136,0.40);
      display: flex;
      align-items: center;
      justify-content: center;
      animation: scrollBounce 2s ease-in-out infinite;
    }
    .scroll-dot::after {
      content: '';
      width: 6px;
      height: 6px;
      background: #009688;
      border-radius: 50%;
      animation: scrollBounce 2s ease-in-out infinite;
    }
    @keyframes scrollBounce {
      0%, 100% { transform: translateY(0); opacity: 1; }
      50%       { transform: translateY(6px); opacity: 0.5; }
    }

    /* ═══════════════════════════════════════════════════════════
       FEATURES
    ═══════════════════════════════════════════════════════════ */
    .features-section { background: #ffffff; }

    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 22px;
    }

    /* Feature card — styled like clinician stat-card */
    .feature-card {
      background: #ffffff;
      border: 1px solid #e8edf2;
      border-radius: 18px;
      padding: 28px 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.03);
      cursor: default;
    }
    .feature-icon-wrap {
      width: 52px;
      height: 52px;
      border-radius: 13px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 18px;
    }
    .feature-icon {
      font-size: 26px !important;
      width: 26px !important;
      height: 26px !important;
    }
    .feature-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #1f2937;
      margin: 0 0 10px;
    }
    .feature-desc {
      font-size: 0.9rem;
      color: #5f6b7a;
      line-height: 1.65;
      margin: 0 0 18px;
    }
    .feature-tag {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.76rem;
      font-weight: 600;
      letter-spacing: 0.03em;
      padding: 4px 10px;
      border-radius: 999px;
    }

    /* ═══════════════════════════════════════════════════════════
       WORKFLOW STRIP
    ═══════════════════════════════════════════════════════════ */
    .workflow-strip {
      background: linear-gradient(135deg, #f0faf9 0%, #e8f5e9 100%);
      border-top: 1px solid rgba(0,150,136,0.10);
      border-bottom: 1px solid rgba(0,150,136,0.10);
      padding: 56px 24px;
    }
    .workflow-steps {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .workflow-step {
      display: flex;
      align-items: flex-start;
      gap: 16px;
      max-width: 280px;
    }
    .workflow-num {
      width: 40px;
      height: 40px;
      flex-shrink: 0;
      border-radius: 50%;
      background: linear-gradient(135deg, #26a69a, #009688);
      color: #ffffff;
      font-size: 1rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0,150,136,0.30);
    }
    .workflow-text {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .workflow-text strong {
      font-size: 0.95rem;
      font-weight: 700;
      color: #1f2937;
    }
    .workflow-text span {
      font-size: 0.84rem;
      color: #5f6b7a;
      line-height: 1.5;
    }
    .workflow-arrow {
      color: #009688;
      opacity: 0.5;
      margin-top: 10px;
    }
    .workflow-arrow mat-icon {
      font-size: 24px !important;
      width: 24px !important;
      height: 24px !important;
    }

    /* ═══════════════════════════════════════════════════════════
       TESTIMONIALS
    ═══════════════════════════════════════════════════════════ */
    .testimonials-section { background: #f4f7fb; }

    .testimonials-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 22px;
    }

    /* Testimonial card — styled like info-card from clinician overview */
    .testimonial-card {
      background: #ffffff;
      border: 1px solid #e8edf2;
      border-radius: 18px;
      padding: 28px 24px 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.03);
      margin: 0;
      position: relative;
    }
    .testimonial-quote-icon {
      position: absolute;
      top: 16px;
      right: 22px;
      font-size: 4rem;
      font-family: Georgia, serif;
      color: rgba(0,150,136,0.15);
      line-height: 1;
      font-weight: 700;
    }
    .testimonial-text {
      font-size: 0.92rem;
      color: #374151;
      line-height: 1.7;
      margin: 0 0 22px;
      font-style: italic;
    }
    .testimonial-footer {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    /* Avatar — matches sidebar user-avatar */
    .testimonial-avatar {
      width: 44px;
      height: 44px;
      flex-shrink: 0;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-size: 13px;
      font-weight: 700;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .testimonial-meta {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .testimonial-name {
      font-size: 0.9rem;
      font-weight: 700;
      color: #1f2937;
    }
    .testimonial-role {
      font-size: 0.78rem;
      font-weight: 500;
      color: #009688;
    }
    .testimonial-institution {
      font-size: 0.76rem;
      color: #9ca3af;
    }

    /* ═══════════════════════════════════════════════════════════
       CTA BANNER
    ═══════════════════════════════════════════════════════════ */
    .cta-banner {
      position: relative;
      overflow: hidden;
      padding: 80px 24px;
      background: linear-gradient(135deg, #00695c 0%, #009688 50%, #26a69a 100%);
    }
    .cta-banner-bg {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .cta-orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(50px);
    }
    .cta-orb--1 {
      width: 400px; height: 400px;
      top: -150px; left: -100px;
      background: rgba(255,255,255,0.08);
    }
    .cta-orb--2 {
      width: 300px; height: 300px;
      bottom: -100px; right: -80px;
      background: rgba(255,255,255,0.06);
    }
    .cta-banner-content {
      position: relative;
      z-index: 1;
      text-align: center;
      max-width: 620px;
      margin: 0 auto;
    }
    .cta-title {
      font-size: clamp(1.6rem, 3vw, 2.2rem);
      font-weight: 800;
      color: #ffffff;
      margin: 0 0 16px;
      letter-spacing: -0.5px;
    }
    .cta-sub {
      font-size: 1rem;
      color: rgba(255,255,255,0.82);
      line-height: 1.7;
      margin: 0 0 36px;
    }
    .cta-actions {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .cta-actions .btn-primary {
      background: #ffffff;
      color: #009688;
      box-shadow: 0 6px 20px rgba(0,0,0,0.20);
    }
    .cta-actions .btn-primary:hover {
      box-shadow: 0 10px 28px rgba(0,0,0,0.30);
      transform: translateY(-2px);
    }
    .cta-actions .btn-primary mat-icon { color: #009688; }

    /* ═══════════════════════════════════════════════════════════
       FOOTER — matches sidebar gradient
    ═══════════════════════════════════════════════════════════ */
    .site-footer {
      background: linear-gradient(180deg, #00695c 0%, #004d40 100%);
      color: rgba(255,255,255,0.80);
    }
    .footer-inner {
      max-width: 1160px;
      margin: 0 auto;
      padding: 64px 24px 48px;
      display: flex;
      gap: 48px;
      flex-wrap: wrap;
    }
    .footer-brand { flex: 1; min-width: 240px; }
    .footer-brand-logo {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    .footer-icon-wrap {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: rgba(255,255,255,0.14);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .footer-icon {
      color: #ffffff;
      font-size: 22px !important;
      width: 22px !important;
      height: 22px !important;
    }
    .footer-brand-title {
      display: block;
      font-size: 0.96rem;
      font-weight: 700;
      color: #ffffff;
    }
    .footer-brand-sub {
      display: block;
      font-size: 0.78rem;
      color: rgba(255,255,255,0.60);
      margin-top: 2px;
    }
    .footer-tagline {
      font-size: 0.86rem;
      color: rgba(255,255,255,0.65);
      line-height: 1.65;
      margin: 0 0 20px;
      max-width: 300px;
    }
    .footer-badges { display: flex; gap: 8px; flex-wrap: wrap; }
    .footer-badge {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.12);
      color: rgba(255,255,255,0.80);
      border: 1px solid rgba(255,255,255,0.18);
    }

    /* Footer nav */
    .footer-nav {
      display: flex;
      gap: 48px;
      flex-wrap: wrap;
    }
    .footer-nav-col { min-width: 140px; }
    .footer-nav-heading {
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.10em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.55);
      margin: 0 0 16px;
    }
    .footer-nav-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .footer-link {
      font-size: 0.88rem;
      color: rgba(255,255,255,0.72);
      text-decoration: none;
      transition: color 0.18s ease;
    }
    .footer-link:hover { color: #ffffff; }
    .footer-link--icon {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .footer-link--icon mat-icon {
      font-size: 16px !important;
      width: 16px !important;
      height: 16px !important;
      opacity: 0.70;
    }
    .footer-link--static { cursor: default; }
    .footer-link--static:hover { color: rgba(255,255,255,0.72); }

    /* Footer bottom */
    .footer-bottom {
      max-width: 1160px;
      margin: 0 auto;
      padding: 20px 24px;
      border-top: 1px solid rgba(255,255,255,0.10);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .footer-copy { font-size: 0.82rem; color: rgba(255,255,255,0.50); }
    .footer-legal { display: flex; gap: 20px; }
    .footer-legal-link {
      font-size: 0.82rem;
      color: rgba(255,255,255,0.50);
      text-decoration: none;
      transition: color 0.18s ease;
    }
    .footer-legal-link:hover { color: rgba(255,255,255,0.85); }

    /* ═══════════════════════════════════════════════════════════
       ACCESSIBILITY
    ═══════════════════════════════════════════════════════════ */
    :focus-visible {
      outline: 2px solid #009688;
      outline-offset: 3px;
      border-radius: 4px;
    }

    /* ═══════════════════════════════════════════════════════════
       RESPONSIVE
    ═══════════════════════════════════════════════════════════ */

    /* ≤ 768px — tablet / large mobile */
    @media (max-width: 768px) {
      .nav-links, .nav-cta-group { display: none; }
      .hamburger { display: flex; }
      .mobile-menu { display: flex; }

      .hero-headline { letter-spacing: -0.5px; }
      .hero-stats { gap: 18px; padding: 14px 20px; flex-wrap: wrap; justify-content: center; }
      .hero-stat-divider { display: none; }

      .section { padding: 64px 20px; }
      .features-grid { grid-template-columns: 1fr; }
      .testimonials-grid { grid-template-columns: 1fr; }

      .workflow-steps { flex-direction: column; align-items: flex-start; max-width: 360px; margin: 0 auto; }
      .workflow-arrow { transform: rotate(90deg); margin-left: 10px; }

      .footer-inner { flex-direction: column; gap: 32px; padding: 48px 20px 36px; }
      .footer-nav { gap: 32px; }
      .footer-bottom { flex-direction: column; align-items: flex-start; gap: 12px; }
    }

    /* ≤ 480px — small mobile */
    @media (max-width: 480px) {
      .hero { padding: 90px 18px 50px; }
      .hero-cta-row { flex-direction: column; align-items: stretch; gap: 12px; }
      .btn-primary, .btn-ghost { justify-content: center; }
      .cta-actions { flex-direction: column; align-items: stretch; gap: 12px; }
    }
  `],
})
export class LandingPageComponent implements OnInit {
  readonly features = FEATURES;
  readonly testimonials = TESTIMONIALS;
  readonly currentYear = new Date().getFullYear();

  scrolled = signal(false);
  mobileOpen = signal(false);

  ngOnInit(): void { }

  scrollTo(sectionId: string): void {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  @HostListener('window:scroll')
  onScroll(): void {
    this.scrolled.set(window.scrollY > 20);
  }
}
