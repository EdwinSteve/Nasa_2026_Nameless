from __future__ import annotations

from dataclasses import dataclass

import phonenumbers
from email_validator import validate_email, EmailNotValidError

from app.modules.identidad.domain.errors import InvalidPhone, InvalidEmail


REGION_POR_DEFECTO = "CO"


@dataclass(frozen=True, slots=True)
class Phone:
    value: str

    def __post_init__(self):
        try:
            parsed = phonenumbers.parse(self.value)
        except phonenumbers.NumberParseException as exc:
            raise InvalidPhone(str(exc)) from exc
        if not phonenumbers.is_valid_number(parsed):
            raise InvalidPhone("El celular no es válido en formato E.164.")
        if not self.value.startswith("+"):
            raise InvalidPhone("El celular debe incluir el prefijo internacional (+57...).")

    @classmethod
    def desde_entrada(cls, texto: str, region: str = REGION_POR_DEFECTO) -> "Phone":
        """Convierte lo que escribe la persona (p. ej. '3001234567') a E.164 ('+573001234567').

        Lanza InvalidPhone si el texto no es un número válido. Quien llama decide
        el mensaje que muestra, para no revelar si el celular existe.
        """
        try:
            parsed = phonenumbers.parse(texto, region)
        except phonenumbers.NumberParseException as exc:
            raise InvalidPhone(str(exc)) from exc
        if not phonenumbers.is_valid_number(parsed):
            raise InvalidPhone("El celular no es válido.")
        return cls(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))

@dataclass(frozen=True, slots=True)
class Email:
    value: str
    def __post_init__(self):
        try:
            normalized = validate_email(self.value, check_deliverability=False)
        except EmailNotValidError as exc:
            raise InvalidEmail(str(exc)) from exc
        object.__setattr__(self, "value", normalized.normalized.lower())