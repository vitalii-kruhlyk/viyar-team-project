from datetime import date, timedelta

from handlers.decorators import input_error
from interfaces.parser import split_values
from models import AddressBook, Record
from storage import JsonStorage


class ContactHandler:
    storage: JsonStorage
    book: AddressBook

    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage
        self.book = AddressBook()
        for item in storage.load():
            self.book.add_record(Record.from_dict(item))

    def _save(self) -> None:
        self.storage.save([record.to_dict() for record in self.book.values()])

    @input_error
    def add_contact(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags:
            raise ValueError("Usage: add --contact -n <name> [-p phones] [-e emails] [-b DD.MM.YYYY]")
        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            record = Record(name)
            self.book.add_record(record)

        if "-p" in flags:
            for phone in split_values(flags["-p"]):
                record.add_phone(phone)

        if "-e" in flags:
            for email in split_values(flags["-e"]):
                record.add_email(email)

        if "-b" in flags:
            record.add_birthday(flags["-b"])

        self._save()
        return f"Contact {name} added.", False

    @input_error
    def add_phone(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-p" not in flags:
            raise ValueError("Usage: add --phone -n <name> -p <phone1,phone2>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        for phone in split_values(flags["-p"]):
            record.add_phone(phone)

        self._save()
        return f"Phone(s) added to {name}.", False

    @input_error
    def add_email(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-e" not in flags:
            raise ValueError("Usage: add --email -n <name> -e <email1,email2>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        for email in split_values(flags["-e"]):
            record.add_email(email)

        self._save()
        return f"Email(s) added to '{name}'.", False

    @input_error
    def add_birthday(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-b" not in flags:
            raise ValueError("Usage: add --birthday -n <name> -b <DD.MM.YYYY>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.add_birthday(flags["-b"])
        self._save()
        return f"Birthday for {name} added.", False

    @input_error
    def add_address(self, flags: dict[str, str]) -> tuple[str, bool]:
        required = {"-n", "-country", "-city", "-street", "-house"}
        if not required.issubset(flags):
            raise ValueError("Usage: add --address -n <name> " "-country <X> -city <X> -street <X> -house <X>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.add_address(flags["-country"], flags["-city"], flags["-street"], flags["-house"])
        self._save()
        return f"Address added to {name}.", False

    @input_error
    def birthday(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-days" not in flags:
            raise ValueError("Usage: birthday --upcoming -days <number>")

        if not flags["-days"].isdigit() or int(flags["-days"]) <= 0:
            raise ValueError("Number of days must be a positive whole number")

        number_of_days = int(flags["-days"])
        day_today = date.today()
        birthday_date_end = day_today + timedelta(days=number_of_days)

        contacts = []
        for record in self.book.data.values():
            if record.birthday is None:
                continue
            bday = record.birthday.value
            contact_birthday = Record._birthday_for_year(bday, day_today.year)
            if contact_birthday < day_today:
                contact_birthday = Record._birthday_for_year(bday, day_today.year + 1)
            if day_today <= contact_birthday <= birthday_date_end:
                contacts.append(record.name.value)

        if not contacts:
            return f"No birthdays in the next {number_of_days} day(s).", False

        names = "\n".join(contacts)
        return f"Birthdays in the next {number_of_days} day(s):\n{names}", False

    @input_error
    def edit_phone(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-old" not in flags or "-new" not in flags:
            raise ValueError("Usage: edit --phone -n <name> -old <phone> -new <phone>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.edit_phone(flags["-old"], flags["-new"])
        self._save()
        return f"Phone updated for '{name}'", False

    @input_error
    def edit_email(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-old" not in flags or "-new" not in flags:
            raise ValueError("Usage: edit --email -n <name> -old <email> -new <email>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.edit_email(flags["-old"], flags["-new"])
        self._save()
        return f"Email updated for {name}.", False

    @input_error
    def edit_address(self, flags: dict[str, str]) -> tuple[str, bool]:
        required = {"-n", "-country", "-city", "-street", "-house"}
        if not required.issubset(flags):
            raise ValueError("Usage: edit --address -n <name> " "-country <X> -city <X> -street <X> -house <X>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.change_address(flags["-country"], flags["-city"], flags["-street"], flags["-house"])
        self._save()
        return f"Address updated for contact {name}.", False

    @input_error
    def show_all(self, flags: dict[str, str]) -> tuple[str, bool]:
        if not self.book.data:
            return "No contacts saved.", False

        if "-page" in flags:
            if not flags["-page"].isdigit() or int(flags["-page"]) == 0:
                raise ValueError("Page size must be a positive whole number")
            page_size = int(flags["-page"])
            pages = []
            for index, chunk in enumerate(self.book.iterator(page_size), start=1):
                page_text = "\n".join(str(record) for record in chunk)
                pages.append(f"Page {index}:\n{page_text}")
            return "\n\n".join(pages), False

        return "\n".join(str(record) for record in self.book.data.values()), False

    @input_error
    def show_one(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags:
            raise ValueError("Usage: show --contact -n <name>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        return str(record), False

    @input_error
    def delete_contact(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags:
            raise ValueError("Usage: delete --contact -n <name>")

        name = flags["-n"]
        if self.book.find(name) is None:
            raise KeyError("Contact not found")

        self.book.delete(name)
        self._save()
        return f"Contact {name} deleted.", False

    @input_error
    def remove_phone(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-p" not in flags:
            raise ValueError("Usage: remove --phone -n <name> -p <phone>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.remove_phone(flags["-p"])
        self._save()
        return f"Phone removed from '{name}'.", False

    @input_error
    def remove_email(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags or "-e" not in flags:
            raise ValueError("Usage: remove --email -n <name> -e <email>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.remove_email(flags["-e"])
        self._save()
        return f"Email removed from '{name}'.", False

    @input_error
    def remove_address(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags:
            raise ValueError("Usage: remove --address -n <name>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.remove_address()
        self._save()
        return f"Address removed from {name}.", False

    @input_error
    def search(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-q" not in flags:
            raise ValueError("Usage: search --contact -q <query>")

        query = flags["-q"]
        results = self.book.search(query)
        if not results:
            return f"No contacts found for query: {query}", False

        return "\n".join(str(record) for record in results), False

    @input_error
    def search_address(self, flags: dict[str, str]) -> tuple[str, bool]:
        if not any(f in flags for f in ("-country", "-city", "-street", "-house")):
            raise ValueError("Usage: search --address " "[-country <X>] [-city <X>] [-street <X>] [-house <X>]")

        results = self.book.search_by_address(
            country=flags.get("-country"),
            city=flags.get("-city"),
            street=flags.get("-street"),
            house=flags.get("-house"),
        )
        if not results:
            return "No contacts found for the given address.", False

        return "\n".join(str(record) for record in results), False

    @input_error
    def add_to_favorites(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags:
            raise ValueError("Usage: add --favorite -n <name>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.favorite = True
        self._save()
        return f"{name} added to favorites.", False

    @input_error
    def remove_from_favorites(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-n" not in flags:
            raise ValueError("Usage: remove --favorite -n <name>")

        name = flags["-n"]
        record = self.book.find(name)
        if record is None:
            raise KeyError("Contact not found")

        record.favorite = False
        self._save()
        return f"{name} removed from favorites.", False

    @input_error
    def show_favorites(self, flags: dict[str, str]) -> tuple[str, bool]:
        favorites = self.book.get_favorites()
        if not favorites:
            return "No favorites saved.", False

        return "\n".join(str(record) for record in favorites), False
