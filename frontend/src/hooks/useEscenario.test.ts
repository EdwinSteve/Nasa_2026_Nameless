// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as servicios from '../api/services';
import { ESPERA_ESCENARIO_MS, useEscenario } from './useEscenario';

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('useEscenario', () => {
  it('con el clima de siempre muestra la frecuencia base sin llamar al servicio', () => {
    const simular = vi.spyOn(servicios, 'simularEscenario');
    const { result } = renderHook(() => useEscenario('p', 'maiz', 8));
    expect(result.current.frecuencia).toBe(8);
    act(() => vi.advanceTimersByTime(1000));
    expect(simular).not.toHaveBeenCalled();
  });

  it('espera 400 ms sin cambios y llama una sola vez con los últimos valores', async () => {
    const simular = vi.spyOn(servicios, 'simularEscenario').mockResolvedValue({ frecuencia_exito: 5 });
    const { result } = renderHook(() => useEscenario('p', 'maiz', 8));

    act(() => result.current.setLluvia(-10));
    act(() => vi.advanceTimersByTime(200));
    act(() => result.current.setLluvia(-20));
    act(() => result.current.setTemperatura(2));
    expect(result.current.calculando).toBe(true);
    act(() => vi.advanceTimersByTime(ESPERA_ESCENARIO_MS - 1));
    expect(simular).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(1);
      await Promise.resolve();
    });
    expect(simular).toHaveBeenCalledTimes(1);
    expect(simular).toHaveBeenCalledWith('p', 'maiz', -20, 2);
    expect(result.current.frecuencia).toBe(5);
    expect(result.current.calculando).toBe(false);
  });

  it('descarta la respuesta de un valor viejo si el productor ya volvió al clima de siempre', async () => {
    let responder: (v: { frecuencia_exito: number }) => void = () => undefined;
    vi.spyOn(servicios, 'simularEscenario').mockImplementation(() => new Promise((r) => (responder = r)));
    const { result } = renderHook(() => useEscenario('p', 'maiz', 8));

    act(() => result.current.setLluvia(-40));
    act(() => vi.advanceTimersByTime(ESPERA_ESCENARIO_MS));
    act(() => result.current.setLluvia(0));
    await act(async () => {
      responder({ frecuencia_exito: 2 });
      await Promise.resolve();
    });
    expect(result.current.frecuencia).toBe(8);
  });
});
