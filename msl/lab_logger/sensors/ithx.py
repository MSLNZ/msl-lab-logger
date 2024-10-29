import re

import numpy as np
from msl.equipment import Config
from msl.equipment import EquipmentRecord
from . import Sensor
from . import sensor
from ..database import DatabaseTypes


@sensor(manufacturer=r'OMEGA', model=r'iTHX-[2DMSW][3D]?', flags=re.IGNORECASE)
class iTHX(Sensor):

    def __init__(self, config: Config, record: EquipmentRecord) -> None:
        super().__init__(config, record)

        props = record.connection.properties
        self.nprobes = props.get('nprobes', 1)
        self.nbytes = props.get('nbytes', None)
        self.celsius = props.get('celsius', True)

    def acquire(self) -> tuple[float, ...]:
        with self.record.connect() as cxn:
            data = cxn.temperature_humidity_dewpoint(probe=1, celsius=self.celsius, nbytes=self.nbytes)
            if self.nprobes == 2:
                data += cxn.temperature_humidity_dewpoint(probe=2, celsius=self.celsius, nbytes=self.nbytes)
            return data

    @property
    def fields(self) -> dict[str, DatabaseTypes]:
        if self.nprobes == 2:
            return {
                'temperature1': DatabaseTypes.FLOAT,
                'humidity1': DatabaseTypes.FLOAT,
                'dewpoint1': DatabaseTypes.FLOAT,
                'temperature2': DatabaseTypes.FLOAT,
                'humidity2': DatabaseTypes.FLOAT,
                'dewpoint2': DatabaseTypes.FLOAT,
            }

        return {
            'temperature': DatabaseTypes.FLOAT,
            'humidity': DatabaseTypes.FLOAT,
            'dewpoint': DatabaseTypes.FLOAT,
        }

    def apply_calibration(self, data_values: np.array) -> np.array:
        # numpy structured array with fields as names
        # also needs to include datetime for readings
        # calibration information comes from the equipment record; we know here it's an equation
        # get appropriate equation for equipment id, measurand, component, date, value

        pass
