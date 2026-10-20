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


class RefreshTokenInvalid(ErrorDominio):
    """Mismo error para token inexistente, expirado, revocado, reutilizado o de usuario bloqueado.
    No se distingue el motivo para no dar pistas a quien intenta robar un token."""

    def __init__(self):
        super().__init__(
            "AUTH_REFRESH_INVALIDO",
            "La sesión ya no es válida. Vuelve a iniciar sesión.",
            401,
        )


class UserAlreadyExists(ErrorDominio):
    def __init__(self):
        super().__init__("IDENTIDAD_USUARIO_DUPLICADO", "El usuario ya existe.", 409)

class PhoneAlreadyRegistered(ErrorDominio):
    def __init__(self):
        super().__init__("USUARIO_CELULAR_DUPLICADO", "Ese celular ya está registrado.", 409)


class EmailAlreadyRegistered(ErrorDominio):
    def __init__(self):
        super().__init__("USUARIO_CORREO_DUPLICADO", "Ese correo ya está registrado.", 409)


class ConsentRequired(ErrorDominio):
    def __init__(self):
        super().__init__(
            "CONSENTIMIENTO_REQUERIDO",
            "Debes autorizar el tratamiento de tus datos para crear la cuenta.",
            422,
        )


class PolicyUnavailable(ErrorDominio):
    def __init__(self):
        super().__init__(
            "POLITICA_NO_DISPONIBLE",
            "No hay una política de privacidad vigente. Intenta más tarde.",
            503,
        )


class PolicyOutdated(ErrorDominio):
    def __init__(self):
        super().__init__(
            "POLITICA_DESACTUALIZADA",
            "La política de privacidad cambió. Revisa la versión vigente y acéptala de nuevo.",
            409,
        )