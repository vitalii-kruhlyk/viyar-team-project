from collections import UserDict
from typing import Any, Iterator

from models.fields import Birthday, Email, Name, Phone


class Address:
    country: str
    city: str
    street: str
    house: str

    def __init__(self, country: str, city: str, street: str, house: str) -> None:
        if not all(
            isinstance(v, str) and v.strip() for v in [country, city, street, house]
        ):
            raise ValueError(
                "All address fields (country, city, street, house) must be non-empty"
            )
        self.country = country.strip()
        self.city = city.strip()
        self.street = street.strip()
        self.house = house.strip()

    def __str__(self) -> str:
        return f"{self.country}, {self.city}, {self.street}, {self.house}"

    def matches(
        self,
        country: str | None = None,
        city: str | None = None,
        street: str | None = None,
        house: str | None = None,
    ) -> bool:
        if country and country.lower() not in self.country.lower():
            return False
        if city and city.lower() not in self.city.lower():
            return False
        if street and street.lower() not in self.street.lower():
            return False
        if house and house.lower() not in self.house.lower():
            return False
        return True

    def to_dict(self) -> dict[str, str]:
        return {
            "country": self.country,
            "city": self.city,
            "street": self.street,
            "house": self.house,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Address":
        return cls(
            country=data["country"],
            city=data["city"],
            street=data["street"],
            house=data["house"],
        )


class Record:
    name: Name
    phones: list[Phone]
    emails: list[Email]
    birthday: Birthday | None
    address: Address | None
    favorite: bool

    def __init__(self, name: str, birthday: str | None = None) -> None:
        self.name = Name(name)
        self.phones = []
        self.emails = []
        self.birthday = Birthday(birthday) if birthday is not None else None
        self.address = None
        self.favorite = False

    def __str__(self) -> str:
        phones = "; ".join(p.value for p in self.phones)
        emails = "; ".join(e.value for e in self.emails)
        mark = "*" if self.favorite else ""
        parts = [f"Contact name: {mark}{self.name.value}", f"phones: {phones}"]
        if emails:
            parts.append(f"emails: {emails}")
        if self.address:
            parts.append(f"address: {self.address}")
        if self.birthday:
            parts.append(f"birthday: {self.birthday}")
        return ", ".join(parts)

    @property
    def favorite(self):
        return self._favorite

    @favorite.setter
    def favorite(self, value) -> None:
        self._favorite = value

    def find_phone(self, phone: str) -> Phone | None:
        try:
            normalized = Phone.validate_phone(phone)
        except ValueError:
            normalized = phone
        for phone_obj in self.phones:
            if phone_obj.value == normalized:
                return phone_obj
        return None

    def add_phone(self, phone: str) -> None:
        if self.find_phone(phone) is not None:
            raise ValueError(
                f"Phone number {phone} already exists for contact {self.name.value}"
            )
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        phone_obj = self.find_phone(phone)
        if phone_obj is None:
            raise ValueError(
                f"Phone number {phone} not found for contact {self.name.value}"
            )
        self.phones.remove(phone_obj)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        old_phone_obj = self.find_phone(old_phone)
        if old_phone_obj is None:
            raise ValueError(
                f"Phone number {old_phone} not found for contact {self.name.value}"
            )
        new_phone_obj = self.find_phone(new_phone)
        if new_phone_obj is not None and new_phone_obj != old_phone_obj:
            raise ValueError(
                f"Phone {new_phone} already exists for contact {self.name.value}"
            )
        old_phone_obj.value = new_phone

    def find_email(self, email: str) -> Email | None:
        try:
            normalized = Email.validate_email(email)
        except ValueError:
            normalized = email
        for email_obj in self.emails:
            if email_obj.value == normalized:
                return email_obj
        return None

    def add_email(self, email: str) -> None:
        if self.find_email(email) is not None:
            raise ValueError(
                f"Email {email} already exists for contact {self.name.value}"
            )
        self.emails.append(Email(email))

    def remove_email(self, email: str) -> None:
        email_obj = self.find_email(email)
        if email_obj is None:
            raise ValueError(f"Email {email} not found for contact {self.name.value}")
        self.emails.remove(email_obj)

    def edit_email(self, old_email: str, new_email: str) -> None:
        old_email_obj = self.find_email(old_email)
        if old_email_obj is None:
            raise ValueError(
                f"Email {old_email} not found for contact {self.name.value}"
            )
        new_email_obj = self.find_email(new_email)
        if new_email_obj is not None and new_email_obj != old_email_obj:
            raise ValueError(
                f"Email {new_email} already exists for contact {self.name.value}"
            )
        old_email_obj.value = new_email

    def add_address(self, country: str, city: str, street: str, house: str) -> None:
        if self.address is not None:
            raise ValueError(
                f"Address already exists for contact {self.name.value}. "
                "Use change_address to update it."
            )
        self.address = Address(country, city, street, house)

    def change_address(self, country: str, city: str, street: str, house: str) -> None:
        if self.address is None:
            raise ValueError(
                f"No address set for contact {self.name.value}. "
                "Use add_address to add one."
            )
        self.address = Address(country, city, street, house)

    def remove_address(self) -> None:
        if self.address is None:
            raise ValueError(f"No address set for contact {self.name.value}")
        self.address = None

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    @staticmethod
    def _birthday_for_year(birthday, year: int):
        from datetime import date

        try:
            return birthday.replace(year=year)
        except ValueError:
            return date(year, 3, 1)

    def days_to_birthday(self) -> int | None:
        if self.birthday is None:
            return None

        from datetime import date

        today = date.today()
        birthday = self.birthday.value
        next_birthday = self._birthday_for_year(birthday, today.year)
        if next_birthday < today:
            next_birthday = self._birthday_for_year(birthday, today.year + 1)

        return (next_birthday - today).days

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": str(self.name),
            "phones": [str(p) for p in self.phones],
            "emails": [str(e) for e in self.emails],
        }
        if self.birthday is not None:
            result["birthday"] = self.birthday.value.isoformat()
        if self.address is not None:
            result["address"] = self.address.to_dict()
        if self.favorite is not None:
            result["favorite"] = self.favorite
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Record":
        name = data.get("name")
        if not isinstance(name, str):
            raise ValueError("Record name is missing or invalid")

        birthday = data.get("birthday")
        if birthday is not None and not isinstance(birthday, str):
            raise ValueError("Birthday must be a string")

        record = cls(name, birthday)

        for phone in data.get("phones", []):
            record.add_phone(phone)

        for email in data.get("emails", []):
            record.add_email(email)

        address_data = data.get("address")
        if address_data is not None:
            record.address = Address.from_dict(address_data)

        favorite_data = data.get("favorite")
        if favorite_data is not None:
            record.favorite = favorite_data

        return record


class AddressBook(UserDict[str, Record]):
    data: dict[str, Record]

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        return self.data.get(name)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]

    def iterator(self, n: int) -> Iterator[list[Record]]:
        if n <= 0:
            raise ValueError("Chunk size must be greater than 0")

        records = list(self.data.values())
        for i in range(0, len(records), n):
            yield records[i : i + n]

    def search(self, query: str) -> list[Record]:
        results = []
        query_lower = query.lower()
        for record in self.data.values():
            if (
                query_lower in record.name.value.lower()
                or any(query_lower in phone.value for phone in record.phones)
                or any(query_lower in email.value.lower() for email in record.emails)
            ):
                results.append(record)
        return results

    def search_by_address(
        self,
        country: str | None = None,
        city: str | None = None,
        street: str | None = None,
        house: str | None = None,
    ) -> list[Record]:
        results = []
        for record in self.data.values():
            if record.address is not None and record.address.matches(
                country, city, street, house
            ):
                results.append(record)
        return results

    def get_favorites(self):
        return [record for record in self.data.values() if record.favorite]
