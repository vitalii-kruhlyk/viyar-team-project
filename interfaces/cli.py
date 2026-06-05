from collections.abc import Callable

from handlers import ContactHandler, TaskHandler
from interfaces.parser import parse_flags, split_input
from storage import JsonStorage


class CliBot:
    contacts: ContactHandler
    tasks: TaskHandler
    commands: dict[str, Callable]
    descriptions: dict[str, list[tuple[str, str]]]

    def __init__(self) -> None:
        self.contacts = ContactHandler(JsonStorage("contacts.json"))
        self.tasks = TaskHandler(JsonStorage("tasks.json"))

        self.commands = {
            "hello": self.hello,
            "help": self.help,
            "add": self.add,
            "edit": self.edit,
            "remove": self.remove,
            "delete": self.delete,
            "search": self.search,
            "show": self.show,
            "birthday": self.birthday,
            "status": self.status,
            "filter": self.filter,
            "exit": self.exit_bot,
        }
        self.descriptions = {
            "hello": [
                ("", "Greet the bot"),
            ],
            "help": [
                ("", "Show this help message"),
            ],
            "add": [
                (
                    "--contact  -n <name> [-p phones] [-e emails] [-b DD.MM.YYYY]",
                    "Create a new contact",
                ),
                ("--phone    -n <name> -p <phone1,phone2>", "Add phone(s) to contact"),
                ("--email    -n <name> -e <email1,email2>", "Add email(s) to contact"),
                ("--birthday -n <name> -b <DD.MM.YYYY>", "Set birthday for contact"),
                (
                    "--address  -n <name> "
                    "-country <X> -city <X> -street <X> -house <X>",
                    "Add address to contact",
                ),
                ("--task     -t <title> [-d <description>]", "Create a new task"),
            ],
            "edit": [
                (
                    "--phone     -n <name> -old <phone> -new <phone>",
                    "Change phone number",
                ),
                ("--email     -n <name> -old <email> -new <email>", "Change email"),
                (
                    "--address   -n <name> "
                    "-country <X> -city <X> -street <X> -house <X>",
                    "Change address",
                ),
                ("--task      -i <id> -t <new_title>", "Edit task title"),
                ("--task-desc -i <id> -d <new_description>", "Edit task description"),
            ],
            "remove": [
                ("--phone   -n <name> -p <phone>", "Remove phone from contact"),
                ("--email   -n <name> -e <email>", "Remove email from contact"),
                ("--address -n <name>", "Remove address from contact"),
            ],
            "delete": [
                ("--contact -n <name>", "Delete contact"),
                ("--task    -i <id>", "Delete task"),
            ],
            "search": [
                ("--contact -q <query>", "Search contacts by name, phone or email"),
                (
                    "--address [-country <X>] [-city <X>] [-street <X>] [-house X]",
                    "Search contacts by address",
                ),
                ("--task    -q <query>", "Search tasks by title or description"),
            ],
            "show": [
                ("--contacts -p <size>", "Show all contacts. Add -page for pagination"),
                ("--contact  -n <name>", "Show specific contact"),
                ("--tasks", "Show all tasks"),
            ],
            "birthday": [
                ("--contact -n <name>", "Show days until contact's birthday"),
            ],
            "status": [
                (
                    "--task -i <id> -s <status>",
                    "Change task status (new, in progress, done, cancelled)",
                ),
            ],
            "filter": [
                ("--task -s <status>", "Filter tasks by status"),
            ],
            "exit": [
                ("", "Exit the bot"),
            ],
        }

    def parse_command(
        self, user_input: str
    ) -> tuple[str | None, str | None, dict[str, str]]:
        tokens = split_input(user_input.strip())
        if not tokens:
            return None, None, {}

        command = tokens[0].lower()

        if command not in self.commands:
            return None, None, {}

        # Субкоманда — второй токен начинающийся с "--"
        subcommand = None
        flag_start = 1
        if len(tokens) > 1 and tokens[1].startswith("--"):
            subcommand = tokens[1].lower()
            flag_start = 2

        flags = parse_flags(tokens[flag_start:])
        return command, subcommand, flags

    @staticmethod
    def hello(_sub: str | None, _flags: dict[str, str]) -> tuple[str, bool]:
        return "How can I help you? Type 'help' to see all available commands.", False

    def help(self, _sub: str | None, _flags: dict[str, str]) -> tuple[str, bool]:
        lines = ["Available commands:", ""]
        for command, entries in self.descriptions.items():
            lines.append(command)
            for usage, description in entries:
                if usage:
                    lines.append(f"  {usage}")
                    lines.append(f"      {description}")
                else:
                    lines.append(f"      {description}")
            lines.append("")
        return "\n".join(lines), False

    def add(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contact":
            return self.contacts.add_contact(flags)
        if sub == "--phone":
            return self.contacts.add_phone(flags)
        if sub == "--email":
            return self.contacts.add_email(flags)
        if sub == "--birthday":
            return self.contacts.add_birthday(flags)
        if sub == "--address":
            return self.contacts.add_address(flags)
        if sub == "--task":
            return self.tasks.add_task(flags)
        raise ValueError(
            "Usage: add --contact | --phone | --email | --birthday | --address | --task"
        )

    def edit(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--phone":
            return self.contacts.change_phone(flags)
        if sub == "--email":
            return self.contacts.change_email(flags)
        if sub == "--address":
            return self.contacts.change_address(flags)
        if sub == "--task":
            return self.tasks.edit_task(flags)
        if sub == "--task-desc":
            return self.tasks.edit_task_desc(flags)
        raise ValueError(
            "Usage: edit --phone | --email | --address | --task | --task-desc"
        )

    def remove(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--phone":
            return self.contacts.remove_phone(flags)
        if sub == "--email":
            return self.contacts.remove_email(flags)
        if sub == "--address":
            return self.contacts.remove_address(flags)
        raise ValueError("Usage: remove --phone | --email | --address")

    def delete(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contact":
            return self.contacts.delete_contact(flags)
        if sub == "--task":
            return self.tasks.delete_task(flags)
        raise ValueError("Usage: delete --contact | --task")

    def search(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contact":
            return self.contacts.search(flags)
        if sub == "--address":
            return self.contacts.search_address(flags)
        if sub == "--task":
            return self.tasks.search_task(flags)
        raise ValueError("Usage: search --contact | --address | --task")

    def show(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contacts":
            return self.contacts.show_all(flags)
        if sub == "--contact":
            return self.contacts.show_one(flags)
        if sub == "--tasks":
            return self.tasks.show_tasks(flags)
        raise ValueError("Usage: show --contacts | --contact | --tasks")

    def birthday(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contact":
            return self.contacts.birthday(flags)
        raise ValueError("Usage: birthday --contact -n <name>")

    def status(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--task":
            return self.tasks.task_status(flags)
        raise ValueError("Usage: status --task -i <id> -s <status>")

    def filter(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--task":
            return self.tasks.tasks_by_status(flags)
        raise ValueError("Usage: filter --task -s <status>")

    @staticmethod
    def exit_bot(_sub: str | None, _flags: dict[str, str]) -> tuple[str, bool]:
        return "Good bye!", True

    def run(self) -> None:
        print("Bot started. Type 'hello' to begin.")

        while True:
            user_input = input("Enter a command: ")

            if not user_input.strip():
                continue

            try:
                command, subcommand, flags = self.parse_command(user_input)
            except ValueError as e:
                print(f"Input error: {e}")
                continue

            if command is None:
                print("Unknown command. Type 'help' to see all available commands.")
                continue

            try:
                message, should_exit = self.commands[command](subcommand, flags)
            except ValueError as e:
                print(f"Input error: {e}")
                continue

            print(message)
            if should_exit:
                break
