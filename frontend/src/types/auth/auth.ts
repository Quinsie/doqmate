/**
 * 인증 및 관리자 계정 관련 타입 정의
 * API 엔드포인트: /api/auth
 */

// ============================================
// 기본 엔티티
// ============================================

/**
 * 관리자 정보
 */
export interface Admin {
  admin_id: string;
  username: string;
  name: string;
  created_at?: string;
  last_login_at?: string;
}

// ============================================
// 로그인 (POST /api/auth/login)
// ============================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponseData {
  token: string;
  admin: {
    admin_id: string;
    username: string;
    name: string;
    created_at: string;
  };
}

// ============================================
// 내 정보 조회 (GET /api/auth/me)
// ============================================

export interface MeResponseData {
  admin_id: string;
  username: string;
  name: string;
  created_at?: string;
  last_login_at?: string;
}

// ============================================
// 비밀번호 변경 (PATCH /api/auth/me/password)
// ============================================

export interface ChangePasswordRequest {
  admin_id: string;
  current_password: string;
  new_password: string;
}

// 응답: ApiResponse<void> (success만 반환)

// ============================================
// 아이디 찾기 (POST /api/auth/find-username)
// ============================================

export interface FindUsernameRequest {
  name: string;
}

export interface FindUsernameResponseData {
  candidates: {
    username_masked: string;
    status: string;
  }[];
}

// ============================================
// 비밀번호 재설정 (POST /api/auth/reset-password)
// ============================================

export interface ResetPasswordRequest {
  username: string;
  name: string;
}

export interface ResetPasswordResponseData {
  temp_password: string;
}
