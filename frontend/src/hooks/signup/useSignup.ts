import { useState } from 'react';
import { apiClient } from '../../api/client';
import type { ApiResponse } from '../../types/api';
import type {
  SignupRequest,
  SignupResponseData,
  CheckUsernameResponseData,
  SignupListResponseData,
  SignupDetailResponseData,
} from '../../types/auth/signup';

/**
 * 가입 신청 생성 API를 호출하는 커스텀 훅
 */
export function useCreateSignup() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createSignup = async (data: SignupRequest): Promise<SignupResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<ApiResponse<SignupResponseData>>(
        '/signup',
        data
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '가입 신청에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '가입 신청에 실패했습니다.';
      setError(errorMessage);
      console.error('가입 신청 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    createSignup,
    isLoading,
    error,
  };
}

/**
 * 아이디 중복 확인 API를 호출하는 커스텀 훅
 */
export function useCheckUsername() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkUsername = async (username: string): Promise<CheckUsernameResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<CheckUsernameResponseData>>(
        `/signup/check-username?username=${encodeURIComponent(username)}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '아이디 중복 확인에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '아이디 중복 확인에 실패했습니다.';
      setError(errorMessage);
      console.error('아이디 중복 확인 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    checkUsername,
    isLoading,
    error,
  };
}

/**
 * 가입 신청 목록 조회 API를 호출하는 커스텀 훅
 */
export function useGetSignups() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSignups = async (): Promise<SignupListResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<SignupListResponseData>>(
        '/signup'
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '가입 신청 목록을 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '가입 신청 목록을 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('가입 신청 목록 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getSignups,
    isLoading,
    error,
  };
}

/**
 * 가입 신청 상세 조회 API를 호출하는 커스텀 훅
 */
export function useGetSignupDetail() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSignupDetail = async (signupId: string): Promise<SignupDetailResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<SignupDetailResponseData>>(
        `/signup/${signupId}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '가입 신청 정보를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '가입 신청 정보를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('가입 신청 상세 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getSignupDetail,
    isLoading,
    error,
  };
}

/**
 * 가입 신청 승인 API를 호출하는 커스텀 훅
 */
export function useApproveSignup() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approveSignup = async (signupId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `/signup/${signupId}/approve`
      );

      if (response.data.success) {
        return true;
      } else {
        const errorMessage = response.data.error?.message || '가입 승인에 실패했습니다.';
        setError(errorMessage);
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '가입 승인에 실패했습니다.';
      setError(errorMessage);
      console.error('가입 승인 실패:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    approveSignup,
    isLoading,
    error,
  };
}

/**
 * 가입 신청 반려 API를 호출하는 커스텀 훅
 */
export function useRejectSignup() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rejectSignup = async (signupId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<ApiResponse<void>>(
        `/signup/${signupId}/reject`
      );

      if (response.data.success) {
        return true;
      } else {
        const errorMessage = response.data.error?.message || '가입 반려에 실패했습니다.';
        setError(errorMessage);
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '가입 반려에 실패했습니다.';
      setError(errorMessage);
      console.error('가입 반려 실패:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    rejectSignup,
    isLoading,
    error,
  };
}
