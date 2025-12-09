/**
 * 챗봇 관리 관련 타입 정의
 * API 엔드포인트: /api/set/chatbots
 */

// ============================================
// 기본 엔티티
// ============================================

export interface Chatbot {
  chatbot_id: string;
  name: string;
  description?: string;
  is_public: boolean;
  tag?: string;
  created_at: string;
}

// ============================================
// 챗봇 목록 조회 (GET /api/set/chatbots)
// ============================================

export interface ChatbotListResponseData {
  chatbots: Chatbot[];
}

// ============================================
// 챗봇 생성 (POST /api/set/chatbots)
// ============================================

export interface CreateChatbotRequest {
  name: string; // 필수
  description?: string; // 선택
  is_public?: boolean; // 기본값 true
  tag?: string;
}

// 응답: ApiResponse<Chatbot>

// ============================================
// 챗봇 상세 조회 (GET /api/set/chatbots/{chatbot_id})
// ============================================

// Chatbot 타입 그대로 사용
export type ChatbotDetailResponseData = Chatbot;

// ============================================
// 챗봇 설정 수정 (PATCH /api/set/chatbots/{chatbot_id})
// ============================================

export interface UpdateChatbotRequest {
  name?: string;
  description?: string;
  is_public?: boolean;
  tag?: string;
}

// 응답: ApiResponse<Chatbot>

// ============================================
// 챗봇 삭제 (DELETE /api/set/chatbots/{chatbot_id})
// ============================================

// 응답: ApiResponse<void>

