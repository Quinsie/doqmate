/**
 * 챗봇별 문서 관리 관련 타입 정의
 * API 엔드포인트: /api/set/manuals
 */

// ============================================
// 기본 엔티티
// ============================================

export type ManualStatus = 'pending' | 'indexing' | 'ready' | 'failed';

export interface Manual {
  manual_id: string;
  chatbot_id: string;
  display_name: string;
  original_filename: string;
  status: ManualStatus;
  created_at: string;
}

// ============================================
// 문서 업로드 (POST /api/set/manuals?chatbot_id={chatbot_id})
// ============================================

// Content-Type: multipart/form-data
// FormData에 다음 필드들을 append
export interface UploadManualFormData {
  file: File; // PDF 파일
  display_name: string; // UI에 표시할 문서 이름
}

// 응답: ApiResponse<Manual>

// ============================================
// 문서 목록 조회 (GET /api/set/manuals?chatbot_id={chatbot_id})
// ============================================

export interface ManualListResponseData {
  manuals: Manual[];
}

// ============================================
// 문서 삭제 (DELETE /api/set/manuals/{manual_id})
// ============================================

// 응답: ApiResponse<void>

// ============================================
// 프론트엔드 전용 타입 (업로드 대기 중인 파일)
// ============================================

export interface UploadingFile {
  file: File;
  display_name: string;
}