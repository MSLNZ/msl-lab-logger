from __future__ import annotations

import re
from typing import TypeVar

from msl.equipment import Config
from msl.equipment import EquipmentRecord

from ..databases import DatabaseTypes


class Sensor:

    fields: dict[str, DatabaseTypes] = {}  # column name, data type

    def __init__(self, config: Config, record: EquipmentRecord) -> None:
        self.config = config
        self.record = record
        self.connection = record.connect()

    def acquire(self) -> tuple[float, ...]:
        raise NotImplementedError('Subclass should implement this')

    def reconnect(self) -> None:
        raise NotImplementedError('Subclass should implement this')

    @staticmethod
    def find(config: Config, record: EquipmentRecord) -> Sensor:
        for s in _sensors:
            if s.matches(record):
                return s.cls(config, record)
        raise ValueError(f'Cannot find sensor matching {record}')


class SensorMatcher:

    def __init__(self,
                 cls: type[Sensor],
                 manufacturer: str = None,
                 model: str = None,
                 flags: int = 0) -> None:
        self.cls = cls
        self.manufacturer = re.compile(manufacturer, flags=flags) if manufacturer else None
        self.model = re.compile(model, flags=flags) if model else None

    def matches(self, record: EquipmentRecord) -> bool:
        """Checks if `record` is a match.

        Args:
            record: The equipment record to check if the manufacturer
                and the model number are a match.

        Returns:
            Whether `record` is a match.
        """
        if not (self.manufacturer or self.model):
            return False
        if self.manufacturer and not self.manufacturer.search(record.manufacturer):
            return False
        if self.model and not self.model.search(record.model):
            return False
        return True


DecoratedSensor = TypeVar('DecoratedSensor', bound=Sensor)


def sensor(*, manufacturer: str = None, model: str = None, flags: int = 0):
    """A decorator to register a Sensor.

    Args:
        manufacturer: The name of the manufacturer. Can be a regex pattern.
        model: The model number of the equipment. Can be a regex pattern.
        flags: The flags to use to compile the regex patterns.
    """
    def decorate(cls: type[DecoratedSensor]) -> type[DecoratedSensor]:
        if not issubclass(cls, Sensor):
            raise TypeError(f'{cls} is not a subclass of {Sensor}')
        _sensors.append(SensorMatcher(cls, manufacturer, model, flags))
        #logger.debug(f'added {cls.__name__!r} to the sensor registry')
        return cls
    return decorate


_sensors: list[SensorMatcher] = []
