""" Validators:
    simple-range (ensures all data values within the same range)
    send-email (sends email if simple-range fails)
    ithx-range-checker (different bounds for each type of data from iTHX sensors)
    ithx-with-reset (resets iTHX sensor if ithx-range-checker fails too many times)
"""
from ..sensors import Sensor

from . import Validator
from . import validator


# The validator name is specified in a configuration file as the text of an XML element
# and the attributes of the element are used as keyword arguments for the
# Validator. For example, to use the ithxRangeChecker validator you could include
# the following in your config.xml file:
#
#   <validator tmax="40" dmax="15">ithx-range-checker</validator>
#
# to change the default values to use for the maximum temperature and the
# maximum dew point.


@validator(name='simple-range')
class simpleRange(Validator):
    """
    A callback that is used to validate the data. Data is a tuple of values with the same acceptance range.
    The callback must return a value whose truthness decides whether to insert the data into the database.
    If the returned value evaluates to True then the data is inserted into the database.
    """
    def __init__(self, sensor: Sensor, vmin=10, vmax=30, **kwargs):
        super().__init__(sensor, **kwargs)
        """Validates the data by verifying that it is within a certain range.

        Parameters
        ----------
        vmin : :class:`float`, optional
            The minimum value allowed.
        vmax : :class:`float`, optional
            The maximum value allowed.
        kwargs
            Anything else is ignored.
        """
        self.vmin = float(vmin)
        self.vmax = float(vmax)

    def validate(self, data):
        fields = self.sensor.fields.keys()
        flag = True  # assume the data is okay to insert into the database
        for f, v in zip(fields, data):
            if not (self.vmin <= v <= self.vmax):
                self.log_warning(
                    f'{f} value of {v} is out of range [{self.vmin}, {self.vmax}] for {self.sensor.record.alias}'
                )
                flag = False  # the data is not okay to insert into the database

        return flag


@validator(name='send-email')
class sendEmail(Validator):
    """
    A callback that is used to validate the data. Data is a tuple of values with the same acceptance range.
    The callback must return a value whose truthness decides whether to insert the data into the database.
    If the returned value evaluates to True then the data is inserted into the database. If False, then the data is
    ignored and an email is sent with a warning message.
    """
    def __init__(self, sensor: Sensor, **kwargs):
        super().__init__(sensor, **kwargs)

        self.simplerange = simpleRange(sensor, **kwargs)

    def validate(self, data):
        if not self.simplerange.validate(data):
            self.send_email(
                body=f'Received {data} from {self.sensor.record.alias}'
            )


@validator(name='ithx-range-checker')  # existing code uses simple-range
class ithxRangeChecker(Validator):
    """
    A callback that is used to validate the data. Data is a tuple of the temperature, humidity and dewpoint values for
    each probe. The callback must return a value whose truthness decides whether to insert the data into the database.
    If the returned value evaluates to True then the data is inserted into the database.
    """
    def __init__(self, sensor: Sensor, tmin=10, tmax=30, hmin=10, hmax=90, dmin=0, dmax=20, **kwargs):
        super().__init__(sensor, **kwargs)
        """Validates the data by verifying that it is within a certain range.

        Parameters
        ----------
        tmin : :class:`float`, optional
            The minimum temperature value allowed.
        tmax : :class:`float`, optional
            The maximum temperature value allowed.
        hmin : :class:`float`, optional
            The minimum humidity value allowed.
        hmax : :class:`float`, optional
            The maximum humidity value allowed.
        dmin : :class:`float`, optional
            The minimum dew point value allowed.
        dmax : :class:`float`, optional
            The maximum dew point value allowed.
        kwargs
            Anything else is ignored.
        """
        self.tmin = float(tmin)
        self.tmax = float(tmax)
        self.hmin = float(hmin)
        self.hmax = float(hmax)
        self.dmin = float(dmin)
        self.dmax = float(dmax)

    def validate(self, data):
        if len(data) == 3:
            t1, h1, d1 = data
            temperatures = [t1]
            humidities = [h1]
            dewpoints = [d1]
        else:
            t1, h1, d1, t2, h2, d2 = data
            temperatures = [t1, t2]
            humidities = [h1, h2]
            dewpoints = [d1, d2]

        for t in temperatures:
            if not (self.tmin <= t <= self.tmax):
                self.log_warning(
                    f'Temperature value of {t} is out of range [{self.tmin}, {self.tmax}] for {self.sensor.record.alias}'
                )
                return False

        for h in humidities:
            if not (self.hmin <= h <= self.hmax):
                self.log_warning(
                    f'Humidity value of {h} is out of range [{self.hmin}, {self.hmax}] for {self.sensor.record.alias}'
                )
                return False

        for d in dewpoints:
            if not (self.dmin <= d <= self.dmax):
                self.log_warning(
                    f'Dewpoint value of {d} is out of range [{self.dmin}, {self.dmax}] for {self.sensor.record.alias}'
                )
                return False

        # the data is okay, return True to insert the data into the database
        return True


@validator(name='ithx-with-reset')
class ithxWithReset(Validator):

    def __init__(self, sensor: Sensor, reset_criterion=5, **kwargs):
        super().__init__(sensor, **kwargs)
        """Reset the iServer after a certain number of invalid data values.

        Parameters
        ----------
        reset_criterion : :class:`int`, optional
            The maximum number of times that the data can fall outside of
            the specified range before resetting the iServer.
        kwargs
            All additional keyword arguments are passed to
            :class:`.SimpleRange`.
        """
        self.counter = 0
        self.reset_criterion = int(reset_criterion)

        self.simplerange = ithxRangeChecker(sensor, **kwargs)

    def validate(self, data):

        if self.simplerange.validate(data):
            return True

        self.counter += 1

        if self.counter >= self.reset_criterion:
            self.log_warning(
                f'The {self.sensor.record.alias} Omega iServer will reset due to {self.reset_criterion} bad readings.'
            )
            with self.sensor.record.connect() as cxn:
                cxn.reset(wait=True, password=None, port=2002, timeout=10)
            self.counter = 0

        return False

