/**
 * 라우트 경로 상수 정의
 * - 라우트 경로를 한 곳에서 관리하여 유지보수성 향상
 * - navigate() 호출 시 문자열 오타 방지
 */

// Public Routes
export const ROUTES = {
  // 메인
  HOME: '/',

  // 채팅
  CHAT: (sessionId?: string) => sessionId ? `/chat/${sessionId}` : '/chat',

  // 인증 관련
  AUTH: {
    LOGIN: '/auth/login',
    SIGNUP: '/auth/signup',
    FIND_USERNAME: '/auth/find-username',
    RESET_PASSWORD: '/auth/reset-password',
  },

  // 관리자
  ADMIN: {
    MAIN: '/admin',
    CHATBOT_LIST: '/admin/chatbotlist',
    CHATBOT_CREATE: '/admin/chatbot/create',
    CHATBOT_MANUAL: (chatbotId: string) => `/admin/chatbot/${chatbotId}/manual`,
    SIGNUP_MANAGEMENT: '/admin/signup-management',
    ADMIN_LIST: '/admin/admins',
    SETTINGS: '/admin/profile-settings',
    STATS: '/admin/stats',
  },
} as const;
