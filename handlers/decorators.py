import functools


def input_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            msg = e.args[0] if e.args else "Not found"
            return str(msg) if msg else "Not found", False
        except ValueError as error:
            return str(error), False

    return wrapper
