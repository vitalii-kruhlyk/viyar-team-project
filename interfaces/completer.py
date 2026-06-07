import re
from typing import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document


class BotCompleter(Completer):
    _commands: list[str]
    _subcommands: dict[str, list[str]]
    _flags: dict[tuple[str, str], list[str]]
    _flag_descriptions: dict[str, str]

    def __init__(self, descriptions: dict[str, list[tuple[str, str]]], flag_descriptions: dict[str, str]) -> None:
        self._commands: list[str] = list(descriptions.keys())
        self._flag_descriptions = flag_descriptions

        self._subcommands: dict[str, list[str]] = {}

        self._flags: dict[tuple[str, str], list[str]] = {}

        for command, entries in descriptions.items():
            subs = []
            for usage, _ in entries:
                if not usage:
                    continue
                tokens = usage.split()
                if not tokens:
                    continue

                sub = tokens[0]
                if sub not in subs:
                    subs.append(sub)

                flags = [t for t in tokens[1:] if re.match(r"^-[^-]", t)]
                key = (command, sub)
                if key not in self._flags:
                    self._flags[key] = []
                for flag in flags:
                    if flag not in self._flags[key]:
                        self._flags[key].append(flag)

            self._subcommands[command] = subs

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        text = document.text_before_cursor
        tokens = text.split()

        ends_with_space = text.endswith(" ")

        # 1. Complete command
        if not tokens or (len(tokens) == 1 and not ends_with_space):
            partial = tokens[0] if tokens else ""
            for cmd in self._commands:
                if cmd.startswith(partial):
                    yield Completion(cmd, start_position=-len(partial), display_meta="command")
            return

        command = tokens[0].lower()
        if command not in self._subcommands:
            return

        # 2. Complete subcommand
        if len(tokens) == 1 and ends_with_space:
            for sub in self._subcommands[command]:
                yield Completion(sub, display_meta="subcommand")
            return

        if len(tokens) == 2 and not ends_with_space:
            partial = tokens[1]
            for sub in self._subcommands[command]:
                if sub.startswith(partial):
                    yield Completion(sub, start_position=-len(partial), display_meta="subcommand")
            return

        # 3. Complete flags
        if len(tokens) >= 2:
            sub = tokens[1].lower() if tokens[1].startswith("--") else None
            if sub is None:
                return

            available_flags: list[str] = self._flags.get((command, sub), [])
            used_flags = {t for t in tokens[2:] if t.startswith("-")}
            remaining = [f for f in available_flags if f not in used_flags]
            if ends_with_space:
                last = tokens[-1]
                if last.startswith("-") and not last.startswith("--"):
                    return
                for flag in remaining:
                    yield Completion(flag, display_meta=self._flag_descriptions.get(flag, "flag"))
            else:
                partial = tokens[-1]
                if not partial.startswith("-"):
                    return
                for flag in remaining:
                    if flag.startswith(partial):
                        yield Completion(
                            flag,
                            start_position=-len(partial),
                            display_meta=self._flag_descriptions.get(flag, "flag"),
                        )
