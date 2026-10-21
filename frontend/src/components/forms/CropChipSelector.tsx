// src/components/forms/CropChipSelector.tsx
import React from 'react';

export interface CropOption {
  id: string;
  nombre: string;
  svgIcon?: React.ReactNode;
}

export interface CropChipSelectorProps {
  id?: string;
  selectedCrop: string | null;
  onChange: (cropId: string) => void;
  options: CropOption[];
  label?: string;
  error?: string;
  disabled?: boolean;
}

export const CropChipSelector: React.FC<CropChipSelectorProps> = ({
  id = 'selector-cultivo',
  selectedCrop,
  onChange,
  options,
  label = '¿Qué sembraste el último semestre?',
  error,
  disabled = false
}) => {
  return (
    <fieldset className="w-full text-left border-none p-0 m-0" id={id} disabled={disabled}>
      {label && (
        <legend className="text-base sm:text-lg font-bold text-[#14202B] mb-2 block">
          {label} <span className="text-[#D94F4F]">*</span>
        </legend>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {options.map((opt) => {
          const isSelected = selectedCrop === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              aria-pressed={isSelected}
              onClick={() => onChange(opt.id)}
              disabled={disabled}
              className={`min-h-[56px] p-3 rounded-xl border-2 flex items-center gap-3 transition-all text-left ${
                isSelected
                  ? 'border-[#1F4D2B] bg-[#1F4D2B]/10 font-black text-[#1F4D2B] ring-1 ring-[#1F4D2B]'
                  : 'border-[#D2C8B5] bg-white text-[#14202B] hover:border-[#1F4D2B]/60'
              } ${disabled ? 'opacity-75 cursor-not-allowed' : ''}`}
            >
              <div className="w-8 h-8 rounded-lg bg-[#1F4D2B]/10 flex items-center justify-center shrink-0 text-[#1F4D2B]">
                {opt.svgIcon || (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <span className="text-base font-bold leading-tight">{opt.nombre}</span>
            </button>
          );
        })}
      </div>

      {error && (
        <span aria-live="polite" className="text-sm font-semibold text-[#D94F4F] mt-2 block">
          {error}
        </span>
      )}
    </fieldset>
  );
};
