import functools
import json
from pathlib import Path
from models import AddressBook, Record


DATA_FILE = Path(__file__).resolve().parent / "contacts.json"


def load_contacts() -> AddressBook:
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


def save_contacts(data: AddressBook) -> None:
	temp_file = DATA_FILE.with_suffix(".tmp")


	with open(temp_file, "w", encoding="utf-8") as file:
		json.dump([record.to_dict() for record in data.values()], file, indent=4)

	temp_file.replace(DATA_FILE)


book = load_contacts()


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


def parse_command(user_input: str) -> tuple[str | None, list[str]]:
	cleaned_input = user_input.strip()
	lowered_input = cleaned_input.lower()

	for command in sorted(COMMANDS_LIST, key=len, reverse=True):
		if lowered_input == command or lowered_input.startswith(command + " "):
			return command, cleaned_input[len(command):].split()

	return None, []


@input_error
def hello(_args: list[str]) -> tuple[str, bool]:
	return "How can I help you?", False


@input_error
def add(args: list[str]) -> tuple[str, bool]:
	if len(args) != 2:
		raise ValueError("Usage: add <name> <phone>")

	name, phone_number = args

	record = book.find(name)
	if record is None:
		record = Record(name)
		record.add_phone(phone_number)
		book.add_record(record)
	else:
		record.add_phone(phone_number)

	save_contacts(book)
	return f"Contact {name} added.", False


@input_error
def add_birthday(args: list[str]) -> tuple[str, bool]:
	if len(args) != 2:
		raise ValueError("Usage: add_birthday <name> <DD.MM.YYYY>")

	name, birthday = args

	record = book.find(name)
	if record is None:
		raise KeyError

	record.add_birthday(birthday)
	save_contacts(book)
	return f"Birthday for {name} added.", False


@input_error
def birthday(args: list[str]) -> tuple[str, bool]:
	if len(args) != 1:
		raise ValueError("Usage: birthday <name>")

	name = args[0]

	record = book.find(name)
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
def change(args: list[str]) -> tuple[str, bool]:
	if len(args) != 3:
		raise ValueError("Usage: change <name> <old_phone> <new_phone>")

	name, old_number, new_number = args

	record = book.find(name)
	if record is None:
		raise KeyError

	record.edit_phone(old_number, new_number)
	save_contacts(book)
	return f"Contact {name} changed.", False


@input_error
def phone(args: list[str]) -> tuple[str, bool]:
	if len(args) != 1:
		raise ValueError("Usage: phone <name>")

	name = args[0]

	record = book.find(name)
	if record is None:
		raise KeyError

	return str(record), False


@input_error
def show_all(_args: list[str]) -> tuple[str, bool]:
	if not book.data:
		return "No contacts saved.", False

	return "\n".join(str(record) for record in book.data.values()), False


@input_error
def show_page(args: list[str]) -> tuple[str, bool]:
	if len(args) != 1:
		raise ValueError("Usage: show_page <page_size>")

	page_size = int(args[0])

	if not book.data:
		return "No contacts saved.", False

	pages = []
	for index, chunk in enumerate(book.iterator(page_size), start=1):
		page_text = "\n".join(str(record) for record in chunk)
		pages.append(f"Page {index}:\n{page_text}")

	return "\n\n".join(pages), False


@input_error
def delete_contact(args: list[str]) -> tuple[str, bool]:
	if len(args) != 1:
		raise ValueError("Usage: delete <name>")

	name = args[0]

	if book.find(name) is None:
		raise KeyError

	book.delete(name)
	save_contacts(book)
	return f"Contact {name} deleted.", False


@input_error
def remove_phone(args: list[str]) -> tuple[str, bool]:
	if len(args) != 2:
		raise ValueError("Usage: remove_phone <name> <phone>")

	name, phone_number = args

	record = book.find(name)
	if record is None:
		raise KeyError

	record.remove_phone(phone_number)
	save_contacts(book)
	return f"Phone number {phone_number} removed from contact {name}.", False


@input_error
def find_phone(args: list[str]) -> tuple[str, bool]:
	if len(args) != 2:
		raise ValueError("Usage: find_phone <name> <phone>")

	name, phone_number = args

	record = book.find(name)
	if record is None:
		raise KeyError

	found_phone = record.find_phone(phone_number)
	if found_phone is None:
		return f"Phone number {phone_number} not found in contact {name}.", False

	return f"{name}: {found_phone}", False


@input_error
def search(args: list[str]) -> tuple[str, bool]:
	if len(args) != 1:
		raise ValueError("Usage: search <query>")

	query = args[0]
	results = book.search(query)

	if not results:
		return f"No contacts found for query: {query}", False

	return "\n".join(f"{str(record)}" for record in results), False


def exit_bot(_args: list[str]) -> tuple[str, bool]:
	return "Good bye!", True


COMMANDS_LIST = {
	"hello": hello,
	"add": add,
	"add_birthday": add_birthday,
	"birthday": birthday,
	"change": change,
	"phone": phone,
	"show": show_all,
	"show_page": show_page,
	"delete": delete_contact,
	"remove_phone": remove_phone,
	"find_phone": find_phone,
	"search": search,
	"good bye": exit_bot,
	"close": exit_bot,
	"stop": exit_bot,
	"exit": exit_bot,
}


def main() -> None:
	print("Bot started. Type 'hello' to begin.")

	while True:
		user_input = input("Enter a command: ")

		if not user_input.strip():
			continue

		command, args = parse_command(user_input)

		if command is None:
			print(f"Unknown command. Available commands: {', '.join(COMMANDS_LIST.keys())}")
			continue

		command_handler = COMMANDS_LIST[command]
		message, should_exit = command_handler(args)

		print(message)

		if should_exit:
			break


if __name__ == "__main__":
	main()
