from time import sleep
import sys

from msl.equipment import Config

from .sensors import Sensor
from .validators import Validator
from .databases import Database

path, serial = sys.argv[1:]

cfg = Config(path)
record = cfg.database().records(serial=serial)[0]

sensor = Sensor.find(cfg, record)
database = Database(cfg.value('log_dir'), sensor.fields)
validators = Validator.find(cfg)

while True:

    while True:
        try:
            data = sensor.acquire()
            break
        except ConnectionError:
            sensor.reconnect()

    add_it = True
    for validator in validators:
        if not validator.validate(data):
            add_it = False
            break

    if add_it:
        database.write(*data)

    sleep(60)
