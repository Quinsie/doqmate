interface DividerProps {
  className?: string;
}

function Divider({ className = '' }: DividerProps) {
  return <div className={`border-t border-gray-200 ${className}`} />;
}

export default Divider;
