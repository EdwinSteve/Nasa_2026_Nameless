// src/components/forms/PhoneInput.tsx
import React from 'react';

export interface PhoneInputProps {
  id?: string;
  value: string;
  onChange: (val: string) => void;
  error?: string;
  label?: string;
  helperText?: string;
  disabled?: boolean;
  onNavigateLogin?: () => void;
  duplicateError?: boolean;
}

export const PhoneInput: React.FC<PhoneInputProps> = ({
  id = 'telefono-celular',
  value,
  onChange,
  error,
  label = 'Número de celular',
  helperText = 'Aquí le avisaremos cuándo sembrar y regar.',
  disabled = false,
  onNavigateLogin,
  duplicateError = false
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const cleaned = e.target.value.replace(/\D/g, '').slice(0, 10);
    onChange(cleaned);
  };

  return (
    <div className="flex flex-col w-full text-left">
      <label htmlFor={id} className="text-base sm:text-lg font-bold text-[#14202B] mb-1.5">
        {label} <span className="text-[#D94F4F]">*</span>
      </label>

      <div className="relative flex items-center">
        {/* Prefijo Colombia limpio de 72px */}
        <div className="absolute left-3 flex items-center pointer-events-none pr-3 border-r-2 border-[#D2C8B5]">
          <span className="font-extrabold text-base sm:text-lg text-[#14202B]">+57</span>
        </div>

        <input
          id={id}
          type="tel"
          inputMode="numeric"
          pattern="[0-9]*"
          value={value}
          onChange={handleChange}
          disabled={disabled}
          placeholder="314 000 0000"
          className={`w-full min-h-[56px] h-14 pl-[72px] pr-4 bg-white rounded-xl text-lg font-semibold text-[#14202B] border-2 transition-all outline-none ${
            error
              ? 'border-[#D94F4F] focus:ring-2 focus:ring-[#D94F4F]/20'
              : 'border-[#D2C8B5] focus:border-[#1F4D2B] focus:ring-2 focus:ring-[#1F4D2B]/20'
          } ${disabled ? 'bg-[#EDE7DA] cursor-not-allowed opacity-75' : ''}`}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : `${id}-helper`}
        />
      </div>

      {error ? (
        <div id={`${id}-error`} aria-live="polite" className="text-sm font-semibold text-[#D94F4F] mt-1.5 flex flex-wrap items-center gap-1.5">
          <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>{error}</span>
          {duplicateError && onNavigateLogin && (
            <button
              type="button"
              onClick={onNavigateLogin}
              className="text-[#1F4D2B] font-black underline ml-1 hover:text-[#16381F] inline"
            >
              Ingresar aquí
            </button>
          )}
        </div>
      ) : (
        <span id={`${id}-helper`} className="text-sm text-[#14202B]/70 mt-1.5">
          {helperText}
        </span>
      )}
    </div>
  );
};
