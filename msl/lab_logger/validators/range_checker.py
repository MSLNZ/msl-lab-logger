from msl.equipment import Config

from . import Validator
from . import validator


# The validator name is specified in a configuration file as the text of an XML element
# and the attributes of the element are used as keyword arguments for the
# Validator. For example, to use the ithxRangeChecker validator you could include
# the following in your config.xml file:
#
#   <validator tmax="40" dmax="15">simple-range</validator>
#
# to change the default values to use for the maximum temperature and the
# maximum dew point.


@validator(name='ithx-range-checker')  # existing code uses simple-range
class ithxRangeChecker(Validator):
    """
    A callback that is used to validate the data. The callback must accept two arguments (data, ithx), where data is a
    tuple of the temperature, humidity and dewpoint values for each probe and ithx is the iTHX instance (i.e., self).
    The callback must return a value whose truthness decides whether to insert the data into the database.
    If the returned value evaluates to True then the data is inserted into the database.
    """

    def __init__(self, config, tmin=10, tmax=30, hmin=10, hmax=90, dmin=0, dmax=20, **kwargs):
        super().__init__(config, **kwargs)
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

    def validate(self, data, ithx):
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
                ithx.log_warning(
                    f'Temperature value of {t} is out of range [{self.tmin}, {self.tmax}]'
                )
                return False

        for h in humidities:
            if not (self.hmin <= h <= self.hmax):
                ithx.log_warning(
                    f'Humidity value of {h} is out of range [{self.hmin}, {self.hmax}]'
                )
                return False

        for d in dewpoints:
            if not (self.dmin <= d <= self.dmax):
                ithx.log_warning(
                    f'Dewpoint value of {d} is out of range [{self.dmin}, {self.dmax}]'
                )
                return False

        # the data is okay, return True to insert the data into the database
        return True


@validator(name='ithx-with-reset')
class ithxWithReset(Validator):

    def __init__(self, config, reset_criterion=5, **kwargs):
        super().__init__(config, **kwargs)
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

        self.simplerange = ithxRangeChecker(**kwargs)

    def validate(self, data, ithx):

        if self.simplerange.validate(data, ithx):
            return True

        self.counter += 1

        if self.counter >= self.reset_criterion:
            ithx.log_warning(
                f'The Omega iServer will reset due to {self.reset_criterion} bad readings.'
            )
            ithx.reset(wait=True, password=None, port=2002, timeout=10)
            self.counter = 0

        return False
