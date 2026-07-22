import type { InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  label?: string;
  error?: string;
  icon?: string;
  prefix?: ReactNode;
  suffix?: ReactNode;
}

export default function Input({
  label,
  error,
  icon,
  prefix,
  suffix,
  className = '',
  ...props
}: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-xs text-fg-secondary font-medium">
          {label}
        </label>
      )}
      <div className="relative">
        {prefix && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-fg-tertiary">
            {prefix}
          </span>
        )}
        {icon && !prefix && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-fg-tertiary iconify" data-icon={icon} />
        )}
        <input
          className={`w-full px-4 py-2.5 bg-bg-subtle border border-bg-border rounded-lg text-sm focus:outline-none focus:border-brand focus:bg-white transition-colors ${
            error ? 'border-danger' : ''
          } ${prefix || icon ? 'pl-9' : ''} ${suffix ? 'pr-9' : ''} ${className}`}
          {...props}
        />
        {suffix && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-fg-tertiary">
            {suffix}
          </span>
        )}
      </div>
      {error && (
        <p className="text-xs text-danger">{error}</p>
      )}
    </div>
  );
}