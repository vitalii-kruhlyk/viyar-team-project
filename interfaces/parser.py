import shlex


def _is_flag(token: str) -> bool:
    """Returns True if token is a flag (starts with - but is not a negative number)."""
    if not token.startswith("-"):
        return False
    rest = token[1:]
    if not rest:
        return False
    # "-5", "-3.14" — это числа, а не флаги
    try:
        float(rest)
        return False
    except ValueError:
        return True


def parse_flags(raw_args: list[str]) -> dict[str, str]:
    """
    Парсит список аргументов в словарь флагов.
    Один флаг — одно значение. Повторный флаг — ошибка.
    Отрицательные числа (например -5) не считаются флагами.

    Пример:
        ["-n", "John Dou", "-p", "+380961234567,+380671234567"]
        → {"-n": "John Dou", "-p": "+380961234567,+380671234567"}
    """
    result: dict[str, str] = {}
    i = 0
    while i < len(raw_args):
        token = raw_args[i]
        if _is_flag(token):
            if token in result:
                raise ValueError(
                    f"Flag '{token}' specified more than once. "
                    "Use comma-separated values instead: -p +380960000000,+380670000000"
                )
            if i + 1 < len(raw_args) and not _is_flag(raw_args[i + 1]):
                result[token] = raw_args[i + 1]
                i += 2
            else:
                raise ValueError(f"Flag '{token}' requires a value")
        else:
            i += 1
    return result


def split_values(value: str) -> list[str]:
    """
    Разбивает строку значений по запятой.

    Пример:
        "+380961234567, +380671234567"
        → ["+380961234567", "+380671234567"]
    """
    return [v.strip() for v in value.split(",") if v.strip()]


def split_input(user_input: str) -> list[str]:
    """
    Разбивает строку ввода с учетом кавычек.

    Пример:
        'add --contact -n "John Dou" -p +380961234567'
        → ["add", "--contact", "-n", "John Dou", "-p", "+380961234567"]
    """
    try:
        return shlex.split(user_input)
    except ValueError:
        return user_input.split()
