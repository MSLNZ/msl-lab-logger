from __future__ import annotations

from typing import TypeVar, Sequence

from msl.io import send_email

from ..sensors import Sensor
from ..log import logger


class Validator:
    """
    A Validator validates the data before the data is inserted into a database.
    All custom-written validators should inherit from the :class:`.Validator` class
    and override the :meth:`~.Validator.validate` method.
    """
    name = ""

    def __init__(self, sensor: Sensor, **kwargs) -> None:
        self.config = sensor.config
        self.sensor = sensor

    def validate(self, data: Sequence[float], ) -> bool:
        raise NotImplementedError('Subclass should implement this')

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
            logger.exception(e)

    @staticmethod
    def find(sensor: Sensor, name: str, **kwargs) -> Validator:
        for v in _validators:
            if v.matches(name):
                val = v.cls(sensor, **kwargs)
                val.name = name
                return val
        raise ValueError(f'Cannot find validator matching {name}')

    @staticmethod
    def log_debug(msg, *args, **kwargs):
        """Log a debug message.

        All input parameters are passed to :meth:`~logging.Logger.debug`.
        """
        logger.debug(msg, *args, **kwargs)

    @staticmethod
    def log_info(msg, *args, **kwargs):
        """Log an info message.

        All input parameters are passed to :meth:`~logging.Logger.info`.
        """
        logger.info(msg, *args, **kwargs)

    @staticmethod
    def log_warning(msg, *args, **kwargs):
        """Log a warning message.

        All input parameters are passed to :meth:`~logging.Logger.warning`.
        """
        logger.warning(msg, *args, **kwargs)

    @staticmethod
    def log_error(msg, *args, **kwargs):
        """Log an error message.

        All input parameters are passed to :meth:`~logging.Logger.error`.
        """
        logger.error(msg, *args, **kwargs)

    @staticmethod
    def log_critical(msg, *args, **kwargs):
        """Log a critical message.

        All input parameters are passed to :meth:`~logging.Logger.critical`.
        """
        logger.critical(msg, *args, **kwargs)


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

from .range_checker import *
