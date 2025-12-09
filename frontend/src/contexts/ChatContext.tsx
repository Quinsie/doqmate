import { createContext, useContext, type ReactNode } from 'react';
import { useChatHistory } from '../hooks/chat/useChatHistory';

interface ChatContextType {
  chatHistories: ReturnType<typeof useChatHistory>['chatHistories'];
  currentSessionId: ReturnType<typeof useChatHistory>['currentSessionId'];
  currentSession: ReturnType<typeof useChatHistory>['currentSession'];
  createNewChat: ReturnType<typeof useChatHistory>['createNewChat'];
  selectChat: ReturnType<typeof useChatHistory>['selectChat'];
  clearCurrentSession: ReturnType<typeof useChatHistory>['clearCurrentSession'];
  deleteChat: ReturnType<typeof useChatHistory>['deleteChat'];
  refreshChatHistories: ReturnType<typeof useChatHistory>['refreshChatHistories'];
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const chatHistory = useChatHistory();

  return (
    <ChatContext.Provider value={chatHistory}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}
