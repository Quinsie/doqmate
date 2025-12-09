import type { ReactNode } from 'react';

interface ResultBoxProps {
  type: 'success' | 'info' | 'warning';
  children: ReactNode;
}

function ResultBox({ type, children }: ResultBoxProps) {
  const colorClasses = {
    success: 'bg-green-50 border-green-200',
    info: 'bg-blue-50 border-blue-200',
    warning: 'bg-yellow-50 border-yellow-200',
  };

  return (
    <div className={`border rounded-lg p-4 ${colorClasses[type]}`}>
      {children}
    </div>
  );
}

export default ResultBox;
