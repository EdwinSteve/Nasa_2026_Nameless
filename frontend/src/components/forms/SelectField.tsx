// src/components/forms/SelectField.tsx
import React from 'react';

export interface SelectOption {
  codigo: string;
  nombre: string;
}

export interface SelectFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  error?: string;
  helperText?: string;
  required?: boolean;
  onRetry?: () => void;
}

export const SelectField: React.FC<SelectFieldProps> = ({
  id,
  label,
  value,
  onChange,
  options,
  placeholder = 'Selecciona una opción',
  disabled = false,
  isLoading = false,
  error,
  helperText,
  required = false,
  onRetry
}) => {
  return (
    <div className="flex flex-col w-full text-left">
      <label htmlFor={id} className="text-base sm:text-lg font-bold text-[#14202B] mb-1.5 flex items-center justify-between">
        <span>
          {label} {required && <span className="text-[#D94F4F]">*</span>}
        </span>
        {isLoading && (
          <span className="text-xs font-semibold text-[#1F4D2B] flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Cargando...
          </span>
        )}
      </label>

      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled || isLoading}
          className={`w-full min-h-[56px] h-14 pl-4 pr-11 bg-white rounded-xl text-base sm:text-lg font-semibold text-[#14202B] border-2 transition-all outline-none appearance-none ${
            error
              ? 'border-[#D94F4F] focus:ring-2 focus:ring-[#D94F4F]/20'
              : 'border-[#D2C8B5] focus:border-[#1F4D2B] focus:ring-2 focus:ring-[#1F4D2B]/20'
          } ${disabled ? 'bg-[#EDE7DA] cursor-not-allowed opacity-70 text-[#14202B]/50' : 'cursor-pointer'}`}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
        >
          <option value="" disabled>
            {isLoading ? 'Cargando opciones...' : placeholder}
          </option>
          {options.map((opt) => (
            <option key={opt.codigo} value={opt.codigo}>
              {opt.nombre}
            </option>
          ))}
        </select>

        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[#14202B]/60">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {error ? (
        <div id={`${id}-error`} aria-live="polite" className="text-sm font-semibold text-[#D94F4F] mt-1.5 flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </span>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="text-xs font-black text-[#1F4D2B] underline hover:text-[#16381F] shrink-0"
            >
              Reintentar
            </button>
          )}
        </div>
      ) : (
        helperText && (
          <span id={`${id}-helper`} className="text-sm text-[#14202B]/70 mt-1.5">
            {helperText}
          </span>
        )
      )}
    </div>
  );
};
