import type { ReactNode } from 'react';

interface PageHeroProps {
  icon: ReactNode;
  title: string;
  description?: string;
  gradient?: string;
}

function PageHero({
  icon,
  title,
  description,
  gradient = 'from-blue-500 via-blue-600 to-indigo-600',
}: PageHeroProps) {
  return (
    <div className="mb-12 text-center">
      <div className={`inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br ${gradient} shadow-2xl shadow-blue-500/30 mb-6`}>
        {icon}
      </div>
      <h1 className="text-3xl font-bold text-gray-900 mb-3">{title}</h1>
      {description && (
        <p className="text-gray-500 text-lg">{description}</p>
      )}
    </div>
  );
}

export default PageHero;
