import functools


def input_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            return str(e) if str(e) else "Not found", False
        except ValueError as error:
            return str(error), False
        except IndexError:
            return "Enter user name", False
        except AttributeError as error:
            return str(error), False

    return wrapper
