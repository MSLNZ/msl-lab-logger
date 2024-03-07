import time
import sys
from datetime import datetime
import traceback

from msl.equipment import Config

from .sensors import Sensor
from .validators import Validator
from .database import Database

from .log import logger


# path, serial = sys.argv[1:]
path = r'C:\Users\rebecca.hawke\PycharmProjects\msl-lab-logger\msl\examples\lab_logger\ithx_config.xml'
serial = '8060940'
print(path, serial)

cfg = Config(path)
record = cfg.database().records(serial=serial)[0]

wait = cfg.value('wait', 60)

sensor = Sensor.find(cfg, record)
database = Database(sensor)

validators = []
validator_element = cfg.find('validators')
if validator_element:
    for val in validator_element:
        name = val.text
        kwargs = val.attrib
        validators.append(Validator.find(sensor, name, **kwargs))
print("validators", validators)

while True:
    try:
        t0 = time.monotonic()

        while True:
            try:
                data = sensor.acquire()
                logger.info(f'{sensor.record.alias} readings: {data}')
                break
            except Exception as exc:
                logger.exception(exc)  # log what happened

        timestamp = datetime.now().replace(microsecond=0).isoformat(sep='T')

        add_it = True
        for validator in validators:
            if not validator.validate(data):
                add_it = False
                break

        if add_it:
            results = [timestamp]
            results.extend(data)
            database.write(results)

        dt = time.monotonic() - t0
        time.sleep(max(0, wait - dt))

    except:
        traceback.print_exc(file=sys.stderr)
        input('Press <ENTER> to close ...')
