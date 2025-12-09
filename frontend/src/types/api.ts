/**
 * 모든 API 응답의 기본 구조
 * 프로젝트 전체에서 사용되는 표준 응답 형태
 */
export interface ApiResponse<T = void> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

/**
 * API 에러 구조
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * 공통 에러 코드
 */
export const ErrorCode = {
  // 인증 관련
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',

  // 리소스 관련
  NOT_FOUND: 'NOT_FOUND',
  DUPLICATE_USERNAME: 'DUPLICATE_USERNAME',
  DUPLICATE_RESOURCE: 'DUPLICATE_RESOURCE',

  // 검증 관련
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INVALID_INPUT: 'INVALID_INPUT',

  // 서버 관련
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
} as const;

export type ErrorCode = typeof ErrorCode[keyof typeof ErrorCode];

/**
 * 페이지네이션을 포함한 목록 응답
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  limit?: number;
  hasNext?: boolean;
}
