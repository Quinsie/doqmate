import { createContext, useContext, type ReactNode } from 'react';

interface ChatbotListContextType {
  // Actions
  onTogglePublic: (chatbotId: string, isPublic: boolean) => void;

  // State
  isUpdating: boolean;
}

const ChatbotListContext = createContext<ChatbotListContextType | undefined>(undefined);

interface ChatbotListProviderProps {
  children: ReactNode;
  onTogglePublic: (chatbotId: string, isPublic: boolean) => void;
  isUpdating: boolean;
}

export function ChatbotListProvider({
  children,
  onTogglePublic,
  isUpdating
}: ChatbotListProviderProps) {
  const value: ChatbotListContextType = {
    onTogglePublic,
    isUpdating
  };

  return (
    <ChatbotListContext.Provider value={value}>
      {children}
    </ChatbotListContext.Provider>
  );
}

export function useChatbotListContext() {
  const context = useContext(ChatbotListContext);
  if (context === undefined) {
    throw new Error('useChatbotListContext must be used within a ChatbotListProvider');
  }
  return context;
}
