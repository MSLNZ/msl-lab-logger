import re
from msl.equipment import Config
from msl.equipment import EquipmentRecord
from . import Sensor
from . import sensor
from ..database import DatabaseTypes


@sensor(manufacturer='Vaisala', model='PTU300', flags=re.IGNORECASE)
class PTU300(Sensor):

    def __init__(self, config: Config, record: EquipmentRecord) -> None:
        super().__init__(config, record)

        desired_units = {
            "P": 'hPa',
            "T": "ºC",
            "RH": "%RH",
        }

        desired_format = '4.3 P " " 3.3 T " " 3.3 RH #r #n'

        with self.record.connect() as cxn:
            cxn.set_units(desired_units=desired_units)
            self.sensor_units = cxn.units
            cxn.set_format(format=desired_format)

    def acquire(self) -> tuple[float, ...]:
        with self.record.connect() as cxn:
            rdgstr = cxn.get_reading_str()
            return tuple(map(float, rdgstr.split()))

    @property
    def fields(self) -> dict[str, DatabaseTypes]:
        return {key: DatabaseTypes.FLOAT for key in self.sensor_units}
