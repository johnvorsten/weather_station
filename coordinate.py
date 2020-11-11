# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:31:17 2020

@author: z003vrzk
"""

# Python imports
import math
import re
import abc



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
                if 'decimal_degree' in kwargs.keys():
                    decimal_degree = kwargs['decimal_degree']
                    self.decimal_degree = decimal_degree
                    degree, minute, second = \
                        self._calc_degree_minute_second(self.decimal_degree)

                elif 'degree' in kwargs.keys():
                    degree = kwargs['degree']
                    minute = kwargs['minute']
                    second = kwargs['second']

            except KeyError:
                msg = ("kwargs must contain keys (degree, minute, second) " +
                       "OR ('decimal_degree'). Got {}".format(kwargs))
                raise ValueError(msg)

        elif args:
            if len(args) == 1:
                self.decimal_degree = args[0]
                degree, minute, second = \
                    self._calc_degree_minute_second(self.decimal_degree)

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
                   "the keys {'degree','minute','second'} or {'decimal_degree'}")
            raise ValueError(msg)

        if any(((minute < 0), (second < 0))):
            msg = ("minute or second cannot be negative numbers. When " +
                   "representing " +
                   "the southern or Western hemisphere pass degree as a " +
                   "negative number")
            raise ValueError(msg)

        self.degree = float(degree)
        self.minute = abs(float(minute))
        self.second = abs(float(second))
        if not 'decimal_degree' in self.__dict__:
            self.decimal_degree = self._calc_decimaldegree(float(degree),
                                                           float(minute),
                                                           float(second))
        _, self.decimal_minute = self._calc_decimal_minute(float(degree),
                                                           float(minute),
                                                           float(second))
        return


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
        sign = math.copysign(1, degree)
        decimal_degree = abs(degree) + abs(minute/60) + abs(second/3600)
        return sign * decimal_degree

    @staticmethod
    def _calc_decimal_minute(degree, minute, second):
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
        return (degree, abs(minute) + abs(second/60))

    @staticmethod
    def _calc_degree_minute_second(decimal_degree):
        """Return the traditional degree, minute, second from decimal degrees
        inputs
        -------
        decimal_degree : (float)
        outputs
        --------
        degree, minute, second : (float) coordinates"""

        if decimal_degree < 0:
            degree = math.ceil(decimal_degree)
        else:
            degree = math.floor(decimal_degree)
        minute = decimal_degree % 1 * 60
        second = minute % 1 * 60
        return (degree, math.floor(minute), round(second))

    @abc.abstractmethod
    def get_hemisphere(self):
        return


    def to_string(self, format_str):
        """
        Output coordinate in formatted string
        inputs
        -------
        format_str : (str) A string of the form A%B%C where A, B and C are
        identifiers.
        'H' - Hemisphere designation (E/W for longitude, N/S for latitude)
        'M' - decimal minute
        'm' - minute
        'd' - degree
        'D' - decimal degree
        'S' - second

        Unknown identifiers (e.g. [' ', ',', '-', '_', ', ']) will be inserted as
        separators in a position corresponding to the position in format.
        Examples:
        """
        reg = '[ ,_-]'
        rege = re.compile(reg)
        format2value = {'H': self.get_hemisphere(),
                        'M': abs(self.decimal_minute),
                        'm': abs(self.minute),
                        'd': self.degree,
                        'D': self.decimal_degree,
                        'S': abs(self.second)}
        format_elements = format_str.split('%')

        coord_list = []
        for element in format_elements:
            res = rege.search(element)

            new_element = rege.sub('', element)
            value = str(format2value.get(new_element, new_element))
            coord_list.append(value)

            if res:
                coord_list.append(element[res.start():res.end()])

        # coord_list = [str(format2value.get(element, element)) for element in format_elements]
        coord_str = ''.join(coord_list)
        if 'H' in format_elements: # No negative values when hemispheres are indicated
            coord_str = coord_str.replace('-', '')
        return coord_str

    def _update(self, degree, minute, second):
        self.decimal_minute = self.\
            _calc_decimal_minute(degree, minute, second)
        self.decimal_degree = self.\
            _calc_decimaldegree(degree, minute, second)
        return

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
        return "APRSCoordinate({})".format(self.decimal_degree)



class Latitude(APRSCoordinate):
    """Latidude Coordinates"""

    def get_hemisphere(self):
        '''
        Returns the hemisphere identifier for the current coordinate
        '''
        if self.decimal_degree < 0: return 'S'
        else: return 'N'

    def set_hemisphere(self, hemi_str):
        """Given a hemisphere identifier, set the sign of the coordinate to
        match that hemisphere"""
        if hemi_str == 'S':
            self.degree = abs(self.degree)*-1
            self.minute = abs(self.minute)
            self.second = abs(self.second)
            self._update(self.degree, self.minute, self.second)
        elif hemi_str == 'N':
            self.degree = abs(self.degree)
            self.minute = abs(self.minute)
            self.second = abs(self.second)
            self._update(self.degree, self.minute, self.second)
        else:
            raise ValueError("Hemisphere must be one of ('N','S')")
        return

    def __repr__(self):
        return "Latitude({})".format(self.decimal_degree)



class Longitude(APRSCoordinate):
    """
    Coordinate object specific for longitude coordinates
    Langitudes outside the range -180 to 180
    """

    def __init__(self, *args, **kwargs):
        super(Longitude, self).__init__(*args, **kwargs)

    def get_hemisphere(self):
        '''
        Returns the hemisphere identifier for the current coordinate
        '''
        if self.decimal_degree < 0: return 'W'
        else: return 'E'

    def set_hemisphere(self, hemi_str):
        '''
        Given a hemisphere identifier, set the sign of the coordinate to match that hemisphere
        '''
        if hemi_str == 'W':
            self.degree = abs(self.degree)*-1
            self.minute = abs(self.minute)
            self.second = abs(self.second)
            self._update(self.degree, self.minute, self.second)
        elif hemi_str == 'E':
            self.degree = abs(self.degree)
            self.minute = abs(self.minute)
            self.second = abs(self.second)
            self._update(self.degree, self.minute, self.second)
        else:
            raise(ValueError, "Hemisphere must be one of ('E','W')")
        return

    def __repr__(self):
        return "Longitude({})".format(self.decimal_degree)












