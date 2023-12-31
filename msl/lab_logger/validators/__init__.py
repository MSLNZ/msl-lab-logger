from typing import TypeVar

from msl.equipment import Config
from msl.io import send_email


class Validator:

    def __init__(self, config: Config, **kwargs) -> None:
        self.config = config

    def validate(self, *data) -> bool:
        return True

    def send_email(self,
                   body: str,
                   *,
                   subject: str = '[MSL-Lab-Logger] Validator warning') -> bool:
        smtp = self.config.find('smtp')
        if smtp is None:
            return False
        settings = smtp.find('settings')
        if settings is None:
            return False
        recipients = smtp.findall('recipients')
        if recipients is None:
            return False

        try:
            send_email(settings, recipients, sender=None, subject=subject, body=body)
        except Exception as e:
            pass
            # log.exception(e)


class ValidatorMatcher:

    def __init__(self,
                 cls: type[Validator],
                 name: str) -> None:
        self.cls = cls
        self.name = name.lower()

    def matches(self, name) -> bool:
        """Checks if `name` is a match.

        Args:
            name:

        Returns:
            Whether `name` is a match.
        """
        return name.lower() == self.name


DecoratedValidator = TypeVar('DecoratedValidator', bound=Validator)


def validator(name: str):
    """A decorator to register a validator.

    Args:
        name: The name of the validator, e.g. range-checker
    """
    def decorate(cls: type[DecoratedValidator]) -> type[DecoratedValidator]:
        if not issubclass(cls, Validator):
            raise TypeError(f'{cls} is not a subclass of {Validator}')
        _validators.append(ValidatorMatcher(cls, name))
        #logger.debug(f'added {cls.__name__!r} to the validator registry')
        return cls
    return decorate


_validators: list[ValidatorMatcher] = []
