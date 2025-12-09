import type { ReactNode, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'white' | 'red';
  size?: 'small' | 'medium' | 'large';
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
}

function Button({
  children,
  variant = 'primary',
  size = 'medium',
  icon,
  iconPosition = 'left',
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const hasRoundedClass = className.includes('rounded');

  const baseClasses = `
    font-medium transition-all duration-200
    inline-flex items-center justify-center
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
    ${hasRoundedClass ? '' : 'rounded-lg'}
  `;

  const variantClasses: Record<string, string> = {
    primary: `
      bg-blue-600 hover:bg-blue-700 active:bg-blue-800
      text-white shadow-sm hover:shadow
      focus:ring-blue-500
    `,
    secondary: `
      bg-gray-100 hover:bg-gray-200 active:bg-gray-300
      text-gray-700
      focus:ring-gray-400
    `,
    outline: `
      border border-gray-300 hover:border-gray-400
      bg-white hover:bg-gray-50 active:bg-gray-100
      text-gray-700
      focus:ring-gray-400
    `,
    white: `
      bg-white hover:bg-gray-50 active:bg-gray-100
      text-gray-700 shadow-sm hover:shadow
      focus:ring-gray-400
    `,
    red: `
      bg-red-400 hover:bg-red-500 active:bg-red-600
      text-white shadow-sm hover:shadow
      focus:ring-red-500
    `,
  };

  const sizeClasses: Record<string, string> = {
    small: 'text-sm py-1.5 px-3',
    medium: 'text-sm py-2 px-4',
    large: 'text-base py-2.5 px-5',
  };

  const gapClass = icon ? 'gap-2' : '';

  return (
    <button
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${gapClass}
        ${className}
      `}
      disabled={disabled}
      {...props}
    >
      {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
      {icon ? <span>{children}</span> : children}
      {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
    </button>
  );
}

export default Button;
