import { useState } from 'react';
import { apiClient } from '../../api/client';
import type { ApiResponse } from '../../types/api';
import type {
  Chatbot,
  ChatbotListResponseData,
  UpdateChatbotRequest,
} from '../../types/admin/chatbot';

/**
 * 챗봇 목록 조회 API를 호출하는 커스텀 훅
 */
export function useGetChatbots() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getChatbots = async (): Promise<ChatbotListResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<ChatbotListResponseData>>(
        '/set/chatbots'
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '챗봇 목록을 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '챗봇 목록을 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('챗봇 목록 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getChatbots,
    isLoading,
    error,
  };
}

/**
 * 챗봇 생성 API를 호출하는 커스텀 훅
 */
export function useCreateChatbot() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createChatbot = async (
    createData: UpdateChatbotRequest
  ): Promise<Chatbot | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<ApiResponse<Chatbot>>(
        '/set/chatbots',
        createData
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '챗봇 생성에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '챗봇 생성에 실패했습니다.';
      setError(errorMessage);
      console.error('챗봇 생성 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    createChatbot,
    isLoading,
    error,
  };
}

/**
 * 챗봇 상세 조회 API를 호출하는 커스텀 훅
 */
export function useGetChatbotDetail() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getChatbotDetail = async (chatbotId: string): Promise<Chatbot | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ApiResponse<Chatbot>>(
        `/set/chatbots/${chatbotId}`
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '챗봇 정보를 불러오지 못했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '챗봇 정보를 불러오지 못했습니다.';
      setError(errorMessage);
      console.error('챗봇 상세 조회 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getChatbotDetail,
    isLoading,
    error,
  };
}

/**
 * 챗봇 수정 API를 호출하는 커스텀 훅
 */
export function useUpdateChatbot() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateChatbot = async (
    chatbotId: string,
    updateData: UpdateChatbotRequest
  ): Promise<Chatbot | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.patch<ApiResponse<Chatbot>>(
        `/set/chatbots/${chatbotId}`,
        updateData
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '챗봇 수정에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '챗봇 수정에 실패했습니다.';
      setError(errorMessage);
      console.error('챗봇 수정 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    updateChatbot,
    isLoading,
    error,
  };
}

/**
 * 챗봇 삭제 API를 호출하는 커스텀 훅
 */
export function useDeleteChatbot() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteChatbot = async (chatbotId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `/set/chatbots/${chatbotId}`
      );

      if (response.data.success) {
        return true;
      } else {
        const errorMessage = response.data.error?.message || '챗봇 삭제에 실패했습니다.';
        setError(errorMessage);
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '챗봇 삭제에 실패했습니다.';
      setError(errorMessage);
      console.error('챗봇 삭제 실패:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    deleteChatbot,
    isLoading,
    error,
  };
}
