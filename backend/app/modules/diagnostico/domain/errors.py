from app.core.errors import ErrorDominio


class DiagnosticoNoEncontrado(ErrorDominio):
    def __init__(self):
        super().__init__("DIAGNOSTICO_NO_ENCONTRADO", "No encontramos ese diagnóstico para este lote.", 404)


class LoteSinAcceso(ErrorDominio):
    """El lote no existe o es de otro productor: no se distingue."""

    def __init__(self):
        super().__init__("LOTE_NO_ENCONTRADO", "No encontramos ese lote en tu cuenta.", 404)
