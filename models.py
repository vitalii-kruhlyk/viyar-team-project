from collections import UserDict
from datetime import datetime, date
from typing import Any, Iterator


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


class Record:
	name: Name
	phones: list[Phone]

	def __init__(self, name: str, birthday: str | None = None) -> None:
		self.name = Name(name)
		self.phones = []
		self.birthday = Birthday(birthday) if birthday is not None else None

	def __str__(self) -> str:
		phones = "; ".join(p.value for p in self.phones)
		if self.birthday:
			return f"Contact name: {self.name.value}, phones: {phones}, birthday: {self.birthday}"
		return f"Contact name: {self.name.value}, phones: {phones}"

	def find_phone(self, phone: str) -> Phone | None:
		for phone_obj in self.phones:
			if phone_obj.value == phone:
				return phone_obj
		return None

	def add_phone(self, phone: str) -> None:
		if self.find_phone(phone) is not None:
			raise ValueError(f"Phone number {phone} already exists for contact {self.name.value}")

		self.phones.append(Phone(phone))

	def remove_phone(self, phone: str) -> None:
		phone_obj = self.find_phone(phone)
		if phone_obj is None:
			raise ValueError(f"Phone number {phone} not found for contact {self.name.value}")

		self.phones.remove(phone_obj)

	def edit_phone(self, old_phone: str, new_phone: str) -> None:
		old_phone_obj = self.find_phone(old_phone)
		if old_phone_obj is None:
			raise ValueError(f"Phone number {old_phone} not found for contact {self.name.value}")

		new_phone_obj = self.find_phone(new_phone)
		if new_phone_obj is not None and new_phone_obj != old_phone_obj:
			raise ValueError(f"This phone number {new_phone} already exists for contact {self.name.value}")

		old_phone_obj.value = new_phone

	def add_birthday(self, birthday: str) -> None:
		self.birthday = Birthday(birthday)

	def _birthday_for_year(self, birthday: date, year: int) -> date:
		try:
			return birthday.replace(year=year)
		except ValueError:
			return date(year, 3, 1)

	def days_to_birthday(self) -> int | None:
		if self.birthday is None:
			return None

		today = date.today()
		birthday = self.birthday.value
		next_birthday = self._birthday_for_year(birthday, today.year)
		if next_birthday < today:
			next_birthday = self._birthday_for_year(birthday, today.year + 1)

		return (next_birthday - today).days

	def to_dict(self) -> dict[str, str | list[str]]:
		result = {"name": str(self.name), "phones": [str(p) for p in self.phones]}
		if self.birthday is not None:
			result["birthday"] = self.birthday.value.isoformat()

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
			yield records[i:i + n]

	def search(self, query: str) -> list[Record]:
		results = []
		if query.isdigit():
			for record in self.data.values():
				if any(query in phone.value for phone in record.phones):
					results.append(record)
		else:
			query = query.lower()
			for record in self.data.values():
				if query in record.name.value.lower():
					results.append(record)

		return results