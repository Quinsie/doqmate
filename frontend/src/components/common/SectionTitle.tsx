import type { ReactNode } from 'react';

interface SectionTitleProps {
  icon: ReactNode;
  iconBgColor?: string;
  children: ReactNode;
}

function SectionTitle({
  icon,
  iconBgColor = 'bg-blue-100',
  children,
}: SectionTitleProps) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <div className={`w-8 h-8 rounded-lg ${iconBgColor} flex items-center justify-center`}>
        {icon}
      </div>
      <h2 className="text-lg font-semibold text-gray-900">{children}</h2>
    </div>
  );
}

export default SectionTitle;
