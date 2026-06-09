import re
from collections.abc import Callable
from html import escape as _escape

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from handlers import ContactHandler, CurrencyService, NoteHandler, TaskHandler, WeatherService
from interfaces.completer import BotCompleter
from interfaces.lexer import BotLexer
from interfaces.parser import parse_flags, split_input
from storage import JsonStorage

_LABELS = "Contact name|phones|emails|address|birthday|tags"
_LABEL_RE = re.compile(rf"\b({_LABELS}):( *)(.*?)(?=,\s*(?:{_LABELS})\b|\n|$)")
_STATUS_RE = re.compile(r"\((new|in progress|done|cancelled)\)")
_STATUS_COLORS = {
    "new": "#4488ff",
    "in progress": "#ffaa00",
    "done": "#00aa00",
    "cancelled": "#888888",
}
_NOTE_TITLE_RE = re.compile(r"^(\[\d+\]) ([^:(]+):")
_TASK_TITLE_RE = re.compile(r"^(\[\d+\]) ([^(]+?) (?=\()")


def _colorize(message: str) -> str:
    lines = message.split("\n")
    result = []
    for line in lines:
        escaped = _escape(line)
        colorized = _NOTE_TITLE_RE.sub(
            lambda m: f"{m.group(1)} <title>{m.group(2)}</title>:",
            escaped,
        )
        colorized = _TASK_TITLE_RE.sub(
            lambda m: f"{m.group(1)} <title>{m.group(2).rstrip()}</title> ",
            colorized,
        )
        colorized = _LABEL_RE.sub(
            lambda m: (f"<success>{m.group(1)}:</success>" f"{m.group(2)}" f"<subcommand>{m.group(3)}</subcommand>"),
            colorized,
        )
        colorized = _STATUS_RE.sub(
            lambda m: f'<style fg="{_STATUS_COLORS[m.group(1)]}">({m.group(1)})</style>',
            colorized,
        )
        result.append(colorized)
    return "\n".join(result)


BOT_STYLE = Style.from_dict(
    {
        "command": "#ffaa00 bold",
        "subcommand": "#00aaaa",
        "flag": "#00aa00",
        "value": "#ffffff",
        "success": "#00aa00",
        "error": "#ff4444 bold",
        "info": "#888888",
        "prompt": "#888888",
        "title": "bold #ffffff",
    }
)


class CliBot:
    contacts: ContactHandler
    tasks: TaskHandler
    notes: NoteHandler
    weather: WeatherService
    currency: CurrencyService
    commands: dict[str, Callable]
    descriptions: dict[str, list[tuple[str, str]]]
    flag_descriptions: dict[str, str]

    def __init__(self) -> None:
        self.contacts = ContactHandler(JsonStorage("contacts.json"))
        self.notes = NoteHandler(JsonStorage("notes.json"))
        self.tasks = TaskHandler(JsonStorage("tasks.json"))
        self.weather = WeatherService()
        self.currency = CurrencyService()
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
                    "--contact  -n <name> [-p phone1,phone2] [-e email1,email2] [-b DD.MM.YYYY]",
                    "Create a new contact",
                ),
                ("--phone    -n <name> -p <phone1,phone2>", "Add phone(s) to contact"),
                ("--email    -n <name> -e <email1,email2>", "Add email(s) to contact"),
                ("--birthday -n <name> -b <DD.MM.YYYY>", "Set birthday for contact"),
                ("--address  -n <name> -country <X> -city <X> -street <X> -house <X>", "Add address to contact"),
                ("--favorite -n <name>", "Add contact to favorites"),
                ("--task     -t <title> [-d <description>]", "Create a new task"),
                ("--note     -t <title> -c <content>", "Create a new note"),
                ("--tag      -i <id> -t <tag> | -ai", "Add tag manually or auto-generate with AI"),
            ],
            "edit": [
                ("--phone     -n <name> -old <phone> -new <phone>", "Change phone number"),
                ("--email     -n <name> -old <email> -new <email>", "Change email"),
                ("--address   -n <name> -country <X> -city <X> -street <X> -house <X>", "Change address"),
                ("--task      -i <id> -t <new_title>", "Edit task title"),
                ("--task-desc -i <id> -d <new_description>", "Edit task description"),
                ("--note      -i <id> -c <new_content>", "Edit note content"),
            ],
            "remove": [
                ("--phone    -n <name> -p <phone>", "Remove phone from contact"),
                ("--email    -n <name> -e <email>", "Remove email from contact"),
                ("--address  -n <name>", "Remove address from contact"),
                ("--favorite -n <name>", "Remove contact from favorites"),
                ("--tag      -i <id> -t <tag>", "Remove tag from note"),
            ],
            "delete": [
                ("--contact -n <name>", "Delete contact"),
                ("--task    -i <id>", "Delete task"),
                ("--note    -i <id>", "Delete note"),
            ],
            "search": [
                ("--contact -q <query>", "Search contacts by name, phone or email"),
                ("--address [-country <X>] [-city <X>] [-street <X>] [-house <X>]", "Search contacts by address"),
                ("--task    -q <query>", "Search tasks by title or description"),
                ("--note    -q <query> [-ai]", "Search notes by content, or semantic search with AI"),
            ],
            "show": [
                ("--contacts  [-page <size>]", "Show all contacts. Add -page for pagination"),
                ("--contact   -n <name>", "Show specific contact"),
                ("--favorites", "Show all favorite contacts"),
                ("--tasks", "Show all tasks"),
                ("--notes", "Show all notes"),
                ("--note     -i <id> [-ai]", "Show note, or AI summary with -ai"),
                ("--currencies", "Gets the exchange rate for today"),
                ("--weather -city <name>", "Receives weather data for the city"),
            ],
            "birthday": [
                ("--upcoming -days <number>", "Show all contacts with birthday in next N days"),
            ],
            "status": [
                ("--task -i <id> -s <status>", "Change task status (new, in progress, done, cancelled)"),
            ],
            "filter": [
                ("--task -s <status>", "Filter tasks by status"),
                ("--note -t <tag>", "Filter notes by tag"),
            ],
            "exit": [
                ("", "Exit the bot"),
            ],
        }

        self.flag_descriptions = {
            "-n": "contact name",
            "-p": "phone number(s), comma-separated",
            "-e": "email(s), comma-separated",
            "-b": "birthday in DD.MM.YYYY",
            "-t": "title / tag",
            "-c": "content",
            "-d": "description",
            "-i": "id",
            "-q": "search query",
            "-s": "status: new | in progress | done | cancelled",
            "-old": "old value",
            "-new": "new value",
            "-days": "number of days",
            "-page": "page size",
            "-country": "country",
            "-city": "city",
            "-street": "street",
            "-house": "house number",
        }

    def parse_command(self, user_input: str) -> tuple[str | None, str | None, dict[str, str]]:
        tokens = split_input(user_input.strip())
        if not tokens:
            return None, None, {}

        command = tokens[0].lower()
        if command not in self.commands:
            return None, None, {}

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
        if sub == "--favorite":
            return self.contacts.add_to_favorites(flags)
        if sub == "--task":
            return self.tasks.add_task(flags)
        if sub == "--note":
            return self.notes.add_note(flags)
        if sub == "--tag":
            if "-ai" in flags:
                return self.notes.ai_tags(flags)
            return self.notes.add_tag(flags)
        return (
            "Usage: add --contact | --phone | --email | --birthday | --address | --favorite | --task | --note | --tag",
            False,
        )

    def edit(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--phone":
            return self.contacts.edit_phone(flags)
        if sub == "--email":
            return self.contacts.edit_email(flags)
        if sub == "--address":
            return self.contacts.edit_address(flags)
        if sub == "--task":
            return self.tasks.edit_task(flags)
        if sub == "--task-desc":
            return self.tasks.edit_task_desc(flags)
        if sub == "--note":
            return self.notes.edit_note(flags)
        return "Usage: edit --phone | --email | --address | --task | --task-desc | --note", False

    def remove(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--phone":
            return self.contacts.remove_phone(flags)
        if sub == "--email":
            return self.contacts.remove_email(flags)
        if sub == "--address":
            return self.contacts.remove_address(flags)
        if sub == "--favorite":
            return self.contacts.remove_from_favorites(flags)
        if sub == "--tag":
            return self.notes.remove_tag(flags)
        return "Usage: remove --phone | --email | --address | --favorite | --tag", False

    def delete(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contact":
            return self.contacts.delete_contact(flags)
        if sub == "--task":
            return self.tasks.delete_task(flags)
        if sub == "--note":
            return self.notes.delete_note(flags)
        return "Usage: delete --contact | --task | --note", False

    def search(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contact":
            return self.contacts.search(flags)
        if sub == "--address":
            return self.contacts.search_address(flags)
        if sub == "--task":
            return self.tasks.search_task(flags)
        if sub == "--note":
            if "-ai" in flags:
                return self.notes.ai_search(flags)
            return self.notes.search_note(flags)
        return "Usage: search --contact | --address | --task | --note", False

    def show(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--contacts":
            return self.contacts.show_all(flags)
        if sub == "--contact":
            return self.contacts.show_one(flags)
        if sub == "--favorites":
            return self.contacts.show_favorites(flags)
        if sub == "--tasks":
            return self.tasks.show_tasks(flags)
        if sub == "--notes":
            return self.notes.show_notes(flags)
        if sub == "--note":
            if "-ai" in flags:
                return self.notes.ai_summary(flags)
            return self.notes.show_note(flags)
        if sub == "--weather":
            return self.weather.get_weather(flags)
        if sub == "--currencies":
            return self.currency.get_currency_rate(flags)
        raise ValueError(
            "Usage: show --contacts | --contact | --favorites | --tasks | --notes | --weather | --currencies"
        )

    def birthday(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--upcoming":
            return self.contacts.birthday(flags)
        return "Usage: birthday --upcoming -days <number>", False

    def status(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--task":
            return self.tasks.set_status(flags)
        return "Usage: status --task -i <id> -s <status>", False

    def filter(self, sub: str | None, flags: dict[str, str]) -> tuple[str, bool]:
        if sub == "--task":
            return self.tasks.filter_by_status(flags)
        if sub == "--note":
            return self.notes.filter_by_tag(flags)
        return "Usage: filter --task | --note", False

    @staticmethod
    def exit_bot(_sub: str | None, _flags: dict[str, str]) -> tuple[str, bool]:
        return "Good bye!", True

    @staticmethod
    def _print(message: str, style: str = "success") -> None:
        is_error = any(
            message.lower().startswith(prefix) for prefix in ("error", "not found", "usage:", "input error", "no ")
        )
        if is_error:
            print_formatted_text(HTML(f"<error>{_escape(message)}</error>"), style=BOT_STYLE)
        else:
            print_formatted_text(HTML(_colorize(message)), style=BOT_STYLE)

    def run(self) -> None:
        try:
            session: PromptSession = PromptSession(
                completer=BotCompleter(self.descriptions, self.flag_descriptions),
                auto_suggest=AutoSuggestFromHistory(),
                lexer=BotLexer(),
                style=BOT_STYLE,
            )

            def prompt() -> str:
                return session.prompt(HTML("\n<prompt>Enter a command: </prompt>"))

        except (OSError, RuntimeError):

            def prompt() -> str:
                return input("Enter a command: ")

        print_formatted_text(HTML("<info>Bot started. Type 'hello' to begin.</info>"), style=BOT_STYLE)
        while True:
            try:
                user_input = prompt()
            except (EOFError, KeyboardInterrupt):
                print_formatted_text(HTML("<info>Good bye!</info>"), style=BOT_STYLE)
                break

            if not user_input.strip():
                continue

            try:
                command, subcommand, flags = self.parse_command(user_input)
            except ValueError as e:
                print_formatted_text(HTML(f"<error>Input error: {e}</error>"), style=BOT_STYLE)
                continue

            if command is None:
                print_formatted_text(
                    HTML("<error>Unknown command. Type 'help' to see all available commands.</error>"),
                    style=BOT_STYLE,
                )
                continue

            try:
                message, should_exit = self.commands[command](subcommand, flags)
            except ValueError as e:
                print_formatted_text(HTML(f"<error>Input error: {e}</error>"), style=BOT_STYLE)
                continue

            self._print(message)
            if should_exit:
                break
