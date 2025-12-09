import { clearAuthData } from './authStorage';
import { ROUTES } from '../constants/routes';

export type LogoutReason = 'logout' | 'expelled' | 'session_expired' | 'unauthorized';

const LOGOUT_REASON_KEY = 'logout_reason';

const LOGOUT_MESSAGES: Record<LogoutReason, string> = {
  logout: '로그아웃 되었습니다.',
  expelled: '계정이 관리자에 의해 삭제되었습니다. 다시 로그인해주세요.',
  session_expired: '세션이 만료되었습니다. 다시 로그인해주세요.',
  unauthorized: '인증이 필요합니다. 로그인해주세요.',
};

// 강제 로그아웃 수행
export function forceLogout(reason: LogoutReason = 'unauthorized'): void {
  // 직접 로그아웃인 경우에만 alert 표시
  if (reason === 'logout') {
    alert(LOGOUT_MESSAGES.logout);
  } else {
    sessionStorage.setItem(LOGOUT_REASON_KEY, reason);
  }

  clearAuthData();
  window.location.href = ROUTES.AUTH.LOGIN;
}

// 로그아웃 사유 가져오기 (한 번 읽으면 삭제됨)
export function getLogoutReason(): LogoutReason | null {
  const reason = sessionStorage.getItem(LOGOUT_REASON_KEY) as LogoutReason | null;
  if (reason) {
    sessionStorage.removeItem(LOGOUT_REASON_KEY);
  }
  return reason;
}

// 사유별 메시지 반환
export function getLogoutMessage(reason: LogoutReason): string {
  return LOGOUT_MESSAGES[reason];
}
