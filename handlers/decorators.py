import functools


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
