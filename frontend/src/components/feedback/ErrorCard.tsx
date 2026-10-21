// src/components/feedback/ErrorCard.tsx
import React from 'react';

export interface ErrorCardProps {
  mensaje: string;
  codigo?: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export const ErrorCard: React.FC<ErrorCardProps> = ({
  mensaje,
  codigo,
  onRetry,
  retryLabel = 'Reintentar'
}) => {
  return (
    <div
      role="alert"
      className="mb-5 p-4 rounded-2xl border-2 border-[#D94F4F] bg-[#FFF5F5] text-left flex flex-col gap-3"
    >
      <div className="flex items-start gap-3">
        <svg className="w-6 h-6 text-[#D94F4F] shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <div>
          <p className="text-base font-extrabold text-[#14202B]">Algo salió mal</p>
          <p className="text-sm text-[#14202B]/80">{mensaje}</p>
          {codigo && <p className="text-sm font-mono text-[#14202B]/60 mt-1">Código: {codigo}</p>}
        </div>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="min-h-[56px] w-full rounded-xl bg-[#D94F4F] hover:bg-[#B93838] text-white font-bold text-base"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
};
