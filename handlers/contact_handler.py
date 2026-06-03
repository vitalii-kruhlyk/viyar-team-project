from collections.abc import Callable

from handlers.decorators import input_error
from models import AddressBook, Record
from storage import JsonStorage


class ContactHandler:
    book: AddressBook
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage
        self.book = storage.load()
        self.commands = {
            "add": self.add,
            "add_birthday": self.add_birthday,
            "add_email": self.add_email,
            "add_address": self.add_address,
            "birthday": self.birthday,
            "change": self.change,
            "change_email": self.change_email,
            "change_address": self.change_address,
            "phone": self.phone,
            "show": self.show_all,
            "show_page": self.show_page,
            "delete": self.delete_contact,
            "remove_phone": self.remove_phone,
            "remove_email": self.remove_email,
            "remove_address": self.remove_address,
            "find_phone": self.find_phone,
            "find_email": self.find_email,
            "search": self.search,
            "search_address": self.search_address,
        }

    @input_error
    def add(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: add <name> <phone>")

        name, phone_number = args

        record = self.book.find(name)
        if record is None:
            record = Record(name)
            record.add_phone(phone_number)
            self.book.add_record(record)
        else:
            record.add_phone(phone_number)

        self.storage.save(self.book)
        return f"Contact {name} added.", False

    @input_error
    def add_birthday(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: add_birthday <name> <DD.MM.YYYY>")

        name, birthday = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.add_birthday(birthday)
        self.storage.save(self.book)
        return f"Birthday for {name} added.", False

    @input_error
    def add_email(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: add_email <name> <email>")

        name, email = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.add_email(email)
        self.storage.save(self.book)
        return f"Email {email} added to contact {name}.", False

    @input_error
    def add_address(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 5:
            raise ValueError(
                "Usage: add_address <name> <country> <city> <street> <house>"
            )

        name, country, city, street, house = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.add_address(country, city, street, house)
        self.storage.save(self.book)
        return f"Address added to contact {name}.", False

    @input_error
    def birthday(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: birthday <name>")

        name = args[0]

        record = self.book.find(name)
        if record is None:
            raise KeyError

        days = record.days_to_birthday()
        if days is None:
            text_return = f"Birthday for contact {name} is not set."
        elif days == 0:
            text_return = f"Today is {name}'s birthday!"
        else:
            text_return = f"{days} day(s) left until {name}'s birthday"

        return text_return, False

    @input_error
    def change(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 3:
            raise ValueError("Usage: change <name> <old_phone> <new_phone>")

        name, old_number, new_number = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.edit_phone(old_number, new_number)
        self.storage.save(self.book)
        return f"Contact {name} changed.", False

    @input_error
    def change_email(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 3:
            raise ValueError("Usage: change_email <name> <old_email> <new_email>")

        name, old_email, new_email = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.edit_email(old_email, new_email)
        self.storage.save(self.book)
        return f"Email updated for contact {name}.", False

    @input_error
    def change_address(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 5:
            raise ValueError(
                "Usage: change_address <name> <country> <city> <street> <house>"
            )

        name, country, city, street, house = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.change_address(country, city, street, house)
        self.storage.save(self.book)
        return f"Address updated for contact {name}.", False

    @input_error
    def phone(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: phone <name>")

        name = args[0]

        record = self.book.find(name)
        if record is None:
            raise KeyError

        return str(record), False

    @input_error
    def show_all(self, _args: list[str]) -> tuple[str, bool]:
        if not self.book.data:
            return "No contacts saved.", False

        return "\n".join(str(record) for record in self.book.data.values()), False

    @input_error
    def show_page(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: show_page <page_size>")

        if not args[0].isdigit() or int(args[0]) == 0:
            raise ValueError("Page size must be a positive whole number")

        page_size = int(args[0])

        if not self.book.data:
            return "No contacts saved.", False

        pages = []
        for index, chunk in enumerate(self.book.iterator(page_size), start=1):
            page_text = "\n".join(str(record) for record in chunk)
            pages.append(f"Page {index}:\n{page_text}")

        return "\n\n".join(pages), False

    @input_error
    def delete_contact(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: delete <name>")

        name = args[0]

        if self.book.find(name) is None:
            raise KeyError

        self.book.delete(name)
        self.storage.save(self.book)
        return f"Contact {name} deleted.", False

    @input_error
    def remove_phone(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: remove_phone <name> <phone>")

        name, phone_number = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.remove_phone(phone_number)
        self.storage.save(self.book)
        return f"Phone number {phone_number} removed from contact {name}.", False

    @input_error
    def remove_email(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: remove_email <name> <email>")

        name, email = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.remove_email(email)
        self.storage.save(self.book)
        return f"Email {email} removed from contact {name}.", False

    @input_error
    def remove_address(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: remove_address <name>")

        name = args[0]

        record = self.book.find(name)
        if record is None:
            raise KeyError

        record.remove_address()
        self.storage.save(self.book)
        return f"Address removed from contact {name}.", False

    @input_error
    def find_phone(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: find_phone <name> <phone>")

        name, phone_number = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        found_phone = record.find_phone(phone_number)
        if found_phone is None:
            return f"Phone number {phone_number} not found in contact {name}.", False

        return f"{name}: {found_phone}", False

    @input_error
    def find_email(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 2:
            raise ValueError("Usage: find_email <name> <email>")

        name, email = args

        record = self.book.find(name)
        if record is None:
            raise KeyError

        found_email = record.find_email(email)
        if found_email is None:
            return f"Email {email} not found in contact {name}.", False

        return f"{name}: {found_email}", False

    @input_error
    def search(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: search <query>")

        query = args[0]
        results = self.book.search(query)

        if not results:
            return f"No contacts found for query: {query}", False

        return "\n".join(str(record) for record in results), False

    @input_error
    def search_address(self, args: list[str]) -> tuple[str, bool]:
        if not args or len(args) > 4:
            raise ValueError("Usage: search_address <country> [city] [street] [house]")

        country = args[0] if len(args) >= 1 else None
        city = args[1] if len(args) >= 2 else None
        street = args[2] if len(args) >= 3 else None
        house = args[3] if len(args) >= 4 else None

        results = self.book.search_by_address(country, city, street, house)

        if not results:
            return "No contacts found for the given address.", False

        return "\n".join(str(record) for record in results), False
