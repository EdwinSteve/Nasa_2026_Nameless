// src/components/forms/ConsentCard.tsx
import React from 'react';

export interface ConsentCardProps {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  error?: string;
  versionPolitica?: string | null;
  urlTexto?: string | null;
  isLoading?: boolean;
  loadError?: string | null;
  onRetryLoad?: () => void;
  disabled?: boolean;
}

export const ConsentCard: React.FC<ConsentCardProps> = ({
  id = 'consentimiento-datos',
  checked,
  onChange,
  error,
  versionPolitica,
  urlTexto,
  isLoading = false,
  loadError = null,
  onRetryLoad,
  disabled = false
}) => {
  if (isLoading) {
    return (
      <div className="p-4 sm:p-5 rounded-xl border-2 border-[#D2C8B5] bg-white/70 flex items-center justify-between text-left">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 animate-spin text-[#1F4D2B]" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span className="text-sm sm:text-base font-semibold text-[#14202B]/80">
            Cargando la política de datos...
          </span>
        </div>
        <input
          type="checkbox"
          disabled
          aria-label="Cargando política"
          className="w-7 h-7 min-w-[28px] min-h-[28px] rounded-lg border-2 border-gray-300 cursor-not-allowed opacity-50"
        />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="p-4 sm:p-5 rounded-xl border-2 border-[#D94F4F] bg-[#FFF5F5] flex items-center justify-between gap-3 text-left">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-[#D94F4F] shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-sm font-semibold text-[#D94F4F]">
            {loadError}
          </span>
        </div>
        {onRetryLoad && (
          <button
            type="button"
            onClick={onRetryLoad}
            className="px-3 py-1.5 bg-[#D94F4F] hover:bg-[#B93838] text-white rounded-lg font-bold text-xs shrink-0"
          >
            Reintentar
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className={`p-4 sm:p-5 rounded-xl border-2 transition-colors ${
        error ? 'border-[#D94F4F] bg-[#FFF5F5]' : 'border-[#D2C8B5] bg-white'
      }`}
    >
      <label htmlFor={id} className="flex items-start gap-3.5 cursor-pointer select-none">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
          className="mt-1 w-7 h-7 min-w-[28px] min-h-[28px] shrink-0 rounded-lg border-2 border-[#1F4D2B] accent-[#1F4D2B] focus:ring-[#1F4D2B] cursor-pointer"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
        />
        <div className="text-sm sm:text-base text-[#14202B] leading-relaxed text-left">
          <span>Autorizo el tratamiento de mis datos personales según la </span>
          <span className="font-bold text-[#1F4D2B]">Ley 1581 de 2012</span>
          <span> de protección de datos en Colombia {versionPolitica ? `(Versión ${versionPolitica})` : ''} exclusivamente para recibir recomendaciones agroclimáticas de mi finca. </span>
          {urlTexto && (
            <a
              href={urlTexto}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#1F4D2B] font-bold underline hover:text-[#16381F] inline-block ml-1"
            >
              Ver política de privacidad
            </a>
          )}
        </div>
      </label>

      {error && (
        <span id={`${id}-error`} aria-live="polite" className="text-sm font-semibold text-[#D94F4F] mt-2.5 block text-left">
          {error}
        </span>
      )}
    </div>
  );
};
