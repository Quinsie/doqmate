import { useState } from 'react';
import { apiClient } from '../../api/client';
import type { ApiResponse } from '../../types/api';
import type {
  OverviewStatsResponseData,
  ChatbotStatsResponseData,
  DateStatsResponseData,
} from '../../types/admin/stats';

/**
 * 전체 통계 조회 API를 호출하는 커스텀 훅
 * GET /api/stats/overview
 */
export function useGetOverviewStats() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getOverviewStats = async (): Promise<OverviewStatsResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<OverviewStatsResponseData>>(
        '/stats/overview'
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '전체 통계를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '전체 통계를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('전체 통계 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getOverviewStats,
    isLoading,
    error,
  };
}

/**
 * 챗봇별 통계 조회 API를 호출하는 커스텀 훅
 * GET /api/stats/chatbot/{chatbot_id}
 */
export function useGetChatbotStats() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getChatbotStats = async (chatbotId: string): Promise<ChatbotStatsResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<ChatbotStatsResponseData>>(
        `/stats/chatbot/${chatbotId}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '챗봇 통계를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '챗봇 통계를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('챗봇 통계 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getChatbotStats,
    isLoading,
    error,
  };
}

/**
 * 날짜별 통계 조회 API를 호출하는 커스텀 훅
 * GET /api/stats/date/{date}
 */
export function useGetDateStats() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getDateStats = async (date: string): Promise<DateStatsResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<DateStatsResponseData>>(
        `/stats/date/${date}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '날짜별 통계를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '날짜별 통계를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('날짜별 통계 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getDateStats,
    isLoading,
    error,
  };
}
