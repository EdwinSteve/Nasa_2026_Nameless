"""Descarga DIVIPOLA (DANE) de datos.gov.co y genera el JSON que sirve el módulo territorio.

    python scripts/actualizar_divipola.py              # Huila (41)
    python scripts/actualizar_divipola.py 41 73        # varios departamentos

Fuentes (datos abiertos del DANE en datos.gov.co):
- gdxc-w37w: DIVIPOLA, códigos de municipios.
- xaxy-8nri: DIVIPOLA, cabeceras y centros poblados.
"""
import json
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

DESTINO = Path(__file__).resolve().parents[1] / 'app/modules/territorio/infrastructure/datos/divipola.json'
MUNICIPIOS = 'https://www.datos.gov.co/resource/gdxc-w37w.json'
CENTROS = 'https://www.datos.gov.co/resource/xaxy-8nri.json'
MINUSCULAS = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e'}


def consultar(url: str, **filtros) -> list[dict]:
    consulta = urllib.parse.urlencode({**filtros, '$limit': 5000})
    with urllib.request.urlopen(f'{url}?{consulta}', timeout=120) as respuesta:
        return json.load(respuesta)


def nombre_propio(texto: str) -> str:
    """'SAN ANTONIO DE ANACONIA' -> 'San Antonio de Anaconia'."""
    palabras = texto.strip().lower().split()
    return ' '.join(p if i and p in MINUSCULAS else p[:1].upper() + p[1:] for i, p in enumerate(palabras))


def orden(texto: str) -> str:
    """Clave de orden alfabético sin tildes: 'Íquira' va antes de 'La Plata'."""
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode().lower()


def coordenada(texto: str | None) -> float | None:
    """El DANE usa coma decimal y a veces separador de miles ('-75,581,775')."""
    if not texto:
        return None
    entero, _, decimales = texto.partition(',')
    return round(float(f"{entero}.{decimales.replace(',', '')}"), 6)


def departamento(codigo: str) -> dict:
    municipios = consultar(MUNICIPIOS, cod_dpto=codigo)
    centros = consultar(CENTROS, codigo_departamento=codigo)
    if not municipios:
        raise SystemExit(f'Sin municipios para el departamento {codigo}')
    por_municipio: dict[str, list[dict]] = {}
    for c in centros:
        por_municipio.setdefault(c['codigo_municipio'], []).append({
            'codigo': c['codigo_centro_poblado'],
            'nombre': nombre_propio(c['nombre_centro_poblado']),
            # CM = cabecera municipal (casco urbano), CP = centro poblado rural
            'tipo': c['tipo_centro_poblado'],
            'lat': coordenada(c.get('latitud')),
            'lon': coordenada(c.get('longitud')),
        })
    return {
        'codigo': codigo,
        'nombre': nombre_propio(municipios[0]['dpto']),
        'municipios': [
            {
                'codigo': m['cod_mpio'],
                'nombre': nombre_propio(m['nom_mpio']),
                'lat': coordenada(m.get('latitud')),
                'lon': coordenada(m.get('longitud')),
                'centros_poblados': sorted(
                    por_municipio.get(m['cod_mpio'], []), key=lambda c: (c['tipo'] != 'CM', orden(c['nombre']))
                ),
            }
            for m in sorted(municipios, key=lambda m: orden(m['nom_mpio']))
        ],
    }


def main() -> None:
    codigos = sys.argv[1:] or ['41']
    datos = {
        'fuente': 'DANE, DIVIPOLA (datos.gov.co: gdxc-w37w y xaxy-8nri)',
        'descargado': date.today().isoformat(),
        'departamentos': [departamento(c) for c in codigos],
    }
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for d in datos['departamentos']:
        centros = sum(len(m['centros_poblados']) for m in d['municipios'])
        print(f"{d['nombre']}: {len(d['municipios'])} municipios, {centros} cabeceras y centros poblados")
    print('Guardado en', DESTINO)


if __name__ == '__main__':
    main()
