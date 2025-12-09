import { getAccessToken } from './authStorage';

/**
 * 사용자가 인증되었는지 확인합니다.
 * 로컬 스토리지에 access_token이 존재하는지 체크합니다.
 */
export function isAuthenticated(): boolean {
  const accessToken = getAccessToken();
  return !!accessToken;
}
