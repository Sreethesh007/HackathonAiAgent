import { trigger, transition, style, query, animate, group } from '@angular/animations';

export const fadeAnimation = trigger('fadeAnimation', [
  transition('* => *', [
    query(':enter', [style({ opacity: 0, transform: 'translateY(10px)' })], { optional: true }),
    query(':leave', [style({ opacity: 1, transform: 'translateY(0)' })], { optional: true }),
    group([
      query(':leave', [animate('300ms ease-out', style({ opacity: 0, transform: 'translateY(-10px)' }))], { optional: true }),
      query(':enter', [animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))], { optional: true })
    ])
  ])
]);
