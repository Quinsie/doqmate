import axios from 'axios';
import { getAccessToken, getAdminId } from '../utils/authStorage';
import { forceLogout } from '../utils/forceLogout';

const API_BASE_URL = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (Authorization 헤더 추가)
apiClient.interceptors.request.use(
  (config) => {
    const accessToken = getAccessToken();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    // 임시: 백엔드가 JWT를 완전히 지원할 때까지 X-Test-Admin-ID 헤더 추가
    const adminId = getAdminId();
    if (adminId) {
      config.headers['X-Test-Admin-ID'] = adminId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 로깅 및 인증 에러 처리)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API 에러:', error.response?.data || error.message);

    // 401 Unauthorized 에러 처리
    if (error.response?.status === 401) {
      forceLogout('session_expired');
    }

    // 403 Forbidden 에러 처리 (추방된 관리자)
    if (error.response?.status === 403) {
      forceLogout('expelled');
    }

    return Promise.reject(error);
  }
);
