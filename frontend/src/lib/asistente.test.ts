import { describe, expect, it } from 'vitest';
import { estaCercaDelFinal } from '../hooks/useAutoScroll';
import { duracionEnPalabras, formatearDuracion, horaMensaje, ondaDecorativa, preguntasSugeridas, tipoAudioSoportado } from './asistente';

describe('preguntas sugeridas', () => {
  it('las cuatro de siempre', () => {
    expect(preguntasSugeridas(null)).toEqual([
      '¿Debo regar hoy?',
      '¿Qué siembro el próximo semestre?',
      '¿Cómo está mi suelo?',
      '¿Cómo viene la lluvia esta semana?'
    ]);
  });

  it('si viene del Plan con un cultivo, esa pregunta va primero', () => {
    const p = preguntasSugeridas('Maíz');
    expect(p[0]).toBe('¿Por qué me recomiendan maíz?');
    expect(p).toHaveLength(5);
  });
});

describe('voz', () => {
  it('duración en minutos y segundos, y en palabras', () => {
    expect(formatearDuracion(4)).toBe('0:04');
    expect(formatearDuracion(75)).toBe('1:15');
    expect(formatearDuracion(60)).toBe('1:00');
    expect(duracionEnPalabras(18)).toBe('18 segundos');
    expect(duracionEnPalabras(1)).toBe('1 segundo');
    expect(duracionEnPalabras(75)).toBe('1 minuto y 15 segundos');
    expect(duracionEnPalabras(120)).toBe('2 minutos');
  });

  it('elige el primer formato de audio que el navegador sabe grabar', () => {
    expect(tipoAudioSoportado((t) => t.startsWith('audio/webm'))).toBe('audio/webm;codecs=opus');
    expect(tipoAudioSoportado((t) => t === 'audio/mp4')).toBe('audio/mp4');
    expect(tipoAudioSoportado(() => false)).toBe('');
  });

  it('la onda decorativa es estable para el mismo mensaje y va de 0,2 a 1', () => {
    const a = ondaDecorativa('m-1');
    expect(ondaDecorativa('m-1')).toEqual(a);
    expect(ondaDecorativa('m-2')).not.toEqual(a);
    expect(a.every((n) => n >= 0.2 && n <= 1)).toBe(true);
  });
});

describe('hora de los mensajes', () => {
  it('solo la hora si es de hoy; día y hora si es de otro día', () => {
    const ahora = new Date(2026, 9, 20, 15, 0);
    expect(horaMensaje(new Date(2026, 9, 20, 7, 14).toISOString(), ahora)).toMatch(/^7:14 a\. ?m\.$/);
    expect(horaMensaje(new Date(2026, 9, 12, 7, 14).toISOString(), ahora)).toMatch(/12.*oct.*7:14/);
  });
});

describe('desplazamiento automático', () => {
  it('cuenta como "abajo" si está a menos de 120 px del final', () => {
    expect(estaCercaDelFinal({ scrollHeight: 1000, scrollTop: 500, clientHeight: 400 })).toBe(true);
    expect(estaCercaDelFinal({ scrollHeight: 1000, scrollTop: 200, clientHeight: 400 })).toBe(false);
  });
});
