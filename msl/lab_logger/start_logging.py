from time import sleep
import sys
from datetime import datetime

from msl.equipment import Config

from .sensors import Sensor
from .validators import Validator
from .database import Database

# path, serial = sys.argv[1:]
path = r'C:\Users\rebecca.hawke\PycharmProjects\msl-lab-logger\msl\examples\lab_logger\ithx_config.xml'
serial = '8060940'
print(path, serial)

cfg = Config(path)
record = cfg.database().records(serial=serial)[0]

wait = cfg.value('wait', 60)

sensor = Sensor.find(cfg, record)
database = Database(cfg, sensor)

validators = []
validator_element = cfg.find('validators')
if validator_element:
    for val in validator_element.find('validator'):
        print(val)
        name = val.text
        kwargs = val.attrib
        validators += Validator.find(cfg, **kwargs)
print("validators", validators)

while True:

    while True:
        try:
            data = sensor.acquire()
            break
        except Exception as exc:
            print(exc)  # log what happened
            pass
        
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

    sleep(wait)
