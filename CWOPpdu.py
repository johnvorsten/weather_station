# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 06:53:49 2020

@author: z003vrzk
"""

# Python imports
import asyncio
import time
import re
import unittest
from datetime import datetime

# Local imports
from coordinate import Latitude, Longitude

#%% CWOP data packet

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

"""The third database is the CWOP database. Ham stations have a Provider ID of
apxxx or arxxx or asxxx or atxxx or auxxx
(two lower case letters followed by 3 numbers) and non-ham weather stations
have a Provider ID of CWxxxx or DWxxxx or EWxxxx or FWxxxx
(2 upper case letters followed by 4 numbers)."""

class ProviderID(object):

    def __init__(self, provider_id):
        """Inputs
        -------
        provider_id : (str) Ham stations have a Provider ID of
        apxxx or arxxx or asxxx or atxxx or auxxx
        (two lower case letters followed by 3 numbers) and non-ham weather stations
        have a Provider ID of CWxxxx or DWxxxx or EWxxxx or FWxxxx
        (2 upper case letters followed by 4 numbers)"""
        self._check_provider_id(provider_id)
        self.provider_id = provider_id

    @staticmethod
    def _check_provider_id(provider_id):
        """Error check for correct format of provider ID
        See http://wxqa.com/faq.html for information on how provider IDs are
        formatted
        The key things to remember are that the ham callsign or CWxxxx or
        DWxxxx or EWxxxx or FWxxxx goes in with your data packet and is what
        you look for on findu.com
        """

        if not isinstance(provider_id, str):
            msg="provider_id must be string data type. Got {}"\
                .format(type(provider_id))
            raise ValueError(msg)

        if not len(provider_id) == 6:
            msg=("provider_id length must be 6 characters for the packet " +
                 "to be sent to the findu.com servers. " +
                 "Got length = {}".format(len(provider_id)))
            raise ValueError(msg)

        if provider_id[:2] not in ['CW','DW','EW','FW']:
            msg=("provider_id must begin with the characters " +
                 "['CW','DW','EW','FW']. Got {}".format(provider_id))
            raise ValueError(msg)

        numbers_re = '[^0-9]'
        if re.search(numbers_re, provider_id[2:]):
            # Characters other than numbers were found
            msg=("Characters other than numbers were found in the last 4 " +
                 "characters of provider_id. Got {}".format(provider_id))
            raise ValueError(msg)

        return True

    def quality_check(self):
        """Send a packet and check if the provider ID reached the findu server"""
        raise NotImplementedError()
        return None


class LoginLine(ProviderID):
    software_name = 'PythonCWOP'
    software_version = '1.0'
    login_base = ("user {ProviderID} " +
                  "pass -1 vers " +
                  "{software_name} {software_version}")

    def __init__(self, provider_id):
        super().__init__(provider_id)

    @property
    def login_line(self):
        """Example
        user EW9876 pass -1 vers YourSoftwareName 1.0
        """
        login_line_str = self.login_base.format(ProviderID=self.provider_id,
                                      software_name=self.software_name,
                                      software_version=self.software_version)
        return bytes(login_line_str, 'utf-8')

    def __str__(self):
        return self.login_line

    def __repr__(self):
        return 'LoginLine<{}>'.format(self.provider_id)



class CWOPHeader(ProviderID):
    header_base = "{ProviderID}>APRS,TCPIP*:"

    def __init_(self, provider_id):
        super().__init__(provider_id)
        return

    @property
    def header(self):
        # String
        return self.header_base.format(ProviderID=self.provider_id)



class CWOPPDU(CWOPHeader, LoginLine):
    """A PDU is composed of protocol-specific control information and user
    data.

    In an APRS weather data packet, the part between "@" and "z" is the time
    of the weather station clock when the packet was sent.

    See http://wxqa.com/faq.html
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

     Example of ARPS packet
    -------
    EW9876>APRS,TCPIP*:rest of packet
    CW0101>APRS,TCPXX*,qAX,CWOP-6:@262058z4447.27N/09130.98W_263/003g012t032r000p002P002h52b10264L228AmbientCWOP.com
    DW0000>APRS,TCPXX*,qAX,CWOP-5:@262055z3707.72S/17436.52E_272/002g006t067r000p000P000b10258h83L671.WD 31
    EW0006>APRS,TCPXX*,qAX,CWOP-5:@262045z3729.10N/00245.99W_236/000g000t047r000p008P000h68b09507L....DsIP
    SV2BZQ-3>APRS,TCPIP*,qAC,T2MEXICO:@312258z4044.76N/02252.05E_345/011g032t060r000p000P000b10168h60eMB50

    """
    base_data = "{header}"\
        "@{time}"\
        "z{latitude}"\
        "/{longitude}"\
        "_{wind_direction}"\
        "/{wind_speed}"\
        "g{peak_instantaneous_wind_velocity}"\
        "t{temperature}"\
        "r{rainfall_rate_hour}"\
        "p{rainfall_rate_day}"\
        "P{rainfall_rate_midnight}"\
        "b{barometric_pressure}"\
        "h{humidity}"

    @property
    def pdu_data_packet(self):
        return bytes(self.base_data.format(header=self.header, **self.data), 'utf-8')

    def __init__(self, provider_id, *args, **kwargs):
        """Inputs
        -------
        provider_id : (str) Ham stations have a Provider ID of
            apxxx or arxxx or asxxx or atxxx or auxxx
            (two lower case letters followed by 3 numbers) and non-ham weather
            stations have a Provider ID of CWxxxx or DWxxxx or EWxxxx or FWxxxx
            (2 upper case letters followed by 4 numbers)
        kwargs : {
        time : (required, str or datetime) The default time format is %d%H%M
            or DayHourMinute. Pass as a string with leading zeros if necessary
        longitude : (required, str or coordinate.Longitude) The format is
            "ddmm.hhN/dddmm.hhW"
        latidude : (required, str or coordinate.Latitude) The format is
            "ddmm.hhN/dddmm.hhW"
        wind_direction : (optional, int) direction in degrees from true North
            [degrees]
        wind_speed : (optional, float) wind speed [miles/hour]
        peak_instantaneous_wind_velocity : (optional, float) peak instantaneous
            wind speed [miles/hour]
        temperature : (optional, int) temperature in farenheit
        rainfall_rate_hour : (optional, int) rain in hundredths of inches
            that fell in the last hour [inch/100]
        rainfall_rate_day : (optional, int) amount of rain in hundredths of
            inches that fell in the past 24 hour
        rainfall_rate_midnight : (optional, float) amount of rain in hundredths
            of inches that fell since local midnight
        barometric_pressure : (optional, float) 5 numbers represents the
            barometric pressure in tenths of a millibar
        humidity : (optional) 2 numbers represents the relative humidity in
            percent, where 'h00' implies 100% RH [percent, RH]
        }

        """
        # Initialize LoginLine and CWOPHeader
        super().__init__(provider_id)

        data = {}

        if 'time' in kwargs:
            data['time'] = self._check_time(kwargs['time'])
        else:
            data['time'] = datetime.now().strftime('%d%H%M')

        if 'latitude' in kwargs:
            data['latitude'] = self._check_latitude(kwargs['latitude'])
        else:
            raise ValueError("'latitude' is a required keyword argument")

        if 'longitude' in kwargs:
            data['longitude'] = self._check_longitude(kwargs['longitude'])
        else:
            raise ValueError("'longitude' is a required keyword argument")

        if 'wind_direction' in kwargs:
            data['wind_direction'] = self._check_wind_direction(kwargs['wind_direction'])
        else:
            data['wind_direction'] = '...'

        if 'wind_speed' in kwargs:
            data['wind_speed'] = self._check_wind_speed(kwargs['wind_speed'])
        else:
            data['wind_speed'] = '...'

        if 'peak_instantaneous_wind_velocity' in kwargs:
            data['peak_instantaneous_wind_velocity'] = self._check_peak_instantaneous_wind_velocity(kwargs['peak_instantaneous_wind_velocity'])
        else:
            data['peak_instantaneous_wind_velocity'] = '...'

        if 'temperature' in kwargs:
            data['temperature'] = self._check_temperature(kwargs['temperature'])
        else:
            data['temperature'] = '...'

        if 'rainfall_rate_hour' in kwargs:
            data['rainfall_rate_hour'] = self._check_rainfall_rate_hour(kwargs['rainfall_rate_hour'])
        else:
            data['rainfall_rate_hour'] = '...'

        if 'rainfall_rate_day' in kwargs:
            data['rainfall_rate_day'] = self._check_rainfall_rate_day(kwargs['rainfall_rate_day'])
        else:
            data['rainfall_rate_day'] = '...'

        if 'rainfall_rate_midnight' in kwargs:
            data['rainfall_rate_midnight'] = self._check_rainfall_rate_midnight(kwargs['rainfall_rate_midnight'])
        else:
            data['rainfall_rate_midnight'] = '...'

        if 'barometric_pressure' in kwargs:
            data['barometric_pressure'] = self._check_barometric_pressure(kwargs['barometric_pressure'])
        else:
            data['barometric_pressure'] = '...'

        if 'humidity' in kwargs:
            data['humidity'] = self._check_humidity(kwargs['humidity'])
        else:
            data['humidity'] = '...'

        self.data = data

        return


    def _check_time(self, arg):
        """The default time format is %d%H%M or DayHourMinute
        Example
        010923 First of the month hour 9 minute 23"""

        msg=("time should be passed as string or datetime in the format "+
             "%d%H%M where %d is day of the month, %H is the current hour "+
             "out of 24, and minute is the minute. Use leading zeros. Got {}")

        if isinstance(arg, datetime):
            return arg.strftime('%d%H%M')
        if not len(arg) == 6:
            raise ValueError(msg.format(arg))
        if re.search('[^0-9]', arg):
            # Not numbers 0-9
            raise ValueError(msg.format(arg))

        return arg

    def _check_longitude(self, arg):

        if isinstance(arg, Longitude):
            # Degree can be 0<180 (No negatives)
            degree = '{:03.0f}'.format(abs(arg.degree)) # 0<180 format w/ E or W
            decimal_minute = '{:05.2f}'.format(arg.decimal_minute)
            hemisphere = arg.get_hemisphere()
            return '{}{}{}'.format(degree, decimal_minute, hemisphere)

        elif not isinstance(arg, str):
            msg='longitude must be str or Longitude type. Got {}'.format(type(arg))

        # Match ####.##H
        # Length 8 characters
        # 4 numbers . 2 numbers [E or W]
        if not re.search('^[0-9]{4}.[0-9]{2}[EW]$', arg):
            msg='Longitude must follow format "dddmm.hhW"'
            raise ValueError(msg)

        return arg

    def _check_latitude(self, arg):

        if isinstance(arg, Latitude):
            # Degree is only 0<90
            degree = '{:02.0f}'.format(arg.degree)
            decimal_minute = '{:05.2f}'.format(arg.decimal_minute)
            hemisphere = arg.get_hemisphere()
            return '{}{}{}'.format(degree, decimal_minute, hemisphere)

        elif not isinstance(arg, str):
            msg='Latitude must be str or Latitude type. Got {}'.format(type(arg))

        # Match ####.##H
        # Length 8 characters
        # 4 numbers . 2 numbers [E or W]
        if not re.search('^[0-9]{4}.[0-9]{2}[NS]$', arg):
            msg='Longitude must follow format "dddmm.hhN"'
            raise ValueError(msg)

        return arg

    def _check_wind_direction(self, arg):
        """The underscore "_" followed by 3 numbers represents wind direction
        in degrees from true north"""
        try:
            direction = int(arg)
        except TypeError:
            msg="Wind direction must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        if (direction > 360) or (direction < 0):
            msg="Wind speed must be less than 360 or greater than 0"
            raise ValueError(msg)

        return '{:03.0f}'.format(direction)

    def _check_wind_speed(self, arg):
        """The slash "/" followed by 3 numbers represents the average wind
        speed in miles per hour"""
        try:
            speed = int(arg)
        except TypeError:
            msg="Wind Speed must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:03.0f}'.format(speed)

    def _check_peak_instantaneous_wind_velocity(self, arg):
        """The letter "g" followed by 3 numbers represents the peak instaneous
        value of wind in miles per hour."""
        try:
            speed = int(arg)
        except TypeError:
            msg="Wind Speed must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:03.0f}'.format(speed)

    def _check_temperature(self, arg):
        """The letter "t" followed by 3 characters (numbers and minus sign)
        represents the temperature in degrees F."""

        try:
            temperature = int(arg)
        except TypeError:
            msg="Temperature must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:03.0f}'.format(temperature)

    def _check_rainfall_rate_hour(self, arg):
        """The letter "r" followed by 3 numbers represents the amount of rain
        in hundredths of inches that fell the past hour."""
        try:
            val = int(arg)
        except TypeError:
            msg="rainfall must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:03.0f}'.format(val)

    def _check_rainfall_rate_day(self, arg):
        """The letter "p" followed by 3 numbers represents the amount of rain
        in hundredths of inches that fell in the past 24 hours"""
        try:
            val = int(arg)
        except TypeError:
            msg="rainfall must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:03.0f}'.format(val)

    def _check_rainfall_rate_midnight(self, arg):
        """The letter "P" followed by 3 numbers represents the amount of rain
        in hundredths of inches that fell since local midnight"""

        try:
            val = int(arg)
        except TypeError:
            msg="rainfall must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:03.0f}'.format(val)

    def _check_barometric_pressure(self, arg):
        """The letter "b" followed by 5 numbers represents the barometric
        pressure in tenths of a millibar."""
        try:
            val = int(arg)
        except TypeError:
            msg="barometric_pressure must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:05.0f}'.format(val)

    def _check_humidity(self, arg):
        """The letter "h" followed by 2 numbers represents the relative
        humidity in percent, where "h00" implies 100% RH"""

        try:
            val = int(arg)
        except TypeError:
            msg="Humidity must be float, integer, or compatable. Got {}"
            raise ValueError(msg.format(type(arg)))

        if val == 100:
            # 100% Humidity
            return '00'

        if val == 0:
            # 1% relative humidity
            return '01'

        if any((val < 0, val > 100)):
            msg="Humidity must be positive 1<=x<=100. Got {}"
            raise ValueError(msg.format(type(arg)))

        return '{:02.0f}'.format(val)

    def __repr__(self):
        return 'CWOPPDU({})'.format(self.pdu_data_packet.decode())

