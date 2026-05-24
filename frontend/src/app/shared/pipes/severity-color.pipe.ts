import { Pipe, PipeTransform } from '@angular/core';
import { UrgencyLevel, URGENCY_CONFIG } from '../../core/models/triage.models';

@Pipe({ name: 'severityColor' })
export class SeverityColorPipe implements PipeTransform {
  transform(level: UrgencyLevel): string {
    return URGENCY_CONFIG[level]?.color ?? '#757575';
  }
}
