import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CopyButtonProps {
  content: string;
  className?: string;
}

function CopyButton({ content, className = '' }: CopyButtonProps) {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('복사 실패:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`p-2 hover:bg-gray-200 rounded-lg transition-colors ${className}`}
      aria-label="복사"
    >
      {isCopied ? (
        <Check size={18} className="text-gray-600" />
      ) : (
        <Copy size={18} className="text-gray-600" />
      )}
    </button>
  );
}

export default CopyButton;
