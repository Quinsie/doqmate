import { Trash2 } from 'lucide-react';
import Button from '../../../common/Button';


export interface ChatbotActionsProps {
  chatbotId: string;
  hasManual?: boolean;
  onAddManual?: (chatbotId: string) => void;
  onEditManual?: (chatbotId: string) => void;
  onDeleteManual?: (chatbotId: string) => void;
}

function ChatbotActions({
  chatbotId,
  hasManual = false,
  onAddManual,
  onEditManual,
  onDeleteManual
}: ChatbotActionsProps) {
  return (
    <div className="flex gap-2 justify-center items-center">
      {hasManual ? (
        <>
          <Button
            variant="secondary"
            size="small"
            onClick={() => onEditManual?.(chatbotId)}
          >
            매뉴얼 수정
          </Button>
          <button
            onClick={() => onDeleteManual?.(chatbotId)}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors"
            aria-label="매뉴얼 삭제"
          >
            <Trash2 size={18} className="text-gray-600" />
          </button>
        </>
      ) : (
        <Button
          variant="secondary"
          size="small"
          onClick={() => onAddManual?.(chatbotId)}
        >
          매뉴얼 추가
        </Button>
      )}
    </div>
  );
}

export default ChatbotActions;
