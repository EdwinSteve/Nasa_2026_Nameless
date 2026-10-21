// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { conversacionDemo, respuestaDemo } from '../api/mocks/asistente';
import * as servicios from '../api/services';
import { useConversacion } from './useConversacion';

const LOTE = 'lote-demo-historia';

beforeEach(() => {
  vi.spyOn(servicios, 'obtenerConversacion').mockResolvedValue(conversacionDemo('nuevo', LOTE));
});
afterEach(() => vi.restoreAllMocks());

describe('useConversacion', () => {
  it('carga la conversación con el nombre del usuario', async () => {
    const { result } = renderHook(() => useConversacion(LOTE));
    expect(result.current.estado).toBe('cargando');
    await waitFor(() => expect(result.current.estado).toBe('listo'));
    expect(result.current.nombre).toBe('Ernesto');
    expect(result.current.mensajes).toEqual([]);
  });

  it('el mensaje del productor aparece de una vez, luego "pensando" y la respuesta', async () => {
    let responder: (v: ReturnType<typeof respuestaDemo>) => void = () => undefined;
    vi.spyOn(servicios, 'enviarMensaje').mockImplementation(() => new Promise((r) => (responder = r)));
    const { result } = renderHook(() => useConversacion(LOTE));
    await waitFor(() => expect(result.current.estado).toBe('listo'));

    act(() => result.current.enviarTexto('  ¿Debo regar hoy?  '));
    expect(result.current.mensajes).toHaveLength(1);
    expect(result.current.mensajes[0]).toMatchObject({ rol: 'productor', texto: '¿Debo regar hoy?', envio: 'enviando' });
    expect(result.current.pensando).toBe(true);

    await act(async () => responder(respuestaDemo('¿Debo regar hoy?', LOTE)));
    expect(result.current.pensando).toBe(false);
    expect(result.current.mensajes.map((m) => m.rol)).toEqual(['productor', 'asistente']);
    expect(result.current.mensajes[0].envio).toBeUndefined();
  });

  it('si falla el envío queda "No se envió" y se puede reintentar', async () => {
    const enviar = vi
      .spyOn(servicios, 'enviarMensaje')
      .mockRejectedValueOnce({ codigo: 'HTTP_503', mensaje: 'Falló' })
      .mockResolvedValueOnce(respuestaDemo('¿Cómo está mi suelo?', LOTE));
    const { result } = renderHook(() => useConversacion(LOTE));
    await waitFor(() => expect(result.current.estado).toBe('listo'));

    act(() => result.current.enviarTexto('¿Cómo está mi suelo?'));
    await waitFor(() => expect(result.current.mensajes[0].envio).toBe('fallido'));

    act(() => result.current.reintentarEnvio(result.current.mensajes[0].id));
    await waitFor(() => expect(result.current.mensajes).toHaveLength(2));
    expect(enviar).toHaveBeenCalledTimes(2);
    expect(enviar).toHaveBeenLastCalledWith(LOTE, '¿Cómo está mi suelo?', null);
  });

  it('una nota de voz se transcribe, se ve la transcripción y se envía con su duración', async () => {
    vi.spyOn(servicios, 'transcribirAudio').mockResolvedValue({ texto: '¿Será que riego el maíz esta semana?' });
    const enviar = vi.spyOn(servicios, 'enviarMensaje').mockResolvedValue(respuestaDemo('riego', LOTE));
    const { result } = renderHook(() => useConversacion(LOTE));
    await waitFor(() => expect(result.current.estado).toBe('listo'));

    act(() => result.current.enviarAudio(new Blob(['x'], { type: 'audio/webm' }), 4.4));
    expect(result.current.mensajes[0]).toMatchObject({ envio: 'transcribiendo', audio_duracion_s: 4, texto: '' });
    await waitFor(() => expect(result.current.mensajes).toHaveLength(2));
    expect(result.current.mensajes[0].texto).toBe('¿Será que riego el maíz esta semana?');
    expect(enviar).toHaveBeenCalledWith(LOTE, '¿Será que riego el maíz esta semana?', 4);
  });

  it('si la transcripción falla, al reintentar vuelve a transcribir el mismo audio', async () => {
    const transcribir = vi
      .spyOn(servicios, 'transcribirAudio')
      .mockRejectedValueOnce({ codigo: 'HTTP_500', mensaje: 'x' })
      .mockResolvedValueOnce({ texto: 'hola' });
    vi.spyOn(servicios, 'enviarMensaje').mockResolvedValue(respuestaDemo('hola', LOTE));
    const { result } = renderHook(() => useConversacion(LOTE));
    await waitFor(() => expect(result.current.estado).toBe('listo'));

    const audio = new Blob(['x']);
    act(() => result.current.enviarAudio(audio, 3));
    await waitFor(() => expect(result.current.mensajes[0].envio).toBe('fallido'));
    act(() => result.current.reintentarEnvio(result.current.mensajes[0].id));
    await waitFor(() => expect(result.current.mensajes).toHaveLength(2));
    expect(transcribir).toHaveBeenNthCalledWith(2, audio);
  });

  it('la valoración se marca de una vez y se deshace si falla', async () => {
    vi.mocked(servicios.obtenerConversacion).mockResolvedValue(conversacionDemo('con-historia', LOTE));
    const valorar = vi.spyOn(servicios, 'valorarMensaje').mockRejectedValue({ codigo: 'HTTP_500', mensaje: 'x' });
    const { result } = renderHook(() => useConversacion(LOTE));
    await waitFor(() => expect(result.current.estado).toBe('listo'));

    act(() => result.current.valorar('demo-2', true));
    expect(result.current.mensajes[1].valoracion).toBe(true);
    await waitFor(() => expect(result.current.mensajes[1].valoracion).toBeUndefined());
    expect(valorar).toHaveBeenCalledWith('demo-2', true);
  });
});
