// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { resumenDemo } from '../api/mocks/inicio';
import * as servicios from '../api/services';
import { clasificarResumen, useResumenInicio } from './useResumenInicio';

afterEach(() => vi.restoreAllMocks());

describe('clasificarResumen', () => {
  it('usuario con historia y riego pendiente', () => {
    expect(clasificarResumen(resumenDemo('historia'))).toEqual({
      esNuevo: false, sinLote: false, sinRecomendacion: false, puedeRegistrarRiego: true
    });
  });

  it('usuario nuevo y sin lote', () => {
    expect(clasificarResumen(resumenDemo('nuevo'))).toMatchObject({ esNuevo: true, sinLote: false, sinRecomendacion: true });
    expect(clasificarResumen(resumenDemo('sin-lote'))).toMatchObject({ esNuevo: true, sinLote: true, puedeRegistrarRiego: false });
  });

  it('una recomendación de tipo "ninguna" cuenta como sin recomendación', () => {
    const r = resumenDemo('historia');
    r.recomendacion_hoy = { ...r.recomendacion_hoy, tipo: 'ninguna', mensaje: '', detalle_porque: '', procedencia: { fuente: 'x', fecha: null } };
    expect(clasificarResumen(r)).toMatchObject({ sinRecomendacion: true, puedeRegistrarRiego: false });
  });
});

describe('useResumenInicio', () => {
  it('pasa de cargando a listo con los datos', async () => {
    vi.spyOn(servicios, 'obtenerResumenInicio').mockResolvedValue(resumenDemo('historia'));
    const { result } = renderHook(() => useResumenInicio());

    expect(result.current.estado).toBe('cargando');
    await waitFor(() => expect(result.current.estado).toBe('listo'));
    expect(result.current.datos?.usuario.nombre).toBe('Ernesto');
  });

  it('muestra el error y reintenta', async () => {
    const espia = vi
      .spyOn(servicios, 'obtenerResumenInicio')
      .mockRejectedValueOnce({ codigo: 'HTTP_500', mensaje: 'Ocurrió un error inesperado.' })
      .mockResolvedValueOnce(resumenDemo('nuevo'));
    const { result } = renderHook(() => useResumenInicio());

    await waitFor(() => expect(result.current.estado).toBe('error'));
    expect(result.current.error?.codigo).toBe('HTTP_500');
    act(() => result.current.reintentar());
    await waitFor(() => expect(result.current.estado).toBe('listo'));
    expect(espia).toHaveBeenCalledTimes(2);
  });

  it('detecta cuando el navegador se queda sin conexión', async () => {
    vi.spyOn(servicios, 'obtenerResumenInicio').mockResolvedValue(resumenDemo('historia'));
    const enLinea = vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    const { result } = renderHook(() => useResumenInicio());
    expect(result.current.sinConexion).toBe(false);

    enLinea.mockReturnValue(false);
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    expect(result.current.sinConexion).toBe(true);
  });
});
