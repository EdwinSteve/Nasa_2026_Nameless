from app.core.errors import ErrorDominio


class DepartamentoNoDisponible(ErrorDominio):
    def __init__(self, codigo: str):
        super().__init__(
            "TERRITORIO_DEPARTAMENTO_NO_DISPONIBLE",
            f"Todavía no tenemos los municipios del departamento {codigo}.",
            404,
        )


class MunicipioNoEncontrado(ErrorDominio):
    def __init__(self, codigo: str):
        super().__init__("TERRITORIO_MUNICIPIO_NO_ENCONTRADO", f"El municipio {codigo} no existe.", 404)
