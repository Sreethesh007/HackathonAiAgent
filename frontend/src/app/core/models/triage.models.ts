export type UrgencyLevel = 'routine' | 'urgent' | 'emergency' | 'unknown';

export const URGENCY_CONFIG: Record<string, { color: string; icon: string; label: string }> = {
  routine: { color: 'green', icon: 'check_circle', label: 'Routine' },
  urgent: { color: 'orange', icon: 'warning', label: 'Urgent' },
  emergency: { color: 'red', icon: 'error', label: 'Emergency' },
  unknown: { color: 'gray', icon: 'help_outline', label: 'Unknown' }
};

export interface TriageRequest {
  patient_id?: string | null;
  message: string;
  session_id?: string | null;
}

export interface ContinueRequest {
  patient_id?: string | null;
  message?: string;
  human_approval?: boolean | null;
}

export interface TriageResponse {
  session_id: string;
  response: string;
  severity_score: number;
  urgency_level: UrgencyLevel;
  primary_concern: string;
  sources: string[];
  guidelines_applied: string[];
  appointment_booked: boolean;
  appointment_id?: string | null;
  requires_human_review: boolean;
  quality_score: number;
  iteration_count: number;
}

export interface ContinueResponse extends TriageResponse {}

export interface SessionStatusResponse {
  session_id: string;
  status: string;
  last_updated: string;
  flow_status?: string;
  urgency_level?: UrgencyLevel;
  severity_score?: number;
  iteration_count?: number;
  patient_name?: string;
  patient_age?: string;
  primary_concern?: string;
  final_response?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  pipeline_ready?: boolean;
  llm_model?: string;
  environment?: string;
}

// ── Conversation persistence ──────────────────────────────────────────────────

/** A single stored conversation turn returned by GET /api/conversations/:sessionId */
export interface ConversationMessage {
  id: number;
  session_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  message: string;
  timestamp: string;
}

/** Payload for POST /api/conversations */
export interface SaveMessageRequest {
  session_id: string;
  user_id?: string | null;
  role: 'user' | 'assistant';
  message: string;
}

