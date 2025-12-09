import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChatContext } from '../../contexts/ChatContext';
import { useChatMessages } from '../../hooks/chat/useChatMessages';
import { usePostUserMessage } from '../../hooks/chat/usePostUserMessage';
import ChatInput from '../../components/chat/ChatInput';
import UserMessage from '../../components/chat/UserMessage';
import BotMessage from '../../components/chat/BotMessage';
import WelcomeTitle from '../../components/common/WelcomeTitle';
import { ROUTES } from '../../constants/routes';
import { addMessageToSession, getSelectedChatbot } from '../../utils/chatStorage';
import type { Message } from '../../types/chat/chat';

function ChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { currentSessionId, createNewChat, selectChat, clearCurrentSession, refreshChatHistories } = useChatContext();
  const { postUserMessage } = usePostUserMessage();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [editingBotIndex, setEditingBotIndex] = useState<number | null>(null);

  // URL의 sessionId와 현재 선택된 세션 동기화
  useEffect(() => {
    if (sessionId) {
      // URL에 sessionId가 있으면 해당 세션 선택
      // (이미 선택되어 있으면 selectChat이 내부적으로 무시할 수도 있음)
      if (sessionId !== currentSessionId) {
        selectChat(sessionId);
      }
    } else {
      // URL에 sessionId가 없으면 (/ 경로) 세션 클리어
      if (currentSessionId) {
        clearCurrentSession();
      }
    }
  }, [sessionId]); // currentSessionId를 의존성에서 제거하여 무한 루프 방지

  const {
    messages,
    sendUserMessage,
    addBotResponse,
    editMessage,
    updateBotResponseAt,
    isLoading,
    setIsLoading,
  } = useChatMessages({ sessionId: currentSessionId, onMessagesChange: refreshChatHistories });

  // 메시지가 추가될 때마다 스크롤을 맨 아래로 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (message: string, chatbotId: string) => {
    // 세션이 없으면 새 채팅 생성
    if (!currentSessionId) {
      const newSession = createNewChat(chatbotId);
      const newSessionId = newSession.session_id;

      // 사용자 메시지를 새 세션에 직접 저장
      const userMessage: Message = {
        role: 'user',
        content: message.trim(),
      };
      addMessageToSession(newSessionId, userMessage);

      // URL을 새 세션 ID로 업데이트 (replace: true로 히스토리 중복 방지)
      navigate(ROUTES.CHAT(newSessionId), { replace: true });

      setIsLoading(true);
      const response = await postUserMessage(message, chatbotId, newSessionId);
      if (response) {
        addMessageToSession(newSessionId, {
          role: 'assistant',
          content: response.answer,
          chatbot_name: response.chatbot_name,
          images: response.images,
        });
      }
      setIsLoading(false);
      return;
    }

    // 기존 세션에 메시지 전송
    sendUserMessage(message);

    setIsLoading(true);
    const response = await postUserMessage(message, chatbotId, currentSessionId);
    if (response) {
      addBotResponse(response.answer, response.chatbot_name, response.images);
    }
    setIsLoading(false);
  };

  const handleEditMessage = async (index: number, newContent: string) => {
    if (!currentSessionId) return;

    // 1. 사용자 메시지 수정
    editMessage(index, newContent);

    // 2. 다음 메시지가 봇 응답인지 확인
    const botResponseIndex = index + 1;
    if (botResponseIndex < messages.length && messages[botResponseIndex].role === 'assistant') {
      // 3. 현재 선택된 챗봇 ID 가져오기
      const selectedChatbot = getSelectedChatbot();
      if (!selectedChatbot) return;

      // 4. 해당 봇 응답을 로딩 상태로 전환
      setEditingBotIndex(botResponseIndex);

      // 5. API 재호출
      const response = await postUserMessage(newContent, selectedChatbot.chatbot_id, currentSessionId);

      // 6. 봇 응답 업데이트
      if (response) {
        updateBotResponseAt(botResponseIndex, response.answer, response.chatbot_name, response.images);
      }

      setEditingBotIndex(null);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <main className="h-[calc(100vh-70px)] flex flex-col relative">
      {hasMessages ? (
        // 메시지가 있을 때
        <>
          <div className="flex-1 overflow-y-auto p-6 pb-[200px]">
            <div className="max-w-4xl mx-auto">
              {messages.map((msg, index) => (
                msg.role === 'user' ? (
                  <UserMessage
                    key={index}
                    content={msg.content}
                    onEdit={(newContent) => handleEditMessage(index, newContent)}
                  />
                ) : (
                  <BotMessage
                    key={index}
                    content={msg.content}
                    chatbotName={msg.chatbot_name}
                    images={msg.images}
                    isLoading={editingBotIndex === index}
                  />
                )
              ))}
              {isLoading && editingBotIndex === null && (
                <BotMessage
                  isLoading={true}
                  chatbotName={getSelectedChatbot()?.name}
                />
              )}
              {/* 스크롤 타겟 */}
              <div ref={messagesEndRef} />
            </div>
          </div>
          <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
            <div className="h-16 bg-gradient-to-t from-white via-white/80 to-transparent"></div>
            <div className="pointer-events-auto">
              <ChatInput onSendMessage={handleSendMessage} isSendDisabled={isLoading} />
            </div>
          </div>
        </>
      ) : (
        // 메시지가 없을 때
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-4xl">
            <WelcomeTitle>
              안녕하세요 👋 도움 받을 챗봇을 선택 후, <br/> 
              궁금한 점을 물어보시면 바로 알려드릴게요!
            </WelcomeTitle>
            <ChatInput onSendMessage={handleSendMessage} />
          </div>
        </div>
      )}
    </main>
  );
}

export default ChatPage;
