import functools
import json
from collections.abc import Callable
from pathlib import Path
from models import AddressBook, Record


DATA_FILE = Path(__file__).resolve().parent / "contacts.json"


def input_error(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except KeyError:
			return "Contact not found", False
		except ValueError as error:
			return str(error), False
		except IndexError:
			return "Enter user name", False
	return wrapper


class Bot:
	book: AddressBook
	commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

	def __init__(self) -> None:
		self.book = self._load_contacts()
		self.commands = {
			"hello": self.hello,
			"add": self.add,
			"add_birthday": self.add_birthday,
			"birthday": self.birthday,
			"change": self.change,
			"phone": self.phone,
			"show": self.show_all,
			"show_page": self.show_page,
			"delete": self.delete_contact,
			"remove_phone": self.remove_phone,
			"find_phone": self.find_phone,
			"search": self.search,
			"good bye": self.exit_bot,
			"close": self.exit_bot,
			"stop": self.exit_bot,
			"exit": self.exit_bot,
		}

	def _load_contacts(self) -> AddressBook:
		if not DATA_FILE.exists():
			return AddressBook()

		try:
			with open(DATA_FILE, "r", encoding="utf-8") as file:
				book = AddressBook()
				for item in json.load(file):
					record = Record.from_dict(item)
					book.add_record(record)
				return book
		except json.JSONDecodeError:
			return AddressBook()

	def _save_contacts(self) -> None:
		temp_file = DATA_FILE.with_suffix(".tmp")

		with open(temp_file, "w", encoding="utf-8") as file:
			json.dump([record.to_dict() for record in self.book.values()], file, indent=4)

		temp_file.replace(DATA_FILE)

	def parse_command(self, user_input: str) -> tuple[str | None, list[str]]:
		cleaned_input = user_input.strip()
		lowered_input = cleaned_input.lower()

		for command in sorted(self.commands, key=len, reverse=True):
			if lowered_input == command or lowered_input.startswith(command + " "):
				return command, cleaned_input[len(command):].split()

		return None, []

	@input_error
	def hello(self, _args: list[str]) -> tuple[str, bool]:
		return "How can I help you?", False

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

		self._save_contacts()
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
		self._save_contacts()
		return f"Birthday for {name} added.", False

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
		self._save_contacts()
		return f"Contact {name} changed.", False

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
		self._save_contacts()
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
		self._save_contacts()
		return f"Phone number {phone_number} removed from contact {name}.", False

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
	def search(self, args: list[str]) -> tuple[str, bool]:
		if len(args) != 1:
			raise ValueError("Usage: search <query>")

		query = args[0]
		results = self.book.search(query)

		if not results:
			return f"No contacts found for query: {query}", False

		return "\n".join(str(record) for record in results), False

	def exit_bot(self, _args: list[str]) -> tuple[str, bool]:
		return "Good bye!", True

	def run(self) -> None:
		print("Bot started. Type 'hello' to begin.")

		while True:
			user_input = input("Enter a command: ")

			if not user_input.strip():
				continue

			command, args = self.parse_command(user_input)

			if command is None:
				print(f"Unknown command. Available commands: {', '.join(self.commands.keys())}")
				continue

			command_handler = self.commands[command]
			message, should_exit = command_handler(args)

			print(message)

			if should_exit:
				break



