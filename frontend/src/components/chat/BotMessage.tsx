import { useState } from 'react';
import { Bot } from 'lucide-react';
import CopyButton from '../common/CopyButton';
import ChatImagesRow from './ChatImagesRow';
import BotMessageSkeleton from './BotMessageSkeleton';
import type { ChatImage } from '../../types/chat/chat';

interface BotMessageProps {
  content?: string;
  isLoading?: boolean;
  chatbotName?: string;
  images?: ChatImage[];
}

function BotMessage({ content, isLoading = false, chatbotName = 'DoQ-Mate', images }: BotMessageProps) {
  const [isHovered, setIsHovered] = useState(false);
  const hasImages = images && images.length > 0;

  if (isLoading) {
    return <BotMessageSkeleton chatbotName={chatbotName} />;
  }

  return (
    <div
      className="flex gap-4 mb-12 group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 봇 아이콘 */}
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
          <Bot size={25} className="text-blue-700" />
        </div>
      </div>

      {/* 메시지 내용 */}
      <div className="flex-1 min-w-0 relative">
        {/* 챗봇 이름 */}
        <div className="text-sm font-semibold text-gray-700 mb-2">
          {chatbotName}
        </div>

        {/* 이미지 표시 (이미지가 있을 때만) */}
        {hasImages && <ChatImagesRow images={images} />}

        {/* 응답 내용 */}
        {content && (
          <>
            <div className="text-gray-800 whitespace-pre-wrap break-words">
              {content}
            </div>

            {/* 복사 버튼 */}
            <div
              className={`mt-3 transition-opacity duration-200 ${
                isHovered ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <CopyButton content={content} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default BotMessage;
