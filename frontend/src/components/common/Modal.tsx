import { useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import Button from './Button';

interface ModalProps {
  isOpen: boolean;
  title?: string;
  message?: string;
  children?: ReactNode;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  showButtons?: boolean;
  confirmDisabled?: boolean;
}

function Modal({
  isOpen,
  title = '확인',
  message,
  children,
  confirmText = '확인',
  cancelText = '취소',
  onConfirm,
  onCancel,
  maxWidth = 'md',
  showButtons = true,
  confirmDisabled = false
}: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className={`relative bg-white rounded-xl shadow-xl p-6 ${maxWidthClasses[maxWidth]} w-full mx-4 z-10`}>
        <h2 className="text-xl font-bold mb-4 text-gray-800">{title}</h2>

        {message && <p className="text-gray-600 mb-6 whitespace-pre-line">{message}</p>}
        {children && <div className="mb-6">{children}</div>}

        {showButtons && (
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={onCancel}>
              {cancelText}
            </Button>
            <Button variant="primary" onClick={onConfirm} disabled={confirmDisabled}>
              {confirmText}
            </Button>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

export default Modal;
