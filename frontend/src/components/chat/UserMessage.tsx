import { useState, useRef, useEffect } from 'react';
import { Edit2, ChevronDown, ChevronUp } from 'lucide-react';
import CopyButton from '../common/CopyButton';

interface UserMessageProps {
  content: string;
  onEdit?: (newContent: string) => void;
}

function UserMessage({ content, onEdit }: UserMessageProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [editedContent, setEditedContent] = useState(content);
  const [needsExpansion, setNeedsExpansion] = useState(false);
  const [bubbleWidth, setBubbleWidth] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const contentRef = useRef<HTMLParagraphElement>(null);
  const bubbleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [isEditing]);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [editedContent, isEditing]);

  // 메시지 길이 확인 (5줄 이상인지 체크)
  useEffect(() => {
    if (contentRef.current && !isEditing) {
      const lineHeight = parseInt(window.getComputedStyle(contentRef.current).lineHeight);
      const height = contentRef.current.scrollHeight;
      const lines = height / lineHeight;
      setNeedsExpansion(lines > 5);
    }
  }, [content, isEditing]);

  const handleEdit = () => {
    if (onEdit) {
      // 편집 시작 전 말풍선의 현재 너비 저장
      if (bubbleRef.current) {
        setBubbleWidth(bubbleRef.current.offsetWidth);
      }
      setEditedContent(content);
      setIsEditing(true);
    }
  };

  const handleCancel = () => {
    setEditedContent(content);
    setIsEditing(false);
    setBubbleWidth(null);
  };

  const handleUpdate = () => {
    if (onEdit && editedContent.trim() !== '' && editedContent !== content) {
      onEdit(editedContent.trim());
    }
    setIsEditing(false);
    setBubbleWidth(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleUpdate();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  return (
    <div className="flex justify-end mb-12">
      <div
        className="relative group"
        onMouseEnter={() => !isEditing && setIsHovered(true)}
        onMouseLeave={() => !isEditing && setIsHovered(false)}
      >
        {/* 아이콘 버튼들 */}
        {!isEditing && (
          <div
            className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full flex items-center gap-2 pr-3 transition-opacity duration-200 ${
              isHovered ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
          >
            <CopyButton content={content} />
            {onEdit && (
              <button
                onClick={handleEdit}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                aria-label="수정"
              >
                <Edit2 size={18} className="text-gray-600" />
              </button>
            )}
          </div>
        )}

        {/* 말풍선 */}
        <div
          ref={bubbleRef}
          className="bg-blue-50 text-gray-800 px-4 py-3 rounded-2xl max-w-2xl"
          style={isEditing ? { minWidth: '200px', width: bubbleWidth ? `${bubbleWidth}px` : undefined } : undefined}
        >
          {isEditing ? (
            <>
              <textarea
                ref={textareaRef}
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                className="w-full bg-transparent resize-none outline-none text-gray-800 whitespace-pre-wrap break-words"
                style={{ maxHeight: '200px', minHeight: '24px' }}
              />
              {/* 취소 및 수정 버튼 */}
              <div className="flex justify-end gap-2 mt-3">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded-2xl transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleUpdate}
                  disabled={!editedContent.trim() || editedContent === content}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-2xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  수정
                </button>
              </div>
            </>
          ) : (
            <>
              <p
                ref={contentRef}
                className={`whitespace-pre-wrap break-words ${!isExpanded && needsExpansion ? 'line-clamp-5' : ''}`}
              >
                {content}
              </p>
              {needsExpansion && (
                <div className="flex justify-end">
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex mt-2 transition-colors cursor-pointer hover:bg-black/10 rounded-full"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp size={20} className='cursor-pointer m-2' />
                      </>
                    ) : (
                      <>
                        <ChevronDown size={20} className='cursor-pointer m-2' />
                      </>
                    )}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default UserMessage;
