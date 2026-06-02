import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  TriageRequest, TriageResponse,
  ContinueRequest, ContinueResponse,
  SessionStatusResponse, HealthResponse,
  ConversationMessage, SaveMessageRequest
} from '../models/triage.models';


@Injectable({ providedIn: 'root' })
export class TriageApiService {
  private base = '/api';

  constructor(private http: HttpClient) { }

  startTriage(req: TriageRequest): Observable<TriageResponse> {
    return this.http.post<TriageResponse>(`${this.base}/triage`, req);
  }

  streamTriage(req: TriageRequest): Observable<any> {
    return this.createFetchStream(`${this.base}/triage`, req);
  }

  continueTriage(sessionId: string, req: ContinueRequest): Observable<ContinueResponse> {
    return this.http.post<ContinueResponse>(`${this.base}/triage/${sessionId}/continue`, req);
  }

  streamContinue(sessionId: string, req: ContinueRequest): Observable<any> {
    return this.createFetchStream(`${this.base}/triage/${sessionId}/continue`, req);
  }

  getSessionStatus(sessionId: string): Observable<SessionStatusResponse> {
    return this.http.get<SessionStatusResponse>(`${this.base}/triage/${sessionId}/status`);
  }

  getSessions(): Observable<{ sessions: any[] }> {
    return this.http.get<{ sessions: any[] }>(`${this.base}/sessions`);
  }

  /**
   * Fetch the full message history for a session from the SQLite store.
   * Returns { session_id, messages: ConversationMessage[] }.
   * An empty messages array means the session exists but has no stored turns.
   */
  getConversationHistory(sessionId: string): Observable<{ session_id: string; messages: ConversationMessage[] }> {
    return this.http.get<{ session_id: string; messages: ConversationMessage[] }>(
      `${this.base}/api/conversations/${sessionId}`
    );
  }

  /**
   * Persist a single conversation turn (user or assistant).
   * Called client-side immediately after the user sends a message,
   * and again after the assistant reply is fully received.
   */
  saveConversationMessage(payload: SaveMessageRequest): Observable<{ id: number; status: string }> {
    return this.http.post<{ id: number; status: string }>(
      `${this.base}/api/conversations`,
      payload
    );
  }

  /**
   * Delete all messages for a session from the conversation store.
   * The backend also purges the in-memory session cache entry.
   */
  deleteConversation(sessionId: string): Observable<{ session_id: string; deleted: number; status: string }> {
    return this.http.delete<{ session_id: string; deleted: number; status: string }>(
      `${this.base}/api/conversations/${sessionId}`
    );
  }

  getPendingReviews(): Observable<{ sessions: SessionStatusResponse[] }> {
    return this.http.get<{ sessions: SessionStatusResponse[] }>(`${this.base}/clinician/pending`);
  }

  getAppointments(): Observable<{appointments: any[]}> {
    return this.http.get<{appointments: any[]}>(`${this.base}/clinician/appointments`);
  }

  checkSlotAvailability(datetimeIso: string): Observable<{ available: boolean }> {
    return this.http.get<{ available: boolean }>(
      `${this.base}/clinician/check-slot`,
      { params: { datetime_iso: datetimeIso } }
    );
  }

  healthCheck(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.base}/health`);
  }

  private createFetchStream(url: string, body: any): Observable<any> {
    return new Observable(observer => {
      const controller = new AbortController();
      const token = localStorage.getItem('hta_token');

      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(body),
        signal: controller.signal
      }).then(async response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        if (!response.body) throw new Error('No body');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                observer.next(JSON.parse(line.substring(6)));
              } catch (e) { }
            }
          }
        }
        observer.complete();
      }).catch(err => {
        // AbortError is expected on unsubscribe — suppress it silently
        if (err?.name !== 'AbortError') {
          observer.error(err);
        }
      });

      // Teardown: abort the in-flight fetch and cancel the reader loop
      return () => controller.abort();
    });
  }
}
