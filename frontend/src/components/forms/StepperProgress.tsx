// src/components/forms/StepperProgress.tsx
import React from 'react';

export interface StepperProgressProps {
  currentStep: number;
  totalSteps: number;
  stepLabels: readonly string[];
  percentageCompleted: number;
}

export const StepperProgress: React.FC<StepperProgressProps> = ({
  currentStep,
  totalSteps,
  stepLabels,
  percentageCompleted
}) => {
  const etiquetaActual = stepLabels[currentStep - 1] ?? '';

  return (
    <header className="sticky top-0 z-20 bg-[#F7F3EA]/95 backdrop-blur border-b-2 border-[#E8E1D3]">
      <div className="max-w-xl mx-auto px-4 sm:px-6 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg font-black tracking-tight text-[#1F4D2B]">SURCO</span>
          <span aria-live="polite" className="text-sm font-bold text-[#14202B]/80">
            Paso {currentStep} de {totalSteps} · {etiquetaActual}
          </span>
        </div>

        <div
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percentageCompleted}
          aria-label="Progreso del registro"
          className="h-2.5 w-full bg-[#E8E1D3] rounded-full overflow-hidden"
        >
          <div
            className="h-full bg-[#1F4D2B] rounded-full transition-all duration-300"
            style={{ width: `${percentageCompleted}%` }}
          />
        </div>

        <ol className="hidden sm:grid mt-2 text-xs font-bold" style={{ gridTemplateColumns: `repeat(${totalSteps}, minmax(0, 1fr))` }}>
          {stepLabels.map((etiqueta, i) => {
            const paso = i + 1;
            const estado = paso < currentStep ? 'hecho' : paso === currentStep ? 'actual' : 'pendiente';
            return (
              <li
                key={etiqueta}
                aria-current={estado === 'actual' ? 'step' : undefined}
                className={`text-center ${
                  estado === 'actual'
                    ? 'text-[#1F4D2B]'
                    : estado === 'hecho'
                      ? 'text-[#14202B]/70'
                      : 'text-[#14202B]/40'
                }`}
              >
                {estado === 'hecho' ? '✓ ' : ''}
                {etiqueta}
              </li>
            );
          })}
        </ol>
      </div>
    </header>
  );
};
