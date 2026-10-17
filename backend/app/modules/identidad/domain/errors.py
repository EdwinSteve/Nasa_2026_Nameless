from app.core.errors import ErrorDominio


class InvalidPhone(ErrorDominio):
    def __init__(self, detalle: str = "Celular inválido."):
        super().__init__("IDENTIDAD_CELULAR_INVALIDO", detalle, 400)


class InvalidEmail(ErrorDominio):
    def __init__(self, detalle: str = "Correo inválido."):
        super().__init__("IDENTIDAD_CORREO_INVALIDO", detalle, 400)


class UserNotFound(ErrorDominio):
    def __init__(self):
        super().__init__("IDENTIDAD_USUARIO_NO_ENCONTRADO", "El usuario no existe.", 404)


class InvalidCredentials(ErrorDominio):
    def __init__(self):
        super().__init__(
            "AUTH_CREDENCIALES_INVALIDAS",
            "El celular o la contraseña no son correctos.",
            401,
        )


class UserBlocked(ErrorDominio):
    def __init__(self):
        super().__init__(
            "AUTH_CUENTA_BLOQUEADA",
            "La cuenta está temporalmente bloqueada por intentos fallidos. Intenta más tarde.",
            423,
        )


class UserAlreadyExists(ErrorDominio):
    def __init__(self):
        super().__init__("IDENTIDAD_USUARIO_DUPLICADO", "El usuario ya existe.", 409)