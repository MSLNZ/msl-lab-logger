import re
from msl.equipment import Config
from msl.equipment import EquipmentRecord
from . import Sensor
from . import sensor
from ..database import DatabaseTypes


@sensor(manufacturer='IsoTech', model='milliK', flags=re.IGNORECASE)
class milliK(Sensor):

    def __init__(self, config: Config, record: EquipmentRecord) -> None:
        super().__init__(config, record)
        self.is_prt = True
        self.channel = self.connection.properties['channel']

    def acquire(self) -> tuple[float, ...]:
        with self.record.connect() as cxn:
            return cxn.read_all_channels()

    @property
    def fields(self) -> dict[str, DatabaseTypes]:
        dict = {}
        for channel in self.connected_devices:
            dict[channel] = DatabaseTypes.FLOAT

        return dict
