/**
 * 관리자 가입 관련 타입 정의
 * API 엔드포인트: /api/signup
 */

// ============================================
// 기본 엔티티
// ============================================

/**
 * 가입 신청 정보
 */
export interface Signup {
  signup_id: string;
  username: string;
  name: string;
  created_at: string;
}

// ============================================
// 가입 신청 생성 (POST /api/signup)
// ============================================

export interface SignupRequest {
  username: string;
  password: string;
  name: string;
}

export interface SignupResponseData {
  signup_id: string;
  username: string;
  name: string;
  created_at: string;
}

// ============================================
// ID 중복 확인 (GET /api/signup/check-username)
// ============================================

export interface CheckUsernameResponseData {
  username: string;
  is_available: boolean;
  message: string;
}

// ============================================
// 가입 신청 목록 조회 (GET /api/signup)
// ============================================

export interface SignupListResponseData {
  signups: Signup[];
}

// ============================================
// 가입 신청 상세 조회 (GET /api/signup/{signup_id})
// ============================================

export interface SignupDetailResponseData {
  signup_id: string;
  username: string;
  name: string;
  created_at: string;
  details?: string;
}

// ============================================
// 가입 신청 승인/반려
// (POST /api/signup/{signup_id}/approve)
// (POST /api/signup/{signup_id}/reject)
// ============================================

// 응답: ApiResponse<void> (success만 반환)
