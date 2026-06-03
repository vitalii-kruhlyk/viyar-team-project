from datetime import date, datetime

import phonenumbers
from email_validator import EmailNotValidError
from email_validator import validate_email as _validate_email
from phonenumbers import NumberParseException


class Field:
    value: str

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value


class Name(Field):
    @Field.value.setter
    def value(self, new_value: str) -> None:
        if not isinstance(new_value, str) or not new_value.strip():
            raise ValueError("Name can't be empty")
        self._value = new_value.strip()


class Phone(Field):
    @staticmethod
    def validate_phone(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Phone number must be a string")
        try:
            parsed = phonenumbers.parse(value)
        except NumberParseException:
            raise ValueError(
                "Phone number must be in international format, e.g. +380501234567"
            )
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Phone number is not valid, e.g. +380501234567")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    @Field.value.setter
    def value(self, new_value: str) -> None:
        self._value = self.validate_phone(new_value)


class Email(Field):
    @staticmethod
    def validate_email(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Email must be a string")
        try:
            email_info = _validate_email(value, check_deliverability=False)
            return email_info.normalized.lower()
        except EmailNotValidError as e:
            raise ValueError(f"Email is not valid: {e}")

    @Field.value.setter
    def value(self, new_value: str) -> None:
        self._value = self.validate_email(new_value)


class Birthday(Field):
    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y")

    @staticmethod
    def validate_birthday(value: str) -> date:
        if not isinstance(value, str):
            raise ValueError("Birthday must be in format DD.MM.YYYY")

        try:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Birthday must be in format DD.MM.YYYY")

    @Field.value.setter
    def value(self, new_value: str) -> None:
        self._value = self.validate_birthday(new_value)
