import type { TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  success?: string;
  required?: boolean;
}

function Textarea({
  label,
  error,
  success,
  required = false,
  className = '',
  ...props
}: TextareaProps) {
  return (
    <div>
      {label && (
        <label htmlFor={props.id} className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {!required && <span className="text-gray-400 font-normal ml-1">(선택)</span>}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        className={`
          w-full px-4 py-3 border rounded-lg
          focus:outline-none focus:ring-2 focus:border-transparent
          resize-none transition-shadow
          ${
            error
              ? 'border-red-500 focus:ring-red-500'
              : success
              ? 'border-green-500 focus:ring-green-500'
              : 'border-gray-300 focus:ring-blue-500'
          }
          ${className}
        `}
        {...props}
      />
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
      {success && <p className="text-sm text-green-600 mt-1">{success}</p>}
    </div>
  );
}

export default Textarea;
