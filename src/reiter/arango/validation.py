import pydantic
from functools import wraps
from horseman.response import Response


class ValidationError(Response, Exception):
    pass


def catch_pydantic_exception(func):
    @wraps(func)
    def exceptions_catcher(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pydantic.ValidationError as exc:
            error = {
                'type': 'Model validation',
                'name': f'{exc.model.__module__}.{exc.model.__name__}',
                'errors': exc.errors()
            }
            raise ValidationError.to_json(400, error)
    return exceptions_catcher
