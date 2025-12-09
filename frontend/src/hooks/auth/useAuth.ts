import { useState } from 'react';
import { apiClient } from '../../api/client';
import type { ApiResponse } from '../../types/api';
import type {
  LoginRequest,
  LoginResponseData,
  MeResponseData,
  ChangePasswordRequest,
  FindUsernameRequest,
  FindUsernameResponseData,
  ResetPasswordRequest,
  ResetPasswordResponseData,
} from '../../types/auth/auth';
import { getAdminId } from '../../utils/authStorage';

/**
 * 로그인 API를 호출하는 커스텀 훅
 */
export function useLogin() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (
    username: string,
    password: string
  ): Promise<LoginResponseData | null> => {
    setIsLoading(true);
    setError(null);

    const requestBody: LoginRequest = {
      username,
      password,
    };

    try {
      const response = await apiClient.post<ApiResponse<LoginResponseData>>(
        '/auth/login',
        requestBody
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '로그인에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '로그인에 실패했습니다.';
      setError(errorMessage);
      console.error('로그인 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    login,
    isLoading,
    error,
  };
}

/**
 * 내 정보 조회 API를 호출하는 커스텀 훅
 */
export function useGetMe() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<MeResponseData | null>(null);

  const getMe = async (): Promise<MeResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<MeResponseData>>(
        '/auth/me'
      );

      if (response.data.success && response.data.data) {
        setUser(response.data.data);
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '사용자 정보를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '사용자 정보를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('사용자 정보 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getMe,
    isLoading,
    error,
    user,
  };
}

/**
 * 비밀번호 변경 API를 호출하는 커스텀 훅
 */
export function useChangePassword() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const changePassword = async (
    currentPassword: string,
    newPassword: string
  ): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    const adminId = getAdminId();
    if (!adminId) {
      setError('관리자 ID를 찾을 수 없습니다.');
      setIsLoading(false);
      return false;
    }

    const requestBody: ChangePasswordRequest = {
      admin_id: adminId,
      current_password: currentPassword,
      new_password: newPassword,
    };

    try {
      const response = await apiClient.patch<ApiResponse<void>>(
        '/auth/me/password',
        requestBody
      );

      if (response.data.success) {
        return true;
      } else {
        const errorMessage = response.data.error?.message || '비밀번호 변경에 실패했습니다.';
        setError(errorMessage);
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '비밀번호 변경에 실패했습니다.';
      setError(errorMessage);
      console.error('비밀번호 변경 실패:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    changePassword,
    isLoading,
    error,
  };
}

/**
 * 아이디 찾기 API를 호출하는 커스텀 훅
 */
export function useFindUsername() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string[] | null>(null);

  const findUsername = async (name: string): Promise<string[] | null> => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    const requestBody: FindUsernameRequest = { name };

    try {
      const response = await apiClient.post<ApiResponse<FindUsernameResponseData>>(
        '/auth/find-username',
        requestBody
      );

      if (response.data.success && response.data.data) {
        const usernames = response.data.data.candidates.map(c => c.username_masked);
        setResult(usernames);
        return usernames;
      } else {
        const errorMessage = response.data.error?.message || '아이디 찾기에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '아이디 찾기에 실패했습니다.';
      setError(errorMessage);
      console.error('아이디 찾기 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return {
    findUsername,
    isLoading,
    error,
    result,
    reset,
  };
}

/**
 * 비밀번호 재설정 API를 호출하는 커스텀 훅
 */
export function useResetPassword() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  const resetPassword = async (username: string, name: string): Promise<string | null> => {
    setIsLoading(true);
    setError(null);
    setTempPassword(null);

    const requestBody: ResetPasswordRequest = { username, name };

    try {
      const response = await apiClient.post<ApiResponse<ResetPasswordResponseData>>(
        '/auth/reset-password',
        requestBody
      );

      if (response.data.success && response.data.data) {
        const password = response.data.data.temp_password;
        setTempPassword(password);
        return password;
      } else {
        const errorMessage = response.data.error?.message || '비밀번호 재설정에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '비밀번호 재설정에 실패했습니다.';
      setError(errorMessage);
      console.error('비밀번호 재설정 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setTempPassword(null);
    setError(null);
  };

  return {
    resetPassword,
    isLoading,
    error,
    tempPassword,
    reset,
  };
}
