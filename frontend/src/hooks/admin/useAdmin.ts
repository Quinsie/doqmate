import { useState } from 'react';
import { apiClient } from '../../api/client';
import type { ApiResponse } from '../../types/api';
import type { AdminListResponseData, AdminDetailResponseData } from '../../types/admin/admin';

/**
 * 관리자 목록 조회 API를 호출하는 커스텀 훅
 */
export function useGetAdmins() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAdmins = async (): Promise<AdminListResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<AdminListResponseData>>(
        '/admin'
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '관리자 목록을 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '관리자 목록을 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('관리자 목록 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getAdmins,
    isLoading,
    error,
  };
}

/**
 * 관리자 상세 조회 API를 호출하는 커스텀 훅
 */
export function useGetAdminDetail() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAdminDetail = async (adminId: string): Promise<AdminDetailResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<AdminDetailResponseData>>(
        `/admin/${adminId}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '관리자 정보를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '관리자 정보를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('관리자 상세 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getAdminDetail,
    isLoading,
    error,
  };
}

/**
 * 관리자 삭제(추방) API를 호출하는 커스텀 훅
 */
export function useDeleteAdmin() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteAdmin = async (adminId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `/admin/${adminId}`
      );

      if (response.data.success) {
        return true;
      } else {
        const errorMessage = response.data.error?.message || '관리자 추방에 실패했습니다.';
        setError(errorMessage);
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '관리자 추방에 실패했습니다.';
      setError(errorMessage);
      console.error('관리자 삭제 실패:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    deleteAdmin,
    isLoading,
    error,
  };
}
