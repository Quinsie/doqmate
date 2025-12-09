const ACCESS_TOKEN_KEY = 'access_token';
const ADMIN_ID_KEY = 'admin_id';
const ADMIN_NAME_KEY = 'admin_name';

/**
 * 로컬 스토리지에서 액세스 토큰을 가져옵니다.
 */
export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    console.error('액세스 토큰 로드 실패:', error);
    return null;
  }
}

/**
 * 로컬 스토리지에 액세스 토큰을 저장합니다.
 */
export function setAccessToken(token: string): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } catch (error) {
    console.error('액세스 토큰 저장 실패:', error);
  }
}

/**
 * 로컬 스토리지에서 액세스 토큰을 삭제합니다.
 */
export function removeAccessToken(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    console.error('액세스 토큰 삭제 실패:', error);
  }
}

/**
 * 로컬 스토리지에서 관리자 ID를 가져옵니다.
 */
export function getAdminId(): string | null {
  try {
    return localStorage.getItem(ADMIN_ID_KEY);
  } catch (error) {
    console.error('관리자 ID 로드 실패:', error);
    return null;
  }
}

/**
 * 로컬 스토리지에 관리자 ID를 저장합니다.
 */
export function setAdminId(adminId: string): void {
  try {
    localStorage.setItem(ADMIN_ID_KEY, adminId);
  } catch (error) {
    console.error('관리자 ID 저장 실패:', error);
  }
}

/**
 * 로컬 스토리지에서 관리자 ID를 삭제합니다.
 */
export function removeAdminId(): void {
  try {
    localStorage.removeItem(ADMIN_ID_KEY);
  } catch (error) {
    console.error('관리자 ID 삭제 실패:', error);
  }
}

/**
 * 로컬 스토리지에서 관리자 이름을 가져옵니다.
 */
export function getAdminName(): string | null {
  try {
    return localStorage.getItem(ADMIN_NAME_KEY);
  } catch (error) {
    console.error('관리자 이름 로드 실패:', error);
    return null;
  }
}

/**
 * 로컬 스토리지에 관리자 이름을 저장합니다.
 */
export function setAdminName(name: string): void {
  try {
    localStorage.setItem(ADMIN_NAME_KEY, name);
  } catch (error) {
    console.error('관리자 이름 저장 실패:', error);
  }
}

/**
 * 로컬 스토리지에서 관리자 이름을 삭제합니다.
 */
export function removeAdminName(): void {
  try {
    localStorage.removeItem(ADMIN_NAME_KEY);
  } catch (error) {
    console.error('관리자 이름 삭제 실패:', error);
  }
}

/**
 * 모든 인증 관련 데이터를 로컬 스토리지에서 삭제합니다.
 */
export function clearAuthData(): void {
  try {
    removeAccessToken();
    removeAdminId();
    removeAdminName();
    window.dispatchEvent(new CustomEvent('auth-change'));
  } catch (error) {
    console.error('인증 데이터 삭제 실패:', error);
  }
}
