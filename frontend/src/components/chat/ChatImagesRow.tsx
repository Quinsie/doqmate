import { useState } from 'react';
import { X } from 'lucide-react';
import ChatImageCard from './ChatImageCard';
import type { ChatImage } from '../../types/chat/chat';

interface ChatImagesRowProps {
  images: ChatImage[];
}

function ChatImagesRow({ images }: ChatImagesRowProps) {
  const [expandedImage, setExpandedImage] = useState<ChatImage | null>(null);

  const validImages = images.filter((img) => img.img_data && img.img_data.length > 0);

  if (validImages.length === 0) return null;

  return (
    <div className="mb-3">
      {/* 이미지 썸네일 목록 */}
      <div className="overflow-x-auto pb-2">
        <div className="flex gap-3 w-fit">
          {validImages.map((img) => (
            <ChatImageCard
              key={img.id}
              image={img}
              onClick={() => setExpandedImage(img)}
            />
          ))}
        </div>
      </div>

      {/* 확대된 이미지 */}
      {expandedImage && (
        <div
          className="relative mt-3 cursor-pointer"
          onClick={() => setExpandedImage(null)}
        >
          <img
            src={`data:${expandedImage.mime_type};base64,${expandedImage.img_data}`}
            alt={expandedImage.description || ''}
            title={expandedImage.description || undefined}
            className="w-full rounded-lg object-contain border border-gray-200"
          />
          <button
            className="absolute top-2 right-2 p-1.5 bg-black/50 hover:bg-black/70 rounded-full transition-colors"
            aria-label="닫기"
          >
            <X size={18} className="text-white" />
          </button>
        </div>
      )}
    </div>
  );
}

export default ChatImagesRow;