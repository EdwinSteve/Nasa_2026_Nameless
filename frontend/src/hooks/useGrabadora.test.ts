// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MAX_GRABACION_S } from '../lib/asistente';
import { useGrabadora } from './useGrabadora';

/** MediaRecorder de mentira: entrega un trozo de audio al detenerse. */
class GrabadoraFalsa {
  static isTypeSupported = (t: string) => t === 'audio/webm;codecs=opus';
  state: 'inactive' | 'recording' = 'inactive';
  mimeType: string;
  ondataavailable: ((ev: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  constructor(_stream: unknown, opciones?: { mimeType?: string }) {
    this.mimeType = opciones?.mimeType ?? '';
  }
  start() {
    this.state = 'recording';
  }
  stop() {
    this.state = 'inactive';
    this.ondataavailable?.({ data: new Blob(['audio'], { type: this.mimeType }) });
    this.onstop?.();
  }
}

const pista = { stop: vi.fn() };
const flujo = { getTracks: () => [pista] };
let getUserMedia: ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('MediaRecorder', GrabadoraFalsa);
  getUserMedia = vi.fn().mockResolvedValue(flujo);
  Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia }, configurable: true });
  pista.stop.mockClear();
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('useGrabadora', () => {
  it('no pide el micrófono hasta que se empieza a grabar', () => {
    renderHook(() => useGrabadora(vi.fn()));
    expect(getUserMedia).not.toHaveBeenCalled();
  });

  it('graba, cuenta el tiempo y al terminar entrega el audio y apaga el micrófono', async () => {
    const onListo = vi.fn();
    const { result } = renderHook(() => useGrabadora(onListo));
    await act(() => result.current.iniciar());
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(result.current.estado).toBe('grabando');

    act(() => vi.advanceTimersByTime(3000));
    expect(result.current.segundos).toBeCloseTo(3, 0);
    act(() => result.current.terminar());

    expect(onListo).toHaveBeenCalledTimes(1);
    const [audio, duracion] = onListo.mock.calls[0] as [Blob, number];
    expect(audio.type).toBe('audio/webm;codecs=opus');
    expect(duracion).toBeCloseTo(3, 0);
    expect(pista.stop).toHaveBeenCalled();
    expect(result.current.estado).toBe('inactivo');
  });

  it('cancelar descarta el audio', async () => {
    const onListo = vi.fn();
    const { result } = renderHook(() => useGrabadora(onListo));
    await act(() => result.current.iniciar());
    act(() => vi.advanceTimersByTime(2000));
    act(() => result.current.cancelar());
    expect(onListo).not.toHaveBeenCalled();
    expect(pista.stop).toHaveBeenCalled();
  });

  it('corta solo a los 60 segundos', async () => {
    const onListo = vi.fn();
    const { result } = renderHook(() => useGrabadora(onListo));
    await act(() => result.current.iniciar());
    act(() => vi.advanceTimersByTime(MAX_GRABACION_S * 1000 + 400));
    expect(onListo).toHaveBeenCalledTimes(1);
    expect(onListo.mock.calls[0][1]).toBe(MAX_GRABACION_S);
  });

  it('un toque muy corto no se envía', async () => {
    const onListo = vi.fn();
    const { result } = renderHook(() => useGrabadora(onListo));
    await act(() => result.current.iniciar());
    act(() => vi.advanceTimersByTime(200));
    act(() => result.current.terminar());
    expect(onListo).not.toHaveBeenCalled();
  });

  it('si el productor niega el permiso queda "sin permiso" y puede volver a intentar', async () => {
    getUserMedia.mockRejectedValueOnce(new DOMException('no', 'NotAllowedError'));
    const { result } = renderHook(() => useGrabadora(vi.fn()));
    await act(() => result.current.iniciar());
    expect(result.current.estado).toBe('sin_permiso');
    await act(() => result.current.iniciar());
    expect(result.current.estado).toBe('grabando');
  });

  it('sin micrófono o sin MediaRecorder lo dice', async () => {
    getUserMedia.mockRejectedValueOnce(new DOMException('no', 'NotFoundError'));
    const { result } = renderHook(() => useGrabadora(vi.fn()));
    await act(() => result.current.iniciar());
    expect(result.current.estado).toBe('sin_microfono');

    vi.stubGlobal('MediaRecorder', undefined);
    act(() => result.current.descartarAviso());
    await act(() => result.current.iniciar());
    expect(result.current.estado).toBe('no_soportado');
  });
});
