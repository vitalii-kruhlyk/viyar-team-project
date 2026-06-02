from datetime import date, datetime
from re import fullmatch


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
    def validate_phone(value: str) -> None:
        if not isinstance(value, str) or not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")

    @Field.value.setter
    def value(self, new_value: str) -> None:
        self.validate_phone(new_value)
        self._value = new_value


class Email(Field):
    @staticmethod
    def validate_email(value: str) -> None:
        pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"
        if not isinstance(value, str) or not fullmatch(pattern, value):
            raise ValueError("Email must be a valid address, e.g. user@example.com")

    @Field.value.setter
    def value(self, new_value: str) -> None:
        self.validate_email(new_value)
        self._value = new_value


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
