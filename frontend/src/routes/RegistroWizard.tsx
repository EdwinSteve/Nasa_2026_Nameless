// src/routes/RegistroWizard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { StepperProgress } from '../components/forms/StepperProgress';
import { PhoneInput } from '../components/forms/PhoneInput';
import { ConsentCard } from '../components/forms/ConsentCard';
import { SelectField } from '../components/forms/SelectField';
import { CropChipSelector, type CropOption } from '../components/forms/CropChipSelector';
import { MapDrawer, type MapMode } from '../components/forms/MapDrawer';
import { PriorityRanker } from '../components/forms/PriorityRanker';
import { ErrorCard } from '../components/feedback/ErrorCard';
import { calcularAreaHa } from '../lib/geo';
import type {
  ErrorApi,
  GeoJSONPolygon,
  TipoRiego,
  PrioridadTipo,
  PoliticaVigente,
  MunicipioItem,
  CorregimientoItem
} from '../api/tipos';
import {
  obtenerPoliticaVigente,
  registrarUsuario,
  guardarTokens,
  listarMunicipios,
  listarCorregimientos,
  crearFinca,
  crearLote,
  guardarPreferencias,
  iniciarDiagnostico
} from '../api/services';

const STEP_LABELS: [string, string, string, string] = [
  'Tus datos',
  'Tu finca',
  'Marca tu lote',
  'Prioridades'
];

const CROP_OPTIONS: CropOption[] = [
  { id: 'maiz', nombre: 'Maíz' },
  { id: 'frijol', nombre: 'Fríjol' },
  { id: 'arroz', nombre: 'Arroz' },
  { id: 'cafe', nombre: 'Café' },
  { id: 'cacao', nombre: 'Cacao' },
  { id: 'soya', nombre: 'Soya' },
  { id: 'ninguno', nombre: 'Nada / lote nuevo' }
];

const RIEGO_OPTIONS: { id: TipoRiego; nombre: string }[] = [
  { id: 'gravedad', nombre: 'Por gravedad' },
  { id: 'aspersion', nombre: 'Aspersión' },
  { id: 'goteo', nombre: 'Goteo' }
];

// Clases compartidas por los inputs de texto del wizard
const inputClase = (error: string | undefined, bloqueado: boolean) =>
  `w-full min-h-[56px] h-14 px-4 rounded-xl text-lg font-semibold text-[#14202B] border-2 outline-none transition-all ${
    bloqueado ? 'bg-[#EDE7DA] cursor-not-allowed opacity-80' : 'bg-white'
  } ${
    error
      ? 'border-[#D94F4F] focus:ring-2 focus:ring-[#D94F4F]/20'
      : 'border-[#D2C8B5] focus:border-[#1F4D2B] focus:ring-2 focus:ring-[#1F4D2B]/20'
  }`;

const etiquetaClase = 'text-base sm:text-lg font-bold text-[#14202B] mb-1.5 block';

const MensajeError: React.FC<{ id: string; mensaje?: string }> = ({ id, mensaje }) =>
  mensaje ? (
    <span id={id} aria-live="polite" className="text-sm font-semibold text-[#D94F4F] mt-1.5 block">
      {mensaje}
    </span>
  ) : null;

const AvisoGuardado: React.FC<{ titulo: string; detalle: string }> = ({ titulo, detalle }) => (
  <div className="p-4 bg-[#E8E1D3] rounded-2xl border-2 border-[#1F4D2B] text-left flex items-center gap-3">
    <svg className="w-6 h-6 text-[#1F4D2B] shrink-0" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
    <div>
      <h4 className="font-extrabold text-base text-[#14202B]">{titulo}</h4>
      <p className="text-xs text-[#14202B]/70">{detalle}</p>
    </div>
  </div>
);

export interface RegistroWizardProps {
  onNavigate?: (path: string) => void;
}

export const RegistroWizard: React.FC<RegistroWizardProps> = ({
  onNavigate = (path) => console.log('[Router Navigation] ->', path)
}) => {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [backendError, setBackendError] = useState<ErrorApi | null>(null);

  // --- IDs persistidos (cero IDs inventados) ---
  const [usuarioId, setUsuarioId] = useState<string | null>(null);
  const [fincaId, setFincaId] = useState<string | null>(null);
  const [loteId, setLoteId] = useState<string | null>(null);

  // --- Catálogos y estados de error ---
  const [municipiosOptions, setMunicipiosOptions] = useState<MunicipioItem[]>([]);
  const [corregimientosOptions, setCorregimientosOptions] = useState<CorregimientoItem[]>([]);
  const [loadingMunicipios, setLoadingMunicipios] = useState<boolean>(false);
  const [loadingCorregimientos, setLoadingCorregimientos] = useState<boolean>(false);
  const [errorCargaMunicipios, setErrorCargaMunicipios] = useState<string | null>(null);
  const [errorCargaCorregimientos, setErrorCargaCorregimientos] = useState<string | null>(null);

  // --- Política vigente ---
  const [politicaVigente, setPoliticaVigente] = useState<PoliticaVigente | null>(null);
  const [loadingPolitica, setLoadingPolitica] = useState<boolean>(true);
  const [errorCargaPolitica, setErrorCargaPolitica] = useState<string | null>(null);

  // --- Estado Paso 1 (Tus Datos) ---
  const [nombreCompleto, setNombreCompleto] = useState<string>('');
  const [celular, setCelular] = useState<string>('');
  const [correo, setCorreo] = useState<string>('');
  const [contrasena, setContrasena] = useState<string>('');
  const [mostrarContrasena, setMostrarContrasena] = useState<boolean>(false);
  const [municipioResidencia, setMunicipioResidencia] = useState<string>('41001'); // Neiva
  const [aceptaPolitica, setAceptaPolitica] = useState<boolean>(false);
  const [errorsPaso1, setErrorsPaso1] = useState<{ [campo: string]: string }>({});
  const [celularDuplicado, setCelularDuplicado] = useState<boolean>(false);

  // --- Estado Paso 2 (Tu Finca) ---
  const [nombreFinca, setNombreFinca] = useState<string>('');
  const [municipioFinca, setMunicipioFinca] = useState<string>('41001');
  const [corregimientoFinca, setCorregimientoFinca] = useState<string>(''); // Vacío por defecto
  const [veredaFinca, setVeredaFinca] = useState<string>('');
  const [errorsPaso2, setErrorsPaso2] = useState<{ [campo: string]: string }>({});

  // --- Estado Paso 3 (Marca tu Lote) ---
  const [nombreLote, setNombreLote] = useState<string>('');
  const [mapModo, setMapModo] = useState<MapMode>('dibujar');
  const [poligonoCoords, setPoligonoCoords] = useState<GeoJSONPolygon | null>(null);
  const [tieneRiego, setTieneRiego] = useState<boolean | null>(null);
  const [tipoRiego, setTipoRiego] = useState<TipoRiego | null>(null);
  const [cultivoAnterior, setCultivoAnterior] = useState<string | null>(null);
  const [errorsPaso3, setErrorsPaso3] = useState<{ [campo: string]: string }>({});

  // --- Estado Paso 4 (Prioridades) ---
  const [prioridadesOrden, setPrioridadesOrden] = useState<PrioridadTipo[]>([
    'ahorro_agua',
    'ganar_mas',
    'cuidar_suelo',
    'arriesgar_menos'
  ]);

  const areaLoteHa = poligonoCoords ? calcularAreaHa(poligonoCoords) : null;

  // Carga inicial de política de datos
  const fetchPolitica = async () => {
    setLoadingPolitica(true);
    setErrorCargaPolitica(null);
    try {
      const pol = await obtenerPoliticaVigente();
      setPoliticaVigente(pol);
    } catch {
      setErrorCargaPolitica('No pudimos cargar la política de privacidad.');
    } finally {
      setLoadingPolitica(false);
    }
  };

  // Carga inicial de municipios de Huila
  const fetchMunicipios = async () => {
    setLoadingMunicipios(true);
    setErrorCargaMunicipios(null);
    try {
      const muns = await listarMunicipios('41');
      setMunicipiosOptions(muns);
    } catch {
      setErrorCargaMunicipios('No pudimos cargar los municipios.');
    } finally {
      setLoadingMunicipios(false);
    }
  };

  useEffect(() => {
    void fetchPolitica();
    void fetchMunicipios();
  }, []);

  // Carga de corregimientos cuando cambia el municipio de la finca
  const fetchCorregimientos = async (munCodigo: string) => {
    if (!munCodigo) {
      setCorregimientosOptions([]);
      setCorregimientoFinca('');
      return;
    }
    setLoadingCorregimientos(true);
    setErrorCargaCorregimientos(null);
    try {
      const corrs = await listarCorregimientos(munCodigo);
      setCorregimientosOptions(corrs);
      // Deja el valor vacío sin seleccionar ninguno automáticamente
      setCorregimientoFinca('');
    } catch {
      setErrorCargaCorregimientos('No pudimos cargar los corregimientos de este municipio.');
      setCorregimientosOptions([]);
    } finally {
      setLoadingCorregimientos(false);
    }
  };

  useEffect(() => {
    if (municipioFinca) {
      void fetchCorregimientos(municipioFinca);
    }
  }, [municipioFinca]);

  // Sincronizar por defecto el municipio de la finca con el de residencia al iniciar
  useEffect(() => {
    if (municipioResidencia && !nombreFinca) {
      setMunicipioFinca(municipioResidencia);
    }
  }, [municipioResidencia, nombreFinca]);

  // Validaciones
  const validatePaso1 = (): boolean => {
    const errs: { [campo: string]: string } = {};
    const nombre = nombreCompleto.trim();
    if (nombre.length < 3 || nombre.length > 120) {
      errs.nombre_completo = 'Escribe tu nombre y apellido completos (mínimo 3 letras).';
    }
    if (!celular || celular.length !== 10 || !celular.startsWith('3')) {
      errs.celular = 'El celular debe tener 10 dígitos y empezar por el número 3.';
    }
    if (correo.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.trim())) {
      errs.correo = 'Escribe un correo electrónico válido o deja este campo vacío.';
    }
    const hasLetra = /[a-zA-Z]/.test(contrasena);
    const hasNumero = /[0-9]/.test(contrasena);
    if (contrasena.length < 8 || !hasLetra || !hasNumero) {
      errs.contrasena = 'La contraseña debe tener mínimo 8 caracteres, al menos una letra y un número.';
    }
    if (!municipioResidencia) {
      errs.municipio_residencia = 'Selecciona tu municipio de residencia.';
    }
    if (!aceptaPolitica) {
      errs.acepta_politica = 'Debes aceptar la política de datos para continuar.';
    }
    setErrorsPaso1(errs);
    return Object.keys(errs).length === 0;
  };

  const validatePaso2 = (): boolean => {
    const errs: { [campo: string]: string } = {};
    if (!nombreFinca.trim()) {
      errs.nombre = 'Escribe el nombre de tu finca o predio.';
    }
    if (!municipioFinca) {
      errs.municipio = 'Elige el municipio de tu finca.';
    }
    if (!corregimientoFinca) {
      errs.corregimiento = 'Selecciona el corregimiento de la finca.';
    }
    setErrorsPaso2(errs);
    return Object.keys(errs).length === 0;
  };

  const validatePaso3 = (): boolean => {
    const errs: { [campo: string]: string } = {};
    if (!nombreLote.trim()) {
      errs.nombre = 'Escribe un nombre para este lote (ej: Lote 1, La Vega).';
    }
    if (!poligonoCoords) {
      errs.poligono = 'Toca las esquinas de tu lote en el mapa o ingresa coordenadas para delimitarlo.';
    }
    if (tieneRiego === null) {
      errs.tiene_riego = 'Indica si tu lote tiene sistema de riego o agua lluvia.';
    }
    if (tieneRiego === true && !tipoRiego) {
      errs.tipo_riego = 'Selecciona el tipo de riego que utilizas.';
    }
    if (!cultivoAnterior) {
      errs.cultivo_anterior = 'Indica qué sembraste el último semestre o elige "Nada / lote nuevo".';
    }
    setErrorsPaso3(errs);
    return Object.keys(errs).length === 0;
  };

  const handleBackendErrorCatch = (err: unknown, paso: 1 | 2 | 3 | 4) => {
    const apiErr = (typeof err === 'object' && err !== null ? err : {}) as Partial<ErrorApi>;
    const codigo = apiErr.codigo || 'ERROR_DESCONOCIDO';
    const mensaje = apiErr.mensaje || 'Revisa tu conexión e inténtalo de nuevo.';
    const detalles = apiErr.detalles || [];

    if (codigo === 'USUARIO_CELULAR_DUPLICADO') {
      setCelularDuplicado(true);
      setErrorsPaso1((prev) => ({
        ...prev,
        celular: 'Ya existe una cuenta con este celular.'
      }));
      return;
    }
    if (codigo === 'USUARIO_CORREO_DUPLICADO') {
      setErrorsPaso1((prev) => ({
        ...prev,
        correo: 'Este correo ya está registrado en otra cuenta.'
      }));
      return;
    }
    if (codigo === 'CONSENTIMIENTO_REQUERIDO') {
      setErrorsPaso1((prev) => ({
        ...prev,
        acepta_politica: 'Debes autorizar el uso de datos para continuar.'
      }));
      return;
    }
    if (codigo === 'POLITICA_DESACTUALIZADA') {
      setAceptaPolitica(false);
      setErrorsPaso1((prev) => ({
        ...prev,
        acepta_politica: 'La política de privacidad cambió. Por favor léela y autorízala nuevamente.'
      }));
      void fetchPolitica();
      return;
    }

    if (detalles.length > 0) {
      const fieldMap: { [campo: string]: string } = {};
      detalles.forEach((d) => {
        fieldMap[d.campo] = d.mensaje;
      });
      if (paso === 1) setErrorsPaso1((prev) => ({ ...prev, ...fieldMap }));
      if (paso === 2) setErrorsPaso2((prev) => ({ ...prev, ...fieldMap }));
      if (paso === 3) setErrorsPaso3((prev) => ({ ...prev, ...fieldMap }));
      return;
    }

    setBackendError({ codigo, mensaje });
  };

  // Manejador del avance en el wizard
  const handleNext = async () => {
    setBackendError(null);
    setCelularDuplicado(false);

    if (currentStep === 1) {
      // Modo lectura si ya fue guardado
      if (usuarioId) {
        setCurrentStep(2);
        return;
      }

      if (!validatePaso1()) return;
      if (!politicaVigente) {
        setBackendError({
          codigo: 'ERROR_POLITICA',
          mensaje: 'No se pudo obtener la versión vigente de la política. Reintenta la carga.'
        });
        return;
      }

      setIsLoading(true);
      try {
        const resp = await registrarUsuario({
          nombre_completo: nombreCompleto.trim(),
          celular: celular.trim(),
          correo: correo.trim() || null,
          contrasena,
          municipio_residencia: municipioResidencia,
          acepta_politica: true,
          version_politica: politicaVigente.version
        });
        guardarTokens(resp.tokens);
        setUsuarioId(resp.usuario.id);
        setCurrentStep(2);
      } catch (err: unknown) {
        handleBackendErrorCatch(err, 1);
      } finally {
        setIsLoading(false);
      }
    } else if (currentStep === 2) {
      if (fincaId) {
        setCurrentStep(3);
        return;
      }

      if (!validatePaso2()) return;

      setIsLoading(true);
      try {
        const resp = await crearFinca({
          nombre: nombreFinca.trim(),
          municipio: municipioFinca,
          corregimiento: corregimientoFinca,
          vereda: veredaFinca.trim() || null
        });
        setFincaId(resp.id);
        setCurrentStep(3);
      } catch (err: unknown) {
        handleBackendErrorCatch(err, 2);
      } finally {
        setIsLoading(false);
      }
    } else if (currentStep === 3) {
      if (loteId) {
        setCurrentStep(4);
        return;
      }

      // Detener avance si falta fincaId previo
      if (!fincaId) {
        setBackendError({
          codigo: 'PASO_INCOMPLETO',
          mensaje: 'Falta información del paso anterior'
        });
        return;
      }

      if (!validatePaso3()) return;

      // Detener avance sin operadores !
      if (!poligonoCoords || tieneRiego === null) {
        setBackendError({
          codigo: 'PASO_INCOMPLETO',
          mensaje: 'Falta información del paso anterior'
        });
        return;
      }

      setIsLoading(true);
      try {
        const resp = await crearLote(fincaId, {
          nombre: nombreLote.trim(),
          poligono: poligonoCoords,
          tiene_riego: tieneRiego,
          tipo_riego: tieneRiego ? tipoRiego : null,
          cultivo_anterior: cultivoAnterior === 'ninguno' ? null : cultivoAnterior
        });
        setLoteId(resp.id);
        setCurrentStep(4);
      } catch (err: unknown) {
        handleBackendErrorCatch(err, 3);
      } finally {
        setIsLoading(false);
      }
    } else if (currentStep === 4) {
      // Detener avance si falta loteId previo
      if (!loteId) {
        setBackendError({
          codigo: 'PASO_INCOMPLETO',
          mensaje: 'Falta información del paso anterior'
        });
        return;
      }

      setIsLoading(true);
      try {
        await guardarPreferencias({
          orden: prioridadesOrden
        });
        const diag = await iniciarDiagnostico(loteId);
        onNavigate(`/lotes/${loteId}?tarea=${diag.tarea_id}`);
      } catch (err: unknown) {
        handleBackendErrorCatch(err, 4);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleBack = () => {
    setBackendError(null);
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as 1 | 2 | 3 | 4);
    }
  };

  const percentage = currentStep * 25;
  const paso1Bloqueado = Boolean(usuarioId);
  const paso2Bloqueado = Boolean(fincaId);
  const paso3Bloqueado = Boolean(loteId);

  return (
    <div className="min-h-screen bg-[#F7F3EA] text-[#14202B] flex flex-col justify-between font-sans">
      <StepperProgress
        currentStep={currentStep}
        totalSteps={4}
        stepLabels={STEP_LABELS}
        percentageCompleted={percentage}
      />

      <main className="flex-1 max-w-xl w-full mx-auto p-4 sm:p-6 flex flex-col justify-start">
        {backendError && (
          <ErrorCard
            mensaje={backendError.mensaje}
            codigo={backendError.codigo}
            onRetry={handleNext}
            retryLabel="Reintentar este paso"
          />
        )}

        {/* ===================== PASO 1 ===================== */}
        {currentStep === 1 && (
          <div className="space-y-5">
            {paso1Bloqueado && (
              <AvisoGuardado titulo="Ya guardamos estos datos" detalle="Tu usuario ya fue registrado en el sistema." />
            )}

            <div className="text-left">
              <h1 className="text-2xl sm:text-3xl font-black text-[#1F4D2B]">
                Comencemos con tus datos
              </h1>
              <p className="text-sm sm:text-base text-[#14202B]/80 mt-1">
                Para que recibas las recomendaciones climáticas y puedas ingresar fácilmente a tu cuenta.
              </p>
            </div>

            {/* Nombre y apellidos */}
            <div className="text-left">
              <label htmlFor="nombre-completo" className={etiquetaClase}>
                Nombre y apellidos <span className="text-[#D94F4F]">*</span>
              </label>
              <input
                id="nombre-completo"
                type="text"
                autoComplete="name"
                value={nombreCompleto}
                disabled={paso1Bloqueado}
                onChange={(e) => setNombreCompleto(e.target.value)}
                placeholder="Ej: Ernesto Ramírez"
                className={inputClase(errorsPaso1.nombre_completo, paso1Bloqueado)}
                aria-invalid={Boolean(errorsPaso1.nombre_completo)}
                aria-describedby={errorsPaso1.nombre_completo ? 'nombre-completo-error' : undefined}
              />
              <MensajeError id="nombre-completo-error" mensaje={errorsPaso1.nombre_completo} />
            </div>

            <PhoneInput
              value={celular}
              onChange={setCelular}
              error={errorsPaso1.celular}
              disabled={paso1Bloqueado}
              duplicateError={celularDuplicado}
              onNavigateLogin={() => onNavigate('/ingresar')}
            />

            {/* Correo (opcional) */}
            <div className="text-left">
              <label htmlFor="correo" className={etiquetaClase}>
                Correo electrónico <span className="text-sm font-semibold text-[#14202B]/60">(opcional)</span>
              </label>
              <input
                id="correo"
                type="email"
                autoComplete="email"
                inputMode="email"
                value={correo}
                disabled={paso1Bloqueado}
                onChange={(e) => setCorreo(e.target.value)}
                placeholder="Ej: ernesto@correo.com"
                className={inputClase(errorsPaso1.correo, paso1Bloqueado)}
                aria-invalid={Boolean(errorsPaso1.correo)}
                aria-describedby={errorsPaso1.correo ? 'correo-error' : undefined}
              />
              <MensajeError id="correo-error" mensaje={errorsPaso1.correo} />
            </div>

            {/* Contraseña */}
            <div className="text-left">
              <label htmlFor="contrasena" className={etiquetaClase}>
                Contraseña <span className="text-[#D94F4F]">*</span>
              </label>
              <div className="relative">
                <input
                  id="contrasena"
                  type={mostrarContrasena ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={paso1Bloqueado ? '••••••••' : contrasena}
                  disabled={paso1Bloqueado}
                  onChange={(e) => setContrasena(e.target.value)}
                  placeholder="Mínimo 8, con letras y números"
                  className={`${inputClase(errorsPaso1.contrasena, paso1Bloqueado)} pr-[72px]`}
                  aria-invalid={Boolean(errorsPaso1.contrasena)}
                  aria-describedby={errorsPaso1.contrasena ? 'contrasena-error' : 'contrasena-helper'}
                />
                {!paso1Bloqueado && (
                  <button
                    type="button"
                    onClick={() => setMostrarContrasena((v) => !v)}
                    aria-pressed={mostrarContrasena}
                    aria-label={mostrarContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    className="absolute right-0 top-0 h-14 min-w-[56px] px-3 text-sm font-bold text-[#1F4D2B] underline"
                  >
                    {mostrarContrasena ? 'Ocultar' : 'Ver'}
                  </button>
                )}
              </div>
              {errorsPaso1.contrasena ? (
                <MensajeError id="contrasena-error" mensaje={errorsPaso1.contrasena} />
              ) : (
                <span id="contrasena-helper" className="text-sm text-[#14202B]/70 mt-1.5 block">
                  Usa una que recuerdes fácil, por ejemplo el nombre de tu finca y un año.
                </span>
              )}
            </div>

            <SelectField
              id="municipio-residencia"
              label="Municipio donde vives"
              value={municipioResidencia}
              onChange={setMunicipioResidencia}
              options={municipiosOptions}
              isLoading={loadingMunicipios}
              disabled={paso1Bloqueado}
              error={errorsPaso1.municipio_residencia ?? errorCargaMunicipios ?? undefined}
              onRetry={errorCargaMunicipios ? () => void fetchMunicipios() : undefined}
              required
            />

            <ConsentCard
              checked={aceptaPolitica}
              onChange={setAceptaPolitica}
              error={errorsPaso1.acepta_politica}
              versionPolitica={politicaVigente?.version}
              urlTexto={politicaVigente?.url_texto}
              isLoading={loadingPolitica}
              loadError={errorCargaPolitica}
              onRetryLoad={() => void fetchPolitica()}
              disabled={paso1Bloqueado}
            />
          </div>
        )}

        {/* ===================== PASO 2 ===================== */}
        {currentStep === 2 && (
          <div className="space-y-5">
            {paso2Bloqueado && (
              <AvisoGuardado titulo="Tu finca ya está guardada" detalle="Puedes seguir al siguiente paso." />
            )}

            <div className="text-left">
              <h1 className="text-2xl sm:text-3xl font-black text-[#1F4D2B]">Cuéntanos de tu finca</h1>
              <p className="text-sm sm:text-base text-[#14202B]/80 mt-1">
                Con la ubicación buscamos los datos de clima y suelo de tu zona.
              </p>
            </div>

            <div className="text-left">
              <label htmlFor="nombre-finca" className={etiquetaClase}>
                Nombre de la finca <span className="text-[#D94F4F]">*</span>
              </label>
              <input
                id="nombre-finca"
                type="text"
                value={nombreFinca}
                disabled={paso2Bloqueado}
                onChange={(e) => setNombreFinca(e.target.value)}
                placeholder="Ej: La Esperanza"
                className={inputClase(errorsPaso2.nombre, paso2Bloqueado)}
                aria-invalid={Boolean(errorsPaso2.nombre)}
                aria-describedby={errorsPaso2.nombre ? 'nombre-finca-error' : undefined}
              />
              <MensajeError id="nombre-finca-error" mensaje={errorsPaso2.nombre} />
            </div>

            <SelectField
              id="municipio-finca"
              label="Municipio de la finca"
              value={municipioFinca}
              onChange={setMunicipioFinca}
              options={municipiosOptions}
              isLoading={loadingMunicipios}
              disabled={paso2Bloqueado}
              error={errorsPaso2.municipio ?? errorCargaMunicipios ?? undefined}
              onRetry={errorCargaMunicipios ? () => void fetchMunicipios() : undefined}
              required
            />

            <SelectField
              id="corregimiento-finca"
              label="Corregimiento"
              value={corregimientoFinca}
              onChange={setCorregimientoFinca}
              options={corregimientosOptions}
              placeholder="Selecciona el corregimiento"
              isLoading={loadingCorregimientos}
              disabled={paso2Bloqueado || !municipioFinca}
              error={errorsPaso2.corregimiento ?? errorCargaCorregimientos ?? undefined}
              onRetry={errorCargaCorregimientos ? () => void fetchCorregimientos(municipioFinca) : undefined}
              required
            />

            <div className="text-left">
              <label htmlFor="vereda-finca" className={etiquetaClase}>
                Vereda <span className="text-sm font-semibold text-[#14202B]/60">(opcional)</span>
              </label>
              <input
                id="vereda-finca"
                type="text"
                value={veredaFinca}
                disabled={paso2Bloqueado}
                onChange={(e) => setVeredaFinca(e.target.value)}
                placeholder="Ej: El Triunfo"
                className={inputClase(errorsPaso2.vereda, paso2Bloqueado)}
              />
              <MensajeError id="vereda-finca-error" mensaje={errorsPaso2.vereda} />
            </div>
          </div>
        )}

        {/* ===================== PASO 3 ===================== */}
        {currentStep === 3 && (
          <div className="space-y-6">
            {paso3Bloqueado && (
              <AvisoGuardado titulo="Tu lote ya está guardado" detalle="Puedes seguir al último paso." />
            )}

            <div className="text-left">
              <h1 className="text-2xl sm:text-3xl font-black text-[#1F4D2B]">Marca tu lote</h1>
              <p className="text-sm sm:text-base text-[#14202B]/80 mt-1">
                Así medimos con satélites de la NASA la humedad y el verdor de ese terreno exacto.
              </p>
            </div>

            <div className="text-left">
              <label htmlFor="nombre-lote" className={etiquetaClase}>
                Nombre del lote <span className="text-[#D94F4F]">*</span>
              </label>
              <input
                id="nombre-lote"
                type="text"
                value={nombreLote}
                disabled={paso3Bloqueado}
                onChange={(e) => setNombreLote(e.target.value)}
                placeholder="Ej: Lote 1, La Vega"
                className={inputClase(errorsPaso3.nombre, paso3Bloqueado)}
                aria-invalid={Boolean(errorsPaso3.nombre)}
                aria-describedby={errorsPaso3.nombre ? 'nombre-lote-error' : undefined}
              />
              <MensajeError id="nombre-lote-error" mensaje={errorsPaso3.nombre} />
            </div>

            <MapDrawer
              poligono={poligonoCoords}
              area_ha={areaLoteHa}
              modo={mapModo}
              onModoChange={setMapModo}
              onPolygonChange={setPoligonoCoords}
              error={errorsPaso3.poligono}
              disabled={paso3Bloqueado}
            />

            {/* ¿Tiene riego? */}
            <fieldset className="text-left border-none p-0 m-0" disabled={paso3Bloqueado}>
              <legend className={etiquetaClase}>
                ¿El lote tiene riego? <span className="text-[#D94F4F]">*</span>
              </legend>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { valor: true, texto: 'Sí, tiene riego' },
                  { valor: false, texto: 'No, solo lluvia' }
                ].map((opcion) => {
                  const activo = tieneRiego === opcion.valor;
                  return (
                    <button
                      key={opcion.texto}
                      type="button"
                      aria-pressed={activo}
                      onClick={() => {
                        setTieneRiego(opcion.valor);
                        if (!opcion.valor) setTipoRiego(null);
                      }}
                      className={`min-h-[56px] rounded-xl border-2 font-bold text-base transition-all ${
                        activo
                          ? 'border-[#1F4D2B] bg-[#1F4D2B] text-white'
                          : 'border-[#D2C8B5] bg-white text-[#14202B] hover:border-[#1F4D2B]/60'
                      }`}
                    >
                      {opcion.texto}
                    </button>
                  );
                })}
              </div>
              <MensajeError id="tiene-riego-error" mensaje={errorsPaso3.tiene_riego} />
            </fieldset>

            {tieneRiego === true && (
              <fieldset className="text-left border-none p-0 m-0" disabled={paso3Bloqueado}>
                <legend className={etiquetaClase}>
                  ¿Qué tipo de riego? <span className="text-[#D94F4F]">*</span>
                </legend>
                <div className="grid grid-cols-3 gap-2">
                  {RIEGO_OPTIONS.map((opcion) => {
                    const activo = tipoRiego === opcion.id;
                    return (
                      <button
                        key={opcion.id}
                        type="button"
                        aria-pressed={activo}
                        onClick={() => setTipoRiego(opcion.id)}
                        className={`min-h-[56px] px-2 rounded-xl border-2 font-bold text-sm sm:text-base transition-all ${
                          activo
                            ? 'border-[#1F4D2B] bg-[#1F4D2B]/10 text-[#1F4D2B] ring-1 ring-[#1F4D2B]'
                            : 'border-[#D2C8B5] bg-white text-[#14202B] hover:border-[#1F4D2B]/60'
                        }`}
                      >
                        {opcion.nombre}
                      </button>
                    );
                  })}
                </div>
                <MensajeError id="tipo-riego-error" mensaje={errorsPaso3.tipo_riego} />
              </fieldset>
            )}

            <CropChipSelector
              selectedCrop={cultivoAnterior}
              onChange={setCultivoAnterior}
              options={CROP_OPTIONS}
              error={errorsPaso3.cultivo_anterior}
              disabled={paso3Bloqueado}
            />
          </div>
        )}

        {/* ===================== PASO 4 ===================== */}
        {currentStep === 4 && (
          <div className="space-y-5">
            <div className="text-left">
              <h1 className="text-2xl sm:text-3xl font-black text-[#1F4D2B]">¿Qué es lo más importante para ti?</h1>
              <p className="text-sm sm:text-base text-[#14202B]/80 mt-1">
                Con este orden ajustamos la recomendación de rotación para tu lote.
              </p>
            </div>

            <PriorityRanker orden={prioridadesOrden} onChange={setPrioridadesOrden} disabled={isLoading} />
          </div>
        )}
      </main>

      {/* Barra de navegación inferior */}
      <footer className="sticky bottom-0 bg-[#F7F3EA]/95 backdrop-blur border-t-2 border-[#E8E1D3]">
        <div className="max-w-xl mx-auto px-4 sm:px-6 py-3 flex gap-3">
          {currentStep > 1 && (
            <button
              type="button"
              onClick={handleBack}
              disabled={isLoading}
              className="min-h-[56px] px-5 rounded-xl border-2 border-[#1F4D2B] text-[#1F4D2B] font-bold text-base bg-white disabled:opacity-50"
            >
              Atrás
            </button>
          )}
          <button
            type="button"
            onClick={() => void handleNext()}
            disabled={isLoading}
            aria-busy={isLoading}
            className="flex-1 min-h-[56px] rounded-xl bg-[#1F4D2B] hover:bg-[#16381F] text-white font-extrabold text-lg disabled:opacity-70 flex items-center justify-center gap-2"
          >
            {isLoading && (
              <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            )}
            {isLoading ? 'Guardando...' : currentStep === 4 ? 'Ver mi diagnóstico' : 'Continuar'}
          </button>
        </div>
      </footer>
    </div>
  );
};
