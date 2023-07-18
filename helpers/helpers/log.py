from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T", bound=Callable[..., any])


# Note that helpers can't be used in production if you wanted to, since they're not built and shipped
# so using 'print' is fine here
def log(msg: str) -> Callable[[T], T]:
    """
    Args:
        msg: String containing the names of function arguments to log. The result can be logged
             using the  __result__ reserved term.

    Example:
        @log("This is an example with inputs '{foo}' and output '{__result__}')
        def f(foo: str):
            return "WORLD"

        >>> f("hello")
        <<< This is an example with inputs 'hello' and output 'WORLD'
    """

    def decorator(fn: T) -> T:
        @wraps(fn)
        def wrapper(*args: tuple[any, ...], **kwargs: any) -> any:
            if args:
                raise ValueError(
                    "@log is only valid on functions called with keyword arguments."
                )

            __result__ = fn(**kwargs)
            print(msg.format(__result__=__result__, **kwargs))  # noqa: T201
            return __result__

        return wrapper

    return decorator
