/**
 * 가입자(관리자) 관리 관련 타입 정의
 * API 엔드포인트: /api/admin
 */

import type { Admin } from '../auth/auth';

// ============================================
// 관리자 계정 목록 조회 (GET /api/admin)
// ============================================

export interface AdminListResponseData {
  admins: Admin[];
}

// ============================================
// 관리자 계정 상세 조회 (GET /api/admin/{admin_id})
// ============================================

// Admin 타입 그대로 사용
export type AdminDetailResponseData = Admin;

// ============================================
// 관리자 계정 삭제 (DELETE /api/admin/{admin_id})
// ============================================

// 응답: ApiResponse<void> (success만 반환)
