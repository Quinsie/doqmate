import { useState, useRef, useEffect } from 'react';
import { EllipsisVertical, Pin, PinOff, Pencil, Trash2 } from 'lucide-react';

interface ChatListItemProps {
  title: string;
  lastMessage: string;
  isSelected: boolean;
  isPinned?: boolean;
  onClick: () => void;
  onPin?: () => void;
  onRename?: (newTitle: string) => void;
  onDelete?: () => void;
}

function ChatListItem({
  title,
  lastMessage,
  isSelected,
  isPinned = false,
  onClick,
  onPin,
  onRename,
  onDelete,
}: ChatListItemProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [editedTitle, setEditedTitle] = useState(title);
  const [isHovered, setIsHovered] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 메뉴 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    }

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  // 이름 변경 모드 진입 시 input에 포커스
  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isRenaming]);

  const handleMenuClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handlePinClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onPin?.();
    setShowMenu(false);
  };

  const handleRenameClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRenaming(true);
    setShowMenu(false);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.();
    setShowMenu(false);
  };

  const handleRenameSubmit = () => {
    if (editedTitle.trim() && editedTitle !== title) {
      onRename?.(editedTitle.trim());
    }
    setIsRenaming(false);
  };

  const handleRenameCancel = () => {
    setEditedTitle(title);
    setIsRenaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      handleRenameCancel();
    }
  };

  return (
    <div
      className="group relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={`w-full text-left px-3 py-2.5 rounded-xl transition-all duration-200 cursor-pointer ${
          isSelected
            ? 'bg-blue-200/60'
            : 'hover:bg-black/10'
        }`}
      >
        <div className="flex items-center justify-between gap-2">
          <div
            className="flex-1 min-w-0"
            onClick={onClick}
          >
            {isRenaming ? (
              <input
                ref={inputRef}
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onBlur={handleRenameSubmit}
                onKeyDown={handleKeyDown}
                className="w-full px-2 py-1 text-sm font-medium border border-blue-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <p className={`text-sm font-medium truncate ${
                isSelected
                  ? 'text-blue-700'
                  : 'text-gray-700 group-hover:text-gray-900'
              }`}>
                {title}
              </p>
            )}
            {lastMessage && !isRenaming && (
              <p className={`text-xs mt-0.5 truncate ${
                isSelected ? 'text-blue-400' : 'text-gray-400'
              }`}>
                {lastMessage}
              </p>
            )}
          </div>

          {/* 고정 아이콘 또는 메뉴 버튼 */}
          <div className="relative flex-shrink-0 self-center" ref={menuRef}>
            {isPinned && !isHovered && !showMenu ? (
              <div className="p-1">
                <Pin size={14} className="text-blue-500" />
              </div>
            ) : (
              <div className={`transition-opacity duration-150 ${isHovered || showMenu ? 'opacity-100' : 'opacity-0'}`}>
                <button
                  onClick={handleMenuClick}
                  className="p-1.5 hover:bg-gray-300/70 rounded-lg transition-colors"
                >
                  <EllipsisVertical size={14} className="text-gray-500" />
                </button>
              </div>
            )}

            {/* 드롭다운 메뉴 */}
            {showMenu && (
              <div className="absolute right-0 top-8 w-36 bg-white rounded-xl shadow-lg border border-gray-100 py-1.5 z-10">
                {onPin && (
                  <button
                    onClick={handlePinClick}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2.5 text-gray-700"
                  >
                    {isPinned ? (
                      <>
                        <PinOff size={14} />
                        <span>고정 해제</span>
                      </>
                    ) : (
                      <>
                        <Pin size={14} />
                        <span>고정하기</span>
                      </>
                    )}
                  </button>
                )}
                {onRename && (
                  <button
                    onClick={handleRenameClick}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2.5 text-gray-700"
                  >
                    <Pencil size={14} />
                    <span>제목 변경</span>
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={handleDeleteClick}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-red-50 flex items-center gap-2.5 text-red-500"
                  >
                    <Trash2 size={14} />
                    <span>채팅 삭제</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatListItem;
