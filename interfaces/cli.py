from collections.abc import Callable

from handlers import ContactHandler
from storage import JsonStorage


class CliBot:
    contacts: ContactHandler
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

    def __init__(self) -> None:
        self.contacts = ContactHandler(JsonStorage("contacts.json"))
        self.commands = {
            **self.contacts.commands,
            "hello": self.hello,
            "good bye": self.exit_bot,
            "close": self.exit_bot,
            "stop": self.exit_bot,
            "exit": self.exit_bot,
        }

    def parse_command(self, user_input: str) -> tuple[str | None, list[str]]:
        cleaned_input = user_input.strip()
        lowered_input = cleaned_input.lower()

        for command in sorted(self.commands, key=len, reverse=True):
            if lowered_input == command or lowered_input.startswith(command + " "):
                return command, cleaned_input[len(command) :].split()

        return None, []

    def hello(self, _args: list[str]) -> tuple[str, bool]:
        return "How can I help you?", False

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
                available = ", ".join(self.commands.keys())
                print(f"Unknown command. Available commands: {available}")
                continue

            command_handler = self.commands[command]
            message, should_exit = command_handler(args)

            print(message)

            if should_exit:
                break
