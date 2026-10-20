import httpx
import pytest

from app.api import app

BASE = "/api/v1/territorio"


@pytest.fixture
async def cliente():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as cliente:
        yield cliente


async def test_los_37_municipios_del_huila_en_orden_alfabetico(cliente):
    respuesta = await cliente.get(f"{BASE}/municipios", params={"departamento": "41"})

    assert respuesta.status_code == 200
    municipios = respuesta.json()
    assert len(municipios) == 37
    assert {"codigo": "41001", "nombre": "Neiva"}.items() <= municipios[[m["codigo"] for m in municipios].index("41001")].items()
    nombres = [m["nombre"] for m in municipios]
    assert nombres.index("Íquira") < nombres.index("La Plata")  # las tildes no alteran el orden


async def test_departamento_por_defecto_es_huila(cliente):
    respuesta = await cliente.get(f"{BASE}/municipios")

    assert len(respuesta.json()) == 37


async def test_departamento_sin_cargar_responde_404(cliente):
    respuesta = await cliente.get(f"{BASE}/municipios", params={"departamento": "05"})

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "TERRITORIO_DEPARTAMENTO_NO_DISPONIBLE"


async def test_codigo_de_departamento_invalido_responde_422(cliente):
    respuesta = await cliente.get(f"{BASE}/municipios", params={"departamento": "huila"})

    assert respuesta.status_code == 422


async def test_corregimientos_de_neiva_empiezan_por_el_casco_urbano(cliente):
    respuesta = await cliente.get(f"{BASE}/municipios/41001/corregimientos")

    assert respuesta.status_code == 200
    centros = respuesta.json()
    assert centros[0]["nombre"] == "Casco urbano" and centros[0]["tipo"] == "cabecera"
    nombres = {c["nombre"] for c in centros}
    assert {"Fortalecillas", "Aipecito", "San Luis", "Vegalarga"} <= nombres
    assert all(c["codigo"].startswith("41001") and len(c["codigo"]) == 8 for c in centros)


async def test_municipio_inexistente_responde_404(cliente):
    respuesta = await cliente.get(f"{BASE}/municipios/41999/corregimientos")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "TERRITORIO_MUNICIPIO_NO_ENCONTRADO"
