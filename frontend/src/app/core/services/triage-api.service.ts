import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  TriageRequest, TriageResponse,
  ContinueRequest, ContinueResponse,
  SessionStatusResponse, HealthResponse
} from '../models/triage.models';

@Injectable({ providedIn: 'root' })
export class TriageApiService {
  private base = '/api';

  constructor(private http: HttpClient) {}

  startTriage(req: TriageRequest): Observable<TriageResponse> {
    return this.http.post<TriageResponse>(`${this.base}/triage`, req);
  }

  continueTriage(sessionId: string, req: ContinueRequest): Observable<ContinueResponse> {
    return this.http.post<ContinueResponse>(`${this.base}/triage/${sessionId}/continue`, req);
  }

  getSessionStatus(sessionId: string): Observable<SessionStatusResponse> {
    return this.http.get<SessionStatusResponse>(`${this.base}/triage/${sessionId}/status`);
  }

  healthCheck(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.base}/health`);
  }
}
