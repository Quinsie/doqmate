import { useState } from 'react';
import type { InputHTMLAttributes } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface PasswordInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  required?: boolean;
}

function PasswordInput({
  label,
  error,
  required = false,
  className = '',
  ...props
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  return (
    <div>
      {label && (
        <label htmlFor={props.id} className="block text-sm font-medium text-gray-700 mb-1">
          {label} {required && '*'}
        </label>
      )}
      <div className="relative">
        <input
          type={showPassword ? 'text' : 'password'}
          className={`
            w-full px-4 py-2 pr-10 border rounded-lg
            focus:outline-none focus:ring-2
            ${
              error
                ? 'border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:ring-blue-500'
            }
            ${className}
          `}
          {...props}
        />
        <button
          type="button"
          onClick={togglePasswordVisibility}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
          tabIndex={-1}
        >
          {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
        </button>
      </div>
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  );
}

export default PasswordInput;
