import type { ReactNode } from 'react';

interface ContainerProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: 'none' | 'small' | 'medium' | 'large';
  background?: 'white' | 'gray' | 'transparent';
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  fullHeight?: boolean;
  centered?: boolean;
}

function Container({
  children,
  className = '',
  maxWidth = 'md',
  padding = 'medium',
  background = 'white',
  shadow = 'lg',
  rounded = '2xl',
  fullHeight = false,
  centered = false,
}: ContainerProps) {
  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-full',
  };

  const paddingClasses = {
    none: 'p-0',
    small: 'p-4',
    medium: 'p-8',
    large: 'p-12',
  };

  const backgroundClasses = {
    white: 'bg-white',
    gray: 'bg-gray-50',
    transparent: 'bg-transparent',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
  };

  const roundedClasses = {
    none: '',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full',
  };

  return (
    <div
      className={`
        ${fullHeight ? 'min-h-screen' : ''}
        ${centered ? 'flex items-center justify-center' : ''}
        ${centered ? 'bg-gradient-to-br from-blue-50 to-blue-100 p-4' : ''}
      `}
    >
      <div
        className={`
          ${backgroundClasses[background]}
          ${paddingClasses[padding]}
          ${roundedClasses[rounded]}
          ${shadowClasses[shadow]}
          ${maxWidthClasses[maxWidth]}
          w-full
          ${className}
        `}
      >
        {children}
      </div>
    </div>
  );
}

export default Container;
