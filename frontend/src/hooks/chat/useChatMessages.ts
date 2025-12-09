import { useState, useEffect, useCallback } from 'react';
import type { Message, ChatImage } from '../../types/chat/chat';
import {
  getChatHistory,
  addMessageToSession,
  updateSessionMessages,
} from '../../utils/chatStorage';

interface UseChatMessagesProps {
  sessionId: string | null;
  onMessagesChange?: () => void;
}

/**
 * 특정 세션의 메시지를 관리하는 커스텀 훅
 */
export function useChatMessages({ sessionId, onMessagesChange }: UseChatMessagesProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // localStorage에서 메시지를 로드하는 함수
  const loadMessages = useCallback(() => {
    if (sessionId) {
      const session = getChatHistory(sessionId);
      if (session) {
        setMessages(session.messages);
      } else {
        console.log('useChatMessages - 세션을 찾을 수 없음');
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
  }, [sessionId]);

  // 세션이 변경되면 해당 세션의 메시지 로드
  useEffect(() => {
    loadMessages();
  }, [sessionId, loadMessages]);

  // localStorage 변경 감지 (다른 컴포넌트에서 직접 추가한 메시지 반영)
  useEffect(() => {
    const handleStorageChange = (e: CustomEvent<{ sessionId: string }>) => {
      if (e.detail.sessionId === sessionId) {
        loadMessages();
      }
    };

    // 커스텀 이벤트 리스너 등록
    window.addEventListener('chatStorageUpdated' as any, handleStorageChange as any);

    return () => {
      window.removeEventListener('chatStorageUpdated' as any, handleStorageChange as any);
    };
  }, [sessionId, loadMessages]);

  /**
   * 새 메시지 추가
   */
  const addMessage = useCallback((message: Message) => {
    if (!sessionId) return;

    const updatedSession = addMessageToSession(sessionId, message);
    if (updatedSession) {
      setMessages(updatedSession.messages);
      onMessagesChange?.();
    }
  }, [sessionId, onMessagesChange]);

  /**
   * 사용자 메시지 전송 (로컬에만 저장)
   */
  const sendUserMessage = useCallback((content: string) => {
    if (!sessionId || !content.trim()) {
      return;
    }

    const userMessage: Message = {
      role: 'user',
      content: content.trim(),
    };

    addMessage(userMessage);
  }, [sessionId, addMessage]);

  /**
   * 봇 응답 추가 (로컬에만 저장)
   */
  const addBotResponse = useCallback((content: string, chatbotName?: string, images?: ChatImage[]) => {
    if (!sessionId) return;

    const botMessage: Message = {
      role: 'assistant',
      content,
      chatbot_name: chatbotName,
      images,
    };

    addMessage(botMessage);
  }, [sessionId, addMessage]);

  /**
   * 메시지 수정
   */
  const editMessage = useCallback((index: number, newContent: string) => {
    if (!sessionId || index < 0 || index >= messages.length) return;

    const updatedMessages = [...messages];
    updatedMessages[index] = {
      ...updatedMessages[index],
      content: newContent,
    };

    const updatedSession = updateSessionMessages(sessionId, updatedMessages);
    if (updatedSession) {
      setMessages(updatedSession.messages);
      onMessagesChange?.();
    }
  }, [sessionId, messages, onMessagesChange]);

  /**
   * 특정 위치의 봇 응답을 업데이트
   */
  const updateBotResponseAt = useCallback((index: number, content: string, chatbotName?: string, images?: ChatImage[]) => {
    if (!sessionId || index < 0) return;

    // localStorage에서 최신 세션 데이터 가져오기
    const session = getChatHistory(sessionId);
    if (!session || index >= session.messages.length) return;

    const updatedMessages = [...session.messages];
    updatedMessages[index] = {
      ...updatedMessages[index],
      content,
      chatbot_name: chatbotName,
      images,
    };

    const updatedSession = updateSessionMessages(sessionId, updatedMessages);
    if (updatedSession) {
      setMessages(updatedSession.messages);
      onMessagesChange?.();
    }
  }, [sessionId, onMessagesChange]);

  /**
   * 메시지 삭제
   */
  const deleteMessage = useCallback((index: number) => {
    if (!sessionId || index < 0 || index >= messages.length) return;

    const updatedMessages = messages.filter((_, i) => i !== index);
    const updatedSession = updateSessionMessages(sessionId, updatedMessages);
    if (updatedSession) {
      setMessages(updatedSession.messages);
      onMessagesChange?.();
    }
  }, [sessionId, messages, onMessagesChange]);

  /**
   * 모든 메시지 삭제
   */
  const clearMessages = useCallback(() => {
    if (!sessionId) return;

    const updatedSession = updateSessionMessages(sessionId, []);
    if (updatedSession) {
      setMessages([]);
      onMessagesChange?.();
    }
  }, [sessionId, onMessagesChange]);

  return {
    messages,
    isLoading,
    setIsLoading,
    addMessage,
    sendUserMessage,
    addBotResponse,
    editMessage,
    updateBotResponseAt,
    deleteMessage,
    clearMessages,
  };
}
