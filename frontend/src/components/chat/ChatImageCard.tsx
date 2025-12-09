import type { ChatImage } from '../../types/chat/chat';

interface ChatImageCardProps {
  image: ChatImage;
  onClick?: () => void;
}

function ChatImageCard({ image, onClick }: ChatImageCardProps) {
  const hasData = image.img_data && image.img_data.length > 0;

  const handleClick = () => {
    if (hasData && onClick) {
      onClick();
    }
  };

  return (
    <div
      onClick={handleClick}
      title={image.description || undefined}
      className={`
        relative w-48 h-32 sm:w-56 sm:h-36 md:w-64 md:h-40
        rounded-lg overflow-hidden border border-gray-200
        ${hasData ? 'cursor-pointer hover:opacity-90' : 'cursor-default'}
        transition-opacity flex-shrink-0
      `}
    >
      {hasData ? (
        <img
          src={`data:${image.mime_type};base64,${image.img_data}`}
          alt={image.description || ''}
          className="w-full h-full object-cover select-none"
          draggable={false}
        />
      ) : (
        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
          <span className="text-gray-400 text-sm">이미지 없음</span>
        </div>
      )}
    </div>
  );
}

export default ChatImageCard;
