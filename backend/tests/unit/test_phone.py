import pytest

from app.modules.identidad.domain.errors import InvalidPhone
from app.modules.identidad.domain.values import Phone


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("3001234567", "+573001234567"),
        ("300 123 4567", "+573001234567"),
        ("+573001234567", "+573001234567"),
    ],
)
def test_desde_entrada_normaliza_a_e164_con_region_colombia(entrada, esperado):
    assert Phone.desde_entrada(entrada).value == esperado


@pytest.mark.parametrize("entrada", ["", "123", "abc", "+1 555"])
def test_desde_entrada_rechaza_numeros_invalidos(entrada):
    with pytest.raises(InvalidPhone):
        Phone.desde_entrada(entrada)
