import functools
import warnings


def deprecated(message: str):
    def decorator(func):
        """
        This decorator will result in a warning appearing when used
        """

        @functools.wraps(func)
        def new_func(*args, **kwargs):
            warnings.simplefilter("always", DeprecationWarning)  # turn off filter
            warnings.warn(
                "Call to deprecated function {}. {}".format(func.__name__, message),
                category=DeprecationWarning,
                stacklevel=2,
            )
            warnings.simplefilter("default", DeprecationWarning)  # reset filter
            return func(*args, **kwargs)

        return new_func

    return decorator
