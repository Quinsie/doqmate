import { useState, useEffect, useCallback } from 'react';
import type { ChatHistory } from '../../types/chat/chat';
import {
  getAllChatHistories,
  getChatHistory,
  createChatSession,
  deleteChatSession,
} from '../../utils/chatStorage';

/**
 * 채팅 히스토리 목록 및 현재 세션을 관리하는 커스텀 훅
 */
export function useChatHistory(defaultChatbotId: string = 'default') {
  const [chatHistories, setChatHistories] = useState<ChatHistory[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentSession, setCurrentSession] = useState<ChatHistory | null>(null);

  // 초기 로드: 로컬 스토리지에서 채팅 기록 가져오기
  useEffect(() => {
    loadChatHistories();
  }, []);

  // 현재 세션 ID가 변경될 때마다 세션 데이터 업데이트
  useEffect(() => {
    if (currentSessionId) {
      const session = getChatHistory(currentSessionId);
      setCurrentSession(session);
    } else {
      setCurrentSession(null);
    }
  }, [currentSessionId]);

  /**
   * 로컬 스토리지에서 채팅 기록 로드
   */
  const loadChatHistories = useCallback(() => {
    const histories = getAllChatHistories();
    setChatHistories(histories);
  }, []);

  /**
   * 새 채팅 세션 생성
   */
  const createNewChat = useCallback((chatbotId?: string) => {
    const newSession = createChatSession(chatbotId || defaultChatbotId);
    loadChatHistories();
    setCurrentSessionId(newSession.session_id);
    return newSession;
  }, [defaultChatbotId, loadChatHistories]);

  /**
   * 채팅 세션 선택
   */
  const selectChat = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  /**
   * 현재 세션 클리어 (세션 생성 없이)
   */
  const clearCurrentSession = useCallback(() => {
    setCurrentSessionId(null);
  }, []);

  /**
   * 채팅 세션 삭제
   */
  const deleteChat = useCallback((sessionId: string) => {
    const success = deleteChatSession(sessionId);
    if (success) {
      loadChatHistories();
      // 현재 선택된 세션이 삭제된 경우 선택 해제
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
      }
    }
    return success;
  }, [currentSessionId, loadChatHistories]);

  /**
   * 채팅 기록 새로고침
   */
  const refreshChatHistories = useCallback(() => {
    loadChatHistories();
    // 현재 세션도 새로고침
    if (currentSessionId) {
      const session = getChatHistory(currentSessionId);
      setCurrentSession(session);
    }
  }, [currentSessionId, loadChatHistories]);

  return {
    chatHistories,
    currentSessionId,
    currentSession,
    createNewChat,
    selectChat,
    clearCurrentSession,
    deleteChat,
    refreshChatHistories,
  };
}
