# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 12:45:51 2020

@author: z003vrzk
"""

# Python imports
import unittest
import re
from datetime import datetime

# Local imports
from CWOPpdu import LoginLine, CWOPPDU, CWOPHeader, ProviderID





class PDUTest(unittest.TestCase):

    def setUp(self):
        """Inputs
        -------
        kwargs :
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
        """
        global init_kwargs, base_kwargs, provider_id

        init_kwargs = {'time':datetime.now(),
                       'longitude':'1234.00E',
                       'latitude':'1234.00N',
                       'wind_direction':123,
                       'wind_speed':123,
                       'peak_instantaneous_wind_velocity':123,
                       'temperature':123,
                       'rainfall_rate_hour':123,
                       'rainfall_rate_day':123,
                       'rainfall_rate_midnight':123,
                       'barometric_pressure':12345,
                       'humidity':26,
                       }
        base_kwargs = {'time':datetime.now(),
                       'longitude':'1234.00E',
                       'latitude':'1234.00N',
                       }
        provider_id = 'FW9999'


    def test_longitude(self):
        return

    def test_latitude(self):
        return

    def test_wind_direction(self):
        return

    def test_wind_speed(self):
        return

    def test_peak_instantaneous_wind_velocity(self):
        return

    def test_temperature(self):
        pdu = CWOPPDU(provider_id, **base_kwargs, temperature=-31)
        test = '-31'
        self.assertEqual(test, pdu.data['temperature'])
        return

    def test_rainfall_rate_hour(self):
        return

    def test_rainfall_rate_day(self):
        return

    def test_rainfall_rate_midnight(self):
        return

    def test_barometric_pressure(self):
        return

    def test_humidity(self):

        # 0% relative humidity should be impossible?
        pdu = CWOPPDU(provider_id, **base_kwargs, humidity=0)
        test = '01'
        self.assertEqual(test, pdu.data['humidity'])

        # 100% relative humidity is represented as 00
        pdu = CWOPPDU(provider_id, **base_kwargs, humidity=0)
        test = '01'
        self.assertEqual(test, pdu.data['humidity'])

        # Negative number
        with self.assertRaises(ValueError):
            pdu = CWOPPDU(provider_id, **base_kwargs, humidity=-26)

        # 1 <= humidity <100
        pdu = CWOPPDU(provider_id, **base_kwargs, humidity=26)
        test = '26'
        self.assertEqual(test, pdu.data['humidity'])

        return

    def test_init(self):
        pdu = CWOPPDU(provider_id, **init_kwargs)

        # Time
        test = datetime.now().strftime('%d%H%M')
        self.assertEqual(test, pdu.data['time'])

        # XXX
        test = init_kwargs['longitude']
        self.assertEqual(test, pdu.data['longitude'])
        # XXX
        test = init_kwargs['latitude']
        self.assertEqual(test, pdu.data['latitude'])
        # XXX
        test = str(init_kwargs['wind_direction'])
        self.assertEqual(test, pdu.data['wind_direction'])
        # XXX
        test = str(init_kwargs['wind_speed'])
        self.assertEqual(test, pdu.data['wind_speed'])
        # XXX
        test = str(init_kwargs['peak_instantaneous_wind_velocity'])
        self.assertEqual(test, pdu.data['peak_instantaneous_wind_velocity'])
        # XXX
        test = str(init_kwargs['temperature'])
        self.assertEqual(test, pdu.data['temperature'])
        # XXX
        test = str(init_kwargs['rainfall_rate_hour'])
        self.assertEqual(test, pdu.data['rainfall_rate_hour'])
        # XXX
        test = str(init_kwargs['rainfall_rate_day'])
        self.assertEqual(test, pdu.data['rainfall_rate_day'])
        # XXX
        test = str(init_kwargs['rainfall_rate_midnight'])
        self.assertEqual(test, pdu.data['rainfall_rate_midnight'])
        # XXX
        test = str(init_kwargs['barometric_pressure'])
        self.assertEqual(test, pdu.data['barometric_pressure'])
        # XXX
        test = str(init_kwargs['humidity'])
        self.assertEqual(test, pdu.data['humidity'])

        return

    def test_pdu_data_packet(self):
        pdu = CWOPPDU(provider_id, **init_kwargs)

        packet = pdu.pdu_data_packet
        self.assertIsInstance(packet, bytes)

        return

    def test_pdu_login_line(self):
        pdu = CWOPPDU(provider_id, **init_kwargs)
        login_line = pdu.login_line
        self.assertIsInstance(login_line, bytes)
        test = b'user FW9999 pass -1 vers PythonCWOP 1.0'
        self.assertEqual(login_line, test)

        return


class ProviderIDTest(unittest.TestCase):

    def test_provider_id(self):

        # Should successfully initialize
        provid = ProviderID('FW9999')
        self.assertIsInstance(provid, ProviderID)

        # Wrong letters
        self.assertRaises(ValueError, ProviderID, 'AA9999')
        # Lower Case
        self.assertRaises(ValueError, ProviderID, 'fw9999')
        # Wrong Numbers
        self.assertRaises(ValueError, ProviderID, 'fw999a')
        # Wrong Length
        self.assertRaises(ValueError, ProviderID, 'fw999')
        # Wrong type
        self.assertRaises(ValueError, ProviderID, 9999)

        return


class LoginLineTest(unittest.TestCase):

    def test_loginline(self):

        provider_id = 'FW9999'
        login = LoginLine(provider_id)

        test = b"user FW9999 pass -1 vers PythonCWOP 1.0"
        self.assertEqual(test, login.login_line)
        self.assertIsInstance(login.login_line, bytes)

        print("Login Line : ", login.login_line)

        return


class CWOPHeaderTest(unittest.TestCase):

    def test_header(self):

        provider_id = 'FW9999'
        header = CWOPHeader(provider_id)

        test = b"FW9999>APRS,TCPIP*:"
        self.assertEqual(test, header.header)
        self.assertIsInstance(header.header, bytes)

        print("Header Line : ", header.header)

        return


if __name__ == '__main__':
    unittest.main(PDUTest())
    unittest.main(ProviderIDTest())
    unittest.main(LoginLineTest())
    unittest.main(CWOPHeaderTest())