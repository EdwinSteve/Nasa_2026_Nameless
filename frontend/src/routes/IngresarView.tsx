// src/routes/IngresarView.tsx
'use client';

import React, { useState } from 'react';
import { PhoneInput } from '../components/forms/PhoneInput';
import { ErrorCard } from '../components/feedback/ErrorCard';
import type { ErrorApi } from '../api/tipos';
import { iniciarSesion } from '../api/services';

export interface IngresarViewProps {
  onNavigate: (path: string) => void;
}

export const IngresarView: React.FC<IngresarViewProps> = ({ onNavigate }) => {
  const [celular, setCelular] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [mostrarContrasena, setMostrarContrasena] = useState(false);
  const [errores, setErrores] = useState<{ celular?: string; contrasena?: string }>({});
  const [errorApi, setErrorApi] = useState<ErrorApi | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [ingresado, setIngresado] = useState(false);

  async function alEnviar(e: React.FormEvent) {
    e.preventDefault();
    const errs: typeof errores = {};
    if (celular.length !== 10 || !celular.startsWith('3')) {
      errs.celular = 'El celular debe tener 10 dígitos y empezar por el número 3.';
    }
    if (!contrasena) errs.contrasena = 'Escribe tu contraseña.';
    setErrores(errs);
    if (Object.keys(errs).length) return;

    setEnviando(true);
    setErrorApi(null);
    try {
      await iniciarSesion({ celular, contrasena });
      setIngresado(true);
      onNavigate('/inicio');
    } catch (err) {
      setErrorApi(err as ErrorApi);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="min-h-dvh bg-[#F7F3EA] text-[#14202B]">
      <div className="max-w-md mx-auto px-4 py-8 flex flex-col gap-6">
        <button
          type="button"
          onClick={() => onNavigate('/')}
          className="self-start min-h-11 font-bold text-[#1F4D2B] hover:underline"
        >
          ← Volver
        </button>

        <header>
          <h1 className="font-titulo text-3xl font-black text-[#1F4D2B]">Ingresa a SURCO</h1>
          <p className="mt-2 text-lg text-[#14202B]/80">Usa el celular y la contraseña con que creaste tu cuenta.</p>
        </header>

        {ingresado ? (
          <div role="status" className="p-4 bg-[#E8E1D3] rounded-2xl border-2 border-[#1F4D2B] flex flex-col gap-1">
            <p className="text-lg font-extrabold">Ya iniciaste sesión</p>
            <p className="text-[#14202B]/80">Te llevamos a tu inicio…</p>
          </div>
        ) : (
          <form onSubmit={alEnviar} noValidate className="flex flex-col gap-5">
            {errorApi && <ErrorCard mensaje={errorApi.mensaje} codigo={errorApi.codigo} />}

            <PhoneInput
              id="ingresar-celular"
              value={celular}
              onChange={setCelular}
              error={errores.celular}
              helperText="El mismo número con que te registraste."
              disabled={enviando}
            />

            <div className="flex flex-col">
              <label htmlFor="ingresar-contrasena" className="text-base sm:text-lg font-bold mb-1.5">
                Contraseña <span className="text-[#D94F4F]">*</span>
              </label>
              <div className="relative">
                <input
                  id="ingresar-contrasena"
                  type={mostrarContrasena ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={contrasena}
                  onChange={(e) => setContrasena(e.target.value)}
                  disabled={enviando}
                  aria-invalid={Boolean(errores.contrasena)}
                  aria-describedby={errores.contrasena ? 'ingresar-contrasena-error' : undefined}
                  className={`w-full min-h-[56px] h-14 pl-4 pr-[72px] bg-white rounded-xl text-lg font-semibold border-2 outline-none transition-all ${
                    errores.contrasena
                      ? 'border-[#D94F4F] focus:ring-2 focus:ring-[#D94F4F]/20'
                      : 'border-[#D2C8B5] focus:border-[#1F4D2B] focus:ring-2 focus:ring-[#1F4D2B]/20'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setMostrarContrasena((v) => !v)}
                  aria-pressed={mostrarContrasena}
                  aria-label={mostrarContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  className="absolute right-2 top-1/2 -translate-y-1/2 min-h-11 px-3 font-bold text-[#1F4D2B]"
                >
                  {mostrarContrasena ? 'Ocultar' : 'Ver'}
                </button>
              </div>
              {errores.contrasena && (
                <span id="ingresar-contrasena-error" aria-live="polite" className="text-sm font-semibold text-[#D94F4F] mt-1.5">
                  {errores.contrasena}
                </span>
              )}
            </div>

            <button
              type="submit"
              disabled={enviando}
              className="min-h-14 w-full rounded-2xl bg-[#1F4D2B] hover:bg-[#16381F] disabled:opacity-60 font-titulo text-lg font-extrabold text-white shadow-md"
            >
              {enviando ? 'Ingresando…' : 'Ingresar'}
            </button>
          </form>
        )}

        <p className="text-center text-base">
          ¿Aún no tienes cuenta?{' '}
          <button type="button" onClick={() => onNavigate('/registro')} className="font-black text-[#1F4D2B] underline">
            Crear mi cuenta
          </button>
        </p>
      </div>
    </main>
  );
};
