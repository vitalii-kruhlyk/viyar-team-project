import shlex


def parse_flags(raw_args: list[str]) -> dict[str, str]:
    """
    Парсит список аргументов в словарь флагов.
    Один флаг — одно значение. Повторный флаг — ошибка.

    Пример:
        ["-n", "John Dou", "-p", "+380961234567,+380671234567"]
        → {"-n": "John Dou", "-p": "+380961234567,+380671234567"}
    """
    result: dict[str, str] = {}
    i = 0
    while i < len(raw_args):
        token = raw_args[i]
        if token.startswith("-"):
            if token in result:
                raise ValueError(
                    f"Flag '{token}' specified more than once. "
                    "Use comma-separated values instead: -p +380960000000,+380670000000"
                )
            if i + 1 < len(raw_args) and not raw_args[i + 1].startswith("-"):
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
