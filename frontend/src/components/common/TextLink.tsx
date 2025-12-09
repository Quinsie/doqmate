interface TextLinkProps {
  children: React.ReactNode;
  onClick: () => void;
  color?: 'black' | 'blue';
  className?: string;
}

function TextLink({ children, onClick, color = 'black', className = '' }: TextLinkProps) {
  const baseClasses = 'hover:underline transition-colors';

  const colorClasses = {
    black: 'text-gray-900 hover:text-gray-700',
    blue: 'text-blue-600 hover:text-blue-700',
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${baseClasses} ${colorClasses[color]} ${className} cursor-pointer`}
    >
      {children}
    </button>
  );
}

export default TextLink;
