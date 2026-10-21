from app.core.errors import ErrorDominio


class FincaNoEncontrada(ErrorDominio):
    """También para fincas de otro productor: no se revela que existen."""

    def __init__(self):
        super().__init__("FINCA_NO_ENCONTRADA", "No encontramos esa finca en su cuenta.", 404)


class LoteNoEncontrado(ErrorDominio):
    def __init__(self):
        super().__init__("LOTE_NO_ENCONTRADO", "No encontramos ese lote en su cuenta.", 404)


class UbicacionInvalida(ErrorDominio):
    def __init__(self, detalle: str):
        super().__init__("FINCA_UBICACION_INVALIDA", detalle, 422)


class PoligonoInvalido(ErrorDominio):
    def __init__(self, detalle: str):
        super().__init__("LOTE_POLIGONO_INVALIDO", detalle, 422)


class RiegoInconsistente(ErrorDominio):
    def __init__(self):
        super().__init__("LOTE_RIEGO_INCONSISTENTE", "Si el lote tiene riego, indica el tipo de riego.", 422)


class PrioridadesInvalidas(ErrorDominio):
    def __init__(self):
        super().__init__(
            "PREFERENCIAS_INVALIDAS",
            "Ordena las cuatro prioridades, cada una una sola vez.",
            422,
        )
