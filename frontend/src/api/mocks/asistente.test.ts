import { describe, expect, it } from 'vitest';
import { conversacionDemo, PREGUNTA_VOZ_DEMO, respuestaDemo, resumenLoteDemo } from './asistente';
import { LOTES_DEMO } from './plan';

const LOTE = LOTES_DEMO[0].id;
const HOY = new Date(2026, 9, 20, 9);

describe('mock del Asistente SURCO', () => {
  it('la conversación de ejemplo es la nota de voz sobre riego y su respuesta, coherente con Inicio', () => {
    const c = conversacionDemo('con-historia', LOTE, HOY);
    expect(c.usuario.nombre).toBe('Ernesto');
    const [pregunta, respuesta] = c.mensajes;
    expect(pregunta).toMatchObject({ rol: 'productor', texto: PREGUNTA_VOZ_DEMO });
    expect(pregunta.audio_duracion_s).toBeGreaterThan(0);
    expect(respuesta.texto).toBe(
      'Sí, Ernesto. La tierra de su lote La Vega está seca para un maíz en floración. Riegue esta semana unos 450 m³ por hectárea.'
    );
    expect(respuesta.tarjetas.map((t) => `${t.etiqueta}: ${t.valor} · ${t.procedencia.fuente}`)).toEqual([
      'Humedad de la tierra: Baja · NASA SMAP',
      'Lluvia de los últimos 7 días: 3 · NASA POWER'
    ]);
    expect(respuesta.enlaces[0].texto).toBe('Ver en mi lote');
  });

  it('la primera vez no hay mensajes', () => {
    expect(conversacionDemo('nuevo', LOTE, HOY).mensajes).toEqual([]);
  });

  it('responde según el tema de las preguntas sugeridas', () => {
    expect(respuestaDemo('¿Debo regar hoy?', LOTE).texto).toContain('Riegue');
    expect(respuestaDemo('¿Qué siembro el próximo semestre?', LOTE).enlaces[0].texto).toBe('Ver mi plan');
    expect(respuestaDemo('¿Cómo está mi suelo?', LOTE).tarjetas[0].etiqueta).toBe('Salud del suelo');
    expect(respuestaDemo('¿Cómo viene la lluvia esta semana?', LOTE).tarjetas[0].etiqueta).toContain('Lluvia');
  });

  it('"¿Por qué me recomiendan maíz?" responde con las razones del plan', () => {
    const r = respuestaDemo('¿Por qué me recomiendan maíz?', LOTE);
    expect(r.texto).toMatch(/^Le recomendamos maíz porque/);
    expect(r.tarjetas[0].valor).toBe('8 de cada 10');
  });

  it('no recomienda abonos, agroquímicos ni da precios: remite al técnico', () => {
    for (const p of ['¿Qué abono le echo?', '¿Cómo mato esa plaga?', '¿A cómo está el maíz?']) {
      const r = respuestaDemo(p, LOTE);
      expect(r.texto).toContain('técnico agrícola');
      expect(r.tarjetas).toEqual([]);
    }
  });

  it('en un lote sin cultivo no habla de un maíz que no existe', () => {
    const otro = LOTES_DEMO[1].id;
    expect(conversacionDemo('con-historia', otro, HOY).mensajes).toEqual([]);
    const r = respuestaDemo('¿Debo regar hoy?', otro);
    expect(r.texto).toContain('no tiene un cultivo registrado');
    expect(r.texto).not.toContain('floración');
  });

  it('el resumen del lote principal tiene cultivo; el otro lote no', () => {
    expect(resumenLoteDemo(LOTE).cultivo?.nombre).toBe('Maíz');
    expect(resumenLoteDemo(LOTES_DEMO[1].id)).toMatchObject({ nombre: 'El Guadual', cultivo: null });
  });
});
