from collections.abc import Callable

from handlers import ContactHandler, TaskHandler, NoteHandler, WeatherService
from storage import JsonStorage


class CliBot:
    contacts: ContactHandler
    tasks: TaskHandler
    notes: NoteHandler
    api: WeatherService
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]
    descriptions: dict[str, str]

    def __init__(self) -> None:
        self.contacts = ContactHandler(JsonStorage("contacts.json"))
        self.notes = NoteHandler(JsonStorage("notes.json"))
        self.tasks = TaskHandler(JsonStorage("tasks.json"))
        self.api = WeatherService()
        self.commands = {
            **self.contacts.commands,
            **self.notes.commands,
            "hello": self.hello,
            "help": self.help,
            **self.contacts.commands,
            **self.tasks.commands,
            **self.api.commands,
            "exit": self.exit_bot,
        }
        self.descriptions = {
            "hello": "Greet the bot",
            "help": "Show all available commands with descriptions",
            **self.contacts.descriptions,
            **self.tasks.descriptions,
            "exit": "Exit the bot",
        }

    def parse_command(self, user_input: str) -> tuple[str | None, list[str]]:
        cleaned_input = user_input.strip()
        lowered_input = cleaned_input.lower()

        for command in sorted(self.commands, key=len, reverse=True):
            if lowered_input == command or lowered_input.startswith(command + " "):
                return command, cleaned_input[len(command) :].split()

        return None, []

    @staticmethod
    def hello(_args: list[str]) -> tuple[str, bool]:
        return "How can I help you? Type 'help' to see all available commands.", False

    def help(self, _args: list[str]) -> tuple[str, bool]:
        lines = ["Available commands:", ""]
        for command, description in self.descriptions.items():
            lines.append(f"  {command:<20} — {description}")
        return "\n".join(lines), False

    @staticmethod
    def exit_bot(_args: list[str]) -> tuple[str, bool]:
        return "Good bye!", True

    def run(self) -> None:
        print("Bot started. Type 'hello' to begin.")

        while True:
            user_input = input("Enter a command: ")

            if not user_input.strip():
                continue

            command, args = self.parse_command(user_input)

            if command is None:
                print("Unknown command. Type 'help' to see all available commands.")
                continue

            command_handler = self.commands[command]
            message, should_exit = command_handler(args)

            print(message)

            if should_exit:
                break
