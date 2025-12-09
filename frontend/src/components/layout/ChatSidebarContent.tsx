import { SquarePen, LogIn, LogOut } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useChatContext } from '../../contexts/ChatContext';
import { updateSessionTitle, togglePinSession } from '../../utils/chatStorage';
import ChatListItem from './ChatListItem';
import { ROUTES } from '../../constants/routes';
import { isAuthenticated } from '../../utils/permissions';
import { clearAuthData } from '../../utils/authStorage';

interface NewChatButtonProps {
  isCollapsed: boolean;
  onClick: () => void;
}

function NewChatButton({ isCollapsed, onClick }: NewChatButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center py-3 text-left transition-all duration-200 rounded-xl ${
        isCollapsed ? 'justify-center' : 'gap-3 px-4'
      } text-gray-700 hover:bg-black/10`}
      title={isCollapsed ? '새 채팅' : undefined}
    >
      <SquarePen size={20} />
      {!isCollapsed && <span className="font-medium whitespace-nowrap">새 채팅</span>}
    </button>
  );
}

interface ChatSidebarContentProps {
  isCollapsed: boolean;
}

function ChatSidebarContent({
  isCollapsed,
}: ChatSidebarContentProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    chatHistories,
    currentSessionId,
    deleteChat,
    refreshChatHistories,
  } = useChatContext();

  const handleNewChat = () => {
    // 홈으로 이동 (새 채팅 시작 화면)
    navigate(ROUTES.HOME);
  };

  const handleChatSelect = (sessionId: string) => {
    // 해당 세션 URL로 이동
    navigate(ROUTES.CHAT(sessionId));
  };

  const handleRename = (sessionId: string, newTitle: string) => {
    updateSessionTitle(sessionId, newTitle);
    refreshChatHistories();
  };

  const handleDelete = (sessionId: string) => {
    if (window.confirm('이 채팅을 삭제하시겠습니까?')) {
      deleteChat(sessionId);
    }
  };

  const handlePin = (sessionId: string) => {
    togglePinSession(sessionId);
    refreshChatHistories();
  };

  const handleLogout = () => {
    clearAuthData();
    navigate(ROUTES.HOME);
  };

  const sortedChats = [...chatHistories].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return 0;
  });

  return (
    <>
      <NewChatButton isCollapsed={isCollapsed} onClick={handleNewChat} />

      <nav className="mt-5 flex-1 overflow-y-auto">
        <div className={`transition-opacity duration-300 ${isCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
          {!isCollapsed && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 px-3 mb-3">
                <div className="h-px flex-1 bg-gray-300/50" />
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">최근 채팅</span>
                <div className="h-px flex-1 bg-gray-300/50" />
              </div>
              {sortedChats.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-400">채팅 기록이 없습니다</p>
                  <p className="text-xs text-gray-300 mt-1">새 채팅을 시작해보세요</p>
                </div>
              ) : (
                sortedChats.map((chat) => {
                  const lastMessage = chat.messages.length > 0
                    ? chat.messages[chat.messages.length - 1].content
                    : '';

                  return (
                    <ChatListItem
                      key={chat.session_id}
                      title={chat.title}
                      lastMessage={lastMessage}
                      isSelected={currentSessionId === chat.session_id}
                      isPinned={chat.isPinned}
                      onClick={() => handleChatSelect(chat.session_id)}
                      onPin={() => handlePin(chat.session_id)}
                      onRename={(newTitle) => handleRename(chat.session_id, newTitle)}
                      onDelete={() => handleDelete(chat.session_id)}
                    />
                  );
                })
              )}
            </div>
          )}
        </div>
      </nav>

      <div className="border-t border-gray-300/50 pt-3">
        {isAuthenticated() ? (
          <button
            onClick={handleLogout}
            className={`w-full flex items-center py-2.5 transition-all duration-200 rounded-lg text-gray-600 hover:bg-red-50 hover:text-red-600 ${
              isCollapsed ? 'justify-center' : 'gap-3 px-4'
            }`}
            title={isCollapsed ? '관리자 로그아웃' : undefined}
          >
            <LogOut size={18} />
            {!isCollapsed && <span className="text-sm font-medium">관리자 로그아웃</span>}
          </button>
        ) : (
          <button
            onClick={() => navigate(ROUTES.AUTH.LOGIN, { state: { from: location } })}
            className={`w-full flex items-center py-2.5 transition-all duration-200 rounded-lg text-gray-600 hover:bg-black/10 hover:text-blue-600 ${
              isCollapsed ? 'justify-center' : 'gap-3 px-4'
            }`}
            title={isCollapsed ? '관리자 로그인' : undefined}
          >
            <LogIn size={18} />
            {!isCollapsed && <span className="text-sm font-medium">관리자 로그인</span>}
          </button>
        )}
      </div>
    </>
  );
}

export default ChatSidebarContent;
