import { useState } from 'react';
import { apiClient } from '../../api/client';
import type { ChatResponse, ChatRequest } from '../../types/chat/chat';
import type { ApiResponse } from '../../types/api';

/**
 * 사용자 메시지를 전송하고 봇 응답을 받아오는 커스텀 훅
 */
export function usePostUserMessage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const postUserMessage = async (
    question: string,
    chatbotId: string,
    sessionId: string
  ): Promise<ChatResponse | null> => {
    setIsLoading(true);
    setError(null);

    const requestBody: ChatRequest = {
      chatbot_id: chatbotId,
      session_id: sessionId,
      messages: [
        {
          role: 'user',
          content: question,
        },
      ],
    };

    try {
      const response = await apiClient.post<ApiResponse<ChatResponse>>(
        '/chats',
        requestBody
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      } else {
        const errorMessage = response.data.error?.message || '메시지 전송에 실패했습니다.';
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.';
      setError(errorMessage);
      console.error('메시지 전송 실패:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    postUserMessage,
    isLoading,
    error,
  };
}
