import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}

export default function Card({ title, children, className = '', actions }: CardProps) {
  return (
    <div className={`bg-white rounded-xl border border-bg-border shadow-sm shadow-fg-primary/5 ${className}`}>
      {title && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-bg-border">
          <h4 className="font-bold text-sm text-fg-primary">{title}</h4>
          {actions}
        </div>
      )}
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}