import { trigger, transition, style, animate, query, group } from '@angular/animations';

export const routeAnimations = trigger('routeAnimations', [
  transition('* <=> *', [
    query(':enter, :leave', [
      style({ position: 'absolute', width: '100%', opacity: 0, transform: 'translateY(16px)' })
    ], { optional: true }),
    group([
      query(':leave',  [ animate('180ms ease-out', style({ opacity: 0, transform: 'translateY(-16px)' })) ], { optional: true }),
      query(':enter',  [ animate('280ms 80ms ease-out', style({ opacity: 1, transform: 'translateY(0)' })) ],  { optional: true })
    ])
  ])
]);

export const staggerAnimation = trigger('stagger', [
  transition('* => *', [
    query(':enter', [
      style({ opacity: 0, transform: 'translateY(12px)' }),
      animate('280ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
    ], { optional: true })
  ])
]);

export const cardEnter = trigger('cardEnter', [
  transition(':enter', [
    style({ opacity: 0, transform: 'scale(0.96) translateY(8px)' }),
    animate('320ms cubic-bezier(0.4,0,0.2,1)', style({ opacity: 1, transform: 'scale(1) translateY(0)' }))
  ])
]);
