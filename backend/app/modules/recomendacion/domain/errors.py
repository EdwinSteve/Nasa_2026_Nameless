from app.core.errors import ErrorDominio


class LoteSinAcceso(ErrorDominio):
    def __init__(self):
        super().__init__("LOTE_NO_ENCONTRADO", "No encontramos ese lote en su cuenta.", 404)


class RecomendacionNoEncontrada(ErrorDominio):
    def __init__(self):
        super().__init__("RECOMENDACION_NO_ENCONTRADA", "No encontramos esa recomendación para este lote.", 404)


class FechaSiembraInvalida(ErrorDominio):
    def __init__(self, detalle: str):
        super().__init__("RECOMENDACION_FECHA_INVALIDA", detalle, 422)


class ModeloNoDisponible(ErrorDominio):
    def __init__(self, detalle: str):
        super().__init__("RECOMENDACION_MODELO_NO_DISPONIBLE", detalle, 503)
