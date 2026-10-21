// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { LOTES_DEMO, lluviasDemo, planDemo, tareaPlanDemo, DURACION_TAREA_MS } from '../api/mocks/plan';
import * as servicios from '../api/services';
import type { ErrorApi } from '../api/tipos';
import { guardarPlan } from '../lib/planGuardado';
import { estadoPorError, usePlanLote } from './usePlanLote';

const [LOTE] = LOTES_DEMO;
const error = (codigo: string, extra: Partial<ErrorApi> = {}): ErrorApi => ({ codigo, mensaje: codigo, ...extra });

beforeEach(() => {
  localStorage.clear();
  vi.spyOn(servicios, 'listarMisLotes').mockResolvedValue(LOTES_DEMO);
  vi.spyOn(servicios, 'obtenerLluviasEsperadas').mockResolvedValue(lluviasDemo());
});
afterEach(() => vi.restoreAllMocks());

describe('estadoPorError', () => {
  it('traduce los errores del backend a estados de la pantalla', () => {
    expect(estadoPorError(error('PLAN_NO_DISPONIBLE'), LOTE.id)).toEqual({ tipo: 'sin_plan' });
    expect(estadoPorError(error('DIAGNOSTICO_NO_DISPONIBLE'), LOTE.id)).toEqual({ tipo: 'sin_diagnostico' });
    expect(estadoPorError(error('PLAN_EN_CALCULO', { detalles: [{ campo: 'tarea_id', mensaje: 't-9' }] }), LOTE.id)).toEqual({
      tipo: 'calculando',
      tareaId: 't-9',
      tarea: null
    });
    expect(estadoPorError(error('HTTP_500'), LOTE.id).tipo).toBe('error');
  });

  it('sin conexión muestra el último plan guardado si lo hay', () => {
    expect(estadoPorError(error('RED_SIN_CONEXION'), LOTE.id).tipo).toBe('error');
    guardarPlan(LOTE.id, { plan: planDemo(LOTE.id), lluvias: null });
    expect(estadoPorError(error('RED_SIN_CONEXION'), LOTE.id)).toMatchObject({ tipo: 'listo', desdeGuardado: true });
  });
});

describe('usePlanLote', () => {
  it('carga los lotes, elige el primero si el pedido no existe, y guarda el plan', async () => {
    const ultimo = vi.spyOn(servicios, 'obtenerUltimoPlan').mockResolvedValue(planDemo(LOTE.id));
    const { result } = renderHook(() => usePlanLote('no-existe'));
    expect(result.current.estado.tipo).toBe('cargando');
    await waitFor(() => expect(result.current.estado.tipo).toBe('listo'));
    expect(result.current.loteId).toBe(LOTE.id);
    expect(ultimo).toHaveBeenCalledWith(LOTE.id);
    expect(localStorage.getItem(`surco.plan.${LOTE.id}`)).not.toBeNull();
  });

  it('sin plan: armarlo muestra la tarea y al terminar carga el plan nuevo', async () => {
    vi.spyOn(servicios, 'obtenerUltimoPlan').mockRejectedValue(error('PLAN_NO_DISPONIBLE'));
    vi.spyOn(servicios, 'generarPlan').mockResolvedValue({ tarea_id: 't-1' });
    vi.spyOn(servicios, 'obtenerTareaPlan').mockResolvedValue(tareaPlanDemo(LOTE, DURACION_TAREA_MS));
    const obtenerPlan = vi.spyOn(servicios, 'obtenerPlan').mockResolvedValue(planDemo(LOTE.id));

    const { result } = renderHook(() => usePlanLote(LOTE.id));
    await waitFor(() => expect(result.current.estado.tipo).toBe('sin_plan'));

    act(() => result.current.armarPlan());
    await waitFor(() => {
      const e = result.current.estado;
      expect(e.tipo === 'calculando' && e.tarea?.estado).toBe('lista');
    });

    act(() => result.current.verPlanCalculado());
    await waitFor(() => expect(result.current.estado.tipo).toBe('listo'));
    expect(obtenerPlan).toHaveBeenCalledWith('plan-demo');
  });

  it('sin lotes muestra el estado para marcar el primero', async () => {
    vi.mocked(servicios.listarMisLotes).mockResolvedValue([]);
    const { result } = renderHook(() => usePlanLote(null));
    await waitFor(() => expect(result.current.estado.tipo).toBe('sin_lotes'));
  });

  it('un error al armar el plan se muestra sin perder la tarjeta', async () => {
    vi.spyOn(servicios, 'obtenerUltimoPlan').mockRejectedValue(error('PLAN_NO_DISPONIBLE'));
    vi.spyOn(servicios, 'generarPlan').mockRejectedValue(error('HTTP_500', { mensaje: 'Falló' }));
    const { result } = renderHook(() => usePlanLote(LOTE.id));
    await waitFor(() => expect(result.current.estado.tipo).toBe('sin_plan'));
    act(() => result.current.armarPlan());
    await waitFor(() => expect(result.current.errorArmar).toBe('Falló'));
    expect(result.current.estado.tipo).toBe('sin_plan');
  });
});
