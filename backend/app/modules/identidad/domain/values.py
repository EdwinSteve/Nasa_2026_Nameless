from __future__ import annotations

from dataclasses import dataclass

import phonenumbers
from email_validator import validate_email, EmailNotValidError

from app.modules.identidad.domain.errors import InvalidPhone, InvalidEmail


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

class Email:
    value: str
    def __post_init__(self):
        try:
            normalized = validate_email(self.value, check_deliverability=False)
        except EmailNotValidError as exc:
            raise InvalidEmail(str(exc)) from exc
        object.__setattr__(self, "value", normalized.normalized.lower())