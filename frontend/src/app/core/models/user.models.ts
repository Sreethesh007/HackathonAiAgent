export type UserRole = 'patient' | 'clinician' | 'admin';

export interface LoginRequest {
  username?: string;
  password?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface JwtPayload {
  sub: string;
  role: UserRole;
  exp: number;
  iat?: number;
}
