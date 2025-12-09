import { Bot } from 'lucide-react';
import ChatImageSkeleton from './ChatImageSkeleton';

interface BotMessageSkeletonProps {
  chatbotName?: string;
}

function BotMessageSkeleton({ chatbotName = 'DoQ-Mate' }: BotMessageSkeletonProps) {
  return (
    <div className="flex gap-4 mb-12">
      {/* 봇 아이콘 + 로딩 애니메이션 */}
      <div className="relative flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
          <Bot size={25} className="text-blue-700" />
        </div>
        <div className="absolute inset-0 rounded-full">
          <svg className="w-10 h-10 animate-spin" viewBox="0 0 40 40">
            <defs>
              <linearGradient id="spinnerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="1" />
                <stop offset="50%" stopColor="#60a5fa" stopOpacity="1" />
                <stop offset="100%" stopColor="#93c5fd" stopOpacity="0.5" />
              </linearGradient>
            </defs>
            <circle
              cx="20"
              cy="20"
              r="18"
              stroke="currentColor"
              strokeWidth="3"
              fill="none"
              className="text-blue-600 opacity-25"
            />
            <circle
              cx="20"
              cy="20"
              r="18"
              stroke="url(#spinnerGradient)"
              strokeWidth="3"
              fill="none"
              strokeDasharray="90 150"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </div>

      {/* 스켈레톤 콘텐츠 */}
      <div className="flex-1 min-w-0">
        {/* 챗봇 이름 */}
        <div className="text-sm font-semibold text-gray-700 mb-2">
          {chatbotName}
        </div>

        {/* 이미지 스켈레톤 */}
        <div className="flex flex-wrap gap-3 mb-3">
          <ChatImageSkeleton />
          <ChatImageSkeleton />
          <ChatImageSkeleton />
        </div>

        {/* 응답 중 텍스트 with 애니메이션 */}
        <div className="text-gray-500">
          응답 중
          <span className="inline-flex ml-1">
            <span className="animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}>.</span>
            <span className="animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}>.</span>
          </span>
        </div>
      </div>
    </div>
  );
}

export default BotMessageSkeleton;
