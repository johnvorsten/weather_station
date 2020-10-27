# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:31:17 2020

@author: z003vrzk
"""

# Python imports
import unittest
import math
import re




#%%
"""
http://wxqa.com/faq.html


Each TCP connection will use port 14580
The ARPS server sends a text line indicating the server software we connected to
Receive one text line terminated with cr/lf. This line identifies server software

Login Line
The CWOP identifier is the user name, the passcode is -1 (minus one),
and the software identifier is your software name (no spaces) followed by the
version number (containing no spaces) (terminate with cr/lf)
Example
-------
user EW9876 pass -1 vers YourSoftwareName 1.0

Next, the server sends an acknowledgement line (can be ignored)

Next, the client can send a single ARPS packet with weather data. After the data
is send the client can disconnect from the server. There will be no
acknowledgement of the packet being received at the server.
The APRS "packet" is also terminated by cr/lf

The first "callsign" is the CWOP station identifier for that station as shown.
The next item is TCPIP followed by an asterisk
Example of ARPS packet
-------
EW9876>APRS,TCPIP*:rest of packet
CW0101>APRS,TCPXX*,qAX,CWOP-6:@262058z4447.27N/09130.98W_263/003g012t032r000p002P002h52b10264L228AmbientCWOP.com
DW0000>APRS,TCPXX*,qAX,CWOP-5:@262055z3707.72S/17436.52E_272/002g006t067r000p000P000b10258h83L671.WD 31
EW0006>APRS,TCPXX*,qAX,CWOP-5:@262045z3729.10N/00245.99W_236/000g000t047r000p008P000h68b09507L....DsIP


How is the weather data coded into the data packet? When you look at examples
of APRS position weather packets here, or here, the part after the longitude
"E" or "W" carries the weather data as symbols followed by numbers.
The underscore "_" followed by 3 numbers represents wind direction in
degrees from true north. This is the direction that the wind is blowing from.
The slash "/" followed by 3 numbers represents the average wind speed in miles
per hour. The letter "g" followed by 3 numbers represents the peak instaneous
value of wind in miles per hour. The letter "t" followed by 3 characters
(numbers and minus sign) represents the temperature in degrees F. The letter "r"
followed by 3 numbers represents the amount of rain in hundredths of inches
that fell the past hour. The letter "p" followed by 3 numbers represents the
 amount of rain in hundredths of inches that fell in the past 24 hours. Only
 these two precipitation values are accepted by MADIS. The letter "P" followed
 by 3 numbers represents the amount of rain in hundredths of inches that fell
 since local midnight. The letter "b" followed by 5 numbers represents the
 barometric pressure in tenths of a millibar. The letter "h" followed by 2
 numbers represents the relative humidity in percent, where "h00" implies
 100% RH. The first four fields
 (wind direction, wind speed, temperature and gust) are required, in that order,
 and if a particular measurement is not present, the three numbers should be
 replaced by "..." to indicate no data available. Solar radiation data can also
 be coded into the data packet.



"""

"""1. How often should I send data and to which server? """
class TaskManager:
    """Define data posting intervals and decide on a server to send data to
    This might not need to be implemented here"""
    pass




""""3. What is the APRS latitude/longitude position format? """
class APRSCoordinate(object):
    """APRS Latitude and Longitude position format
    LORAN position format
    about 60 feet resolution on the findu.com maps
    The format is "ddmm.hhN/dddmm.hhW
    """

    def __init__(self, *args, **kwargs):
        """
        inputs
        -------
        Either *args must be an iterable of (degree, minute, second), or
        **kwargs must contain the keys {'degree','minute','second'}"""

        if kwargs:
            try:
                degree = kwargs['degree']
                minute = kwargs['minute']
                second = kwargs['second']
            except ValueError:
                msg = ("kwargs must contain keys (degree, minute, second) " +
                       "got {}".format(args))
                raise ValueError(msg)

        elif args:
            if len(args) == 1:
                self.degree_minute = args[0]
                degree, minute, second = \
                    self._calc_degree_minute_second(self.degree_minute)

            else:
                try:
                    degree = args[0]
                    minute = args[1]
                    second = args[2]
                except IndexError:
                    msg = ("args must be an iterable of (degree, minute, second) " +
                           "got {}".format(args))
                    raise ValueError(msg)

        else:
            msg = ("Class constructor must contain either an iterable of" +
                   "(degree, minute, second), or **kwargs must contain " +
                   "the keys {'degree','minute','second'}")
            raise ValueError(msg)

        self.degree = float(degree)
        self.minute = float(minute)
        self.second = float(second)
        self.decimal_degree = self._calc_decimaldegree(float(degree),
                                                       float(minute),
                                                       float(second))
        self.degree_minute = self._calc_decimaldegree(float(degree),
                                                      float(minute),
                                                      float(second))

        return

    def _find_position(self):
        pass

    @staticmethod
    def _calc_decimaldegree(degree, minute, second):
        """
        Convert latitude/longitude with the entry format
        (degress, minutes, seconds) to decimal degrees

        inputs
        -------
        degree : (int)
        minute : (int)
        second : (int)

        outputs
        -------
        decimal_degree : (float) coordinate in decimal degrees

        Example - There are 60 minutes in a degree, 60 seconds in a minute
        degrees = 12
        minutes = 20
        seconds = 44
        result = degree + minute/60 + second/3600
        """
        decimal_degree = degree + minute/60. + second/3600.
        return decimal_degree

    @staticmethod
    def _calc_degree_minute(degree, minute, second):
        """
        Convert latitude/longitude with the entry format
        (degress, minutes, seconds) to degree minutes. Degree minutes are
        a way to represent coordinates in the format
        (Degrees, minutes, hundreths of a minute). Degrees are simply degrees
        degree minutes are calculated as minutes + (seconds / 60)

        inputs
        -------
        degree : (int)
        minute : (int)
        second : (int)

        outputs
        -------
        (degree, decimal_minutes) : (tuple) coordinate in degrees minutes
        """
        return (degree, minute + second/60)

    @staticmethod
    def _calc_degree_minute_second(decimal_degree):
        """Return the traditional degree, minute, second from decimal degrees
        inputs
        -------
        decimal_degree : (float)
        outputs
        --------
        degree, minute, second : (float) coordinates"""
        degree = math.floor(decimal_degree)
        minute = decimal_degree % 1 * 60
        second = minute % 1 * 60

        return (math.floor(decimal_degree), math.floor(minute), round(second))

    def __neg__(self):
        return APRSCoordinate(-self.decimal_degree)

    def __pos__(self):
        return APRSCoordinate(self.decimal_degree)

    def __abs__(self):
        return APRSCoordinate(self.decimal_degree)

    def __add__(self, other):
        return APRSCoordinate(self.decimal_degree + other)

    def __iadd__(self, other):
        return self.__add__(other)

    def __radd__(self, other):
        # other is a scalar
        return self.__add__(other)

    def __sub__(self, other):
        # other is a scalar
        return self.__add__(-other)

    def __isub__(self, other):
        # other is a scalar
        return self.__sub__(other)

    def __rsub__(self, other):
        # other is a scalar
        return self.__sub__(other)

    def __floor__(self):
        return APRSCoordinate(math.floor(self.decimal_degree))

    def __round__(self):
        return APRSCoordinate(round(self.decimal_degree))

    def __ceil__(self):
        return APRSCoordinate(math.ceil(self.decimal_degree))

    def __int__(self):
        return self.degree

    def __float__(self):
        return self.decimal_degree

    def __str__(self):
        return str(self.decimal_degree)

    def __repr__(self):
        return self.__str__()

class GeoTest(unittest.TestCase):

    def setUp(self):
        global aprs, latitude, longitude, lat_dd, lat_dm
        latitude =  (12, 34, 56)
        lat_dd = 12.582222222222223
        lat_dm = 34.933333333333
        longitude = (16, 25, 34)
        aprs = APRSCoordinate(*latitude)
        return

    def test_decimaldegree(self):
        decimal_degree = APRSCoordinate._calc_decimaldegree(*latitude)
        print(decimal_degree)
        self.assertAlmostEqual(decimal_degree, 12.5822, places=4)
        return

    def test_ARPSCoordinate_init(self):

        # Args method
        _aprs = APRSCoordinate(*latitude)
        self.assertIsInstance(_aprs, APRSCoordinate)
        self.assertEqual(_aprs.degree, latitude[0])
        self.assertEqual(_aprs.minute, latitude[1])
        self.assertEqual(_aprs.second, latitude[2])
        self.assertAlmostEqual(_aprs.decimal_degree, lat_dd, places=4)

        # Kwargs method
        coord = {'degree':latitude[0],'minute':latitude[1],'second':latitude[2]}
        _aprs = APRSCoordinate(**coord)
        self.assertIsInstance(_aprs, APRSCoordinate)
        self.assertEqual(_aprs.degree, latitude[0])
        self.assertEqual(_aprs.minute, latitude[1])
        self.assertEqual(_aprs.second, latitude[2])
        self.assertAlmostEqual(_aprs.decimal_degree, lat_dd, places=4)

        # Decimal degree method
        _aprs = APRSCoordinate(12.582222222)
        self.assertIsInstance(_aprs, APRSCoordinate)
        self.assertEqual(_aprs.degree, latitude[0])
        self.assertEqual(_aprs.minute, latitude[1])
        self.assertEqual(_aprs.second, latitude[2])
        self.assertAlmostEqual(_aprs.decimal_degree, lat_dd, places=4)

        return





if __name__ == '__main__':
    unittest.main(GeoTest())








