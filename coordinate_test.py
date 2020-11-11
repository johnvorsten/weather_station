# -*- coding: utf-8 -*-


# Python imports
import unittest

# Local imports
from coordinate import APRSCoordinate, Latitude, Longitude



#%%


class CoordinateTest(unittest.TestCase):

    def setUp(self):
        global aprs, latitude, longitude, lat_dd, lat_dm
        latitude =  (12, 34, 56)
        lat_dd = 12.582222222222223
        lat_dm = 34.933333333333
        longitude = (16, 25, 34)
        return

    def test_decimaldegree(self):
        decimal_degree = APRSCoordinate._calc_decimaldegree(*latitude)
        print(decimal_degree)
        self.assertAlmostEqual(decimal_degree, 12.5822, places=4)
        return

    def test_ARPSCoordinate_init(self):

        # Args method
        aprs = APRSCoordinate(*latitude)
        self.assertIsInstance(aprs, APRSCoordinate)
        self.assertEqual(aprs.degree, latitude[0])
        self.assertEqual(aprs.minute, latitude[1])
        self.assertEqual(aprs.second, latitude[2])
        self.assertAlmostEqual(aprs.decimal_degree, lat_dd, places=4)

        # Kwargs method
        coord = {'degree':latitude[0],'minute':latitude[1],'second':latitude[2]}
        aprs = APRSCoordinate(**coord)
        self.assertIsInstance(aprs, APRSCoordinate)
        self.assertEqual(aprs.degree, latitude[0])
        self.assertEqual(aprs.minute, latitude[1])
        self.assertEqual(aprs.second, latitude[2])
        self.assertAlmostEqual(aprs.decimal_degree, lat_dd, places=4)

        # Kwargs method
        coord = {'decimal_degree':lat_dd}
        aprs = APRSCoordinate(**coord)
        self.assertIsInstance(aprs, APRSCoordinate)
        self.assertEqual(aprs.degree, latitude[0])
        self.assertEqual(aprs.minute, latitude[1])
        self.assertEqual(aprs.second, latitude[2])
        self.assertAlmostEqual(aprs.decimal_degree, lat_dd, places=4)

        # Decimal degree method
        aprs = APRSCoordinate(12.582222222)
        self.assertIsInstance(aprs, APRSCoordinate)
        self.assertEqual(aprs.degree, latitude[0])
        self.assertEqual(aprs.minute, latitude[1])
        self.assertEqual(aprs.second, latitude[2])
        self.assertAlmostEqual(aprs.decimal_degree, lat_dd, places=4)

        # Incorrect constructor
        self.assertRaises(ValueError, APRSCoordinate, latitude[0],
                                                     -latitude[1],
                                                     -latitude[2])
        self.assertRaises(ValueError, APRSCoordinate, latitude[0],
                                                     -latitude[1],
                                                     latitude[2])
        self.assertRaises(ValueError, APRSCoordinate, latitude[0],
                                                     latitude[1],
                                                     -latitude[2])
        self.assertRaises(ValueError, APRSCoordinate, **{'degree':latitude[0],
                                                         'minute':-latitude[1],
                                                         'second':-latitude[2]})
        self.assertRaises(ValueError, APRSCoordinate, **{'degree':latitude[0],
                                                         'minute':-latitude[1],
                                                         'second':latitude[2]})
        self.assertRaises(ValueError, APRSCoordinate, **{'degree':latitude[0],
                                                        'minute':latitude[1],
                                                        'second':-latitude[2]})

        return

    def test_negative(self):

        aprs = APRSCoordinate(-latitude[0], latitude[1], latitude[2])
        self.assertEqual(aprs.degree, -latitude[0])
        self.assertEqual(aprs.minute, latitude[1])
        self.assertEqual(aprs.second, latitude[2])
        self.assertAlmostEqual(aprs.decimal_degree, -lat_dd, places=4)

        # Decimal Degree
        decimal_degree = -95.458310
        aprs = APRSCoordinate(decimal_degree)
        aprs.degree
        aprs.minute
        aprs.second
        aprs.decimal_degree
        aprs.decimal_minute
        aprs._calc_degree_minute_second(decimal_degree)

        return

    def test__calc_degree_minute_second(self):
        decimal_degree = -95.458310
        aprs = APRSCoordinate(decimal_degree)
        degree, minute, second = aprs._calc_degree_minute_second(decimal_degree)
        self.assertEqual(degree, -95)
        self.assertEqual(minute, 27)
        self.assertEqual(second, 30)

        return

    def test_str_format(self):
        """
        'H' - Hemisphere designation (E/W for longitude, N/S for latitude)
        'M' - decimal minute
        'm' - minute
        'd' - degree
        'D' - decimal degree
        'S' - second
        """
        aprs = APRSCoordinate(latitude[0], latitude[1], latitude[2])
        res = aprs.to_string('%H')
        self.assertEqual(res, 'None') # Not implemented
        res = aprs.to_string('%H %M %m %d %D %S')
        elements = res.split(' ')
        self.assertEqual(elements[0], 'None')
        self.assertEqual(elements[1], str(aprs.decimal_minute))
        self.assertEqual(elements[2], str(aprs.minute))
        self.assertEqual(elements[3], str(aprs.degree))
        self.assertEqual(elements[4], str(aprs.decimal_degree))
        self.assertEqual(elements[5], str(aprs.second))

if __name__ == '__main__':
    unittest.main(CoordinateTest())


#%%



class LatitudeTest(unittest.TestCase):

    def setUp(self):
        global aprs, latitude, longitude, lat_dd, lat_dm
        latitude =  (12, 34, 56)
        lat_dd = 12.582222222222223
        lat_dm = 34.933333333333
        longitude = (16, 25, 34)
        return

    def test_get_hemisphere(self):
        # North latitudes run 0,90 degrees
        lat = Latitude(latitude[0], latitude[1], latitude[2])
        hemisphere = lat.get_hemisphere()
        self.assertEqual(hemisphere, 'N')

        # South latitudes run 0,-90 degrees
        lat = Latitude(-latitude[0], latitude[1], latitude[2])
        hemisphere = lat.get_hemisphere()
        self.assertEqual(hemisphere, 'S')
        return

    def test_set_hemisphere(self):

        # North latitudes run 0,90 degrees
        lat = Latitude(latitude[0], latitude[1], latitude[2])
        lat.set_hemisphere('S')
        self.assertEqual(lat.degree, -latitude[0])
        self.assertEqual(lat.decimal_degree, -lat_dd)


        # South latitudes run 0,-90 degrees
        lat = Latitude(-latitude[0], latitude[1], latitude[2])
        lat.set_hemisphere('N')
        self.assertEqual(lat.degree, latitude[0])
        self.assertEqual(lat.decimal_degree, lat_dd)

        return

    def test_to_string(self):
        # North latitudes run 0,90 degrees
        lat = Latitude(latitude[0], latitude[1], latitude[2])
        self.assertEqual("N", lat.to_string("%H"))
        self.assertEqual("34.933", lat.to_string("%M")[:6])
        self.assertEqual("34.0", lat.to_string("%m"))
        self.assertEqual("12.582", lat.to_string("%D")[:6])
        self.assertEqual("12.0", lat.to_string("%d"))
        self.assertEqual("56.0", lat.to_string("%S"))

        return

    def test_custom_format(self):

        arg = Latitude(latitude[0], latitude[1], latitude[2])
        if isinstance(arg, Latitude):
            degree = str(int(arg.degree))
            decimal_minute = '{:05.2f}'.format(arg.decimal_minute)
            result = '{}{}'.format(degree, decimal_minute)
        self.assertEqual(result, '1234.93')
        return






if __name__ == '__main__':
    unittest.main(LatitudeTest())





class Test(object):
    def __init__(self, a=1, b=2):
        """_c is dependent on a and b. a and b are independent of eachother"""
        self._c = a + b / 2
        self._a = a
        self._b = b

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, value):
        self._a = value % 1 * 2
        self._b = self._a % 1 * 2
        self._c = value

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        self._a = value
        # self._b is unchanged (is not dependent on a)
        self._c = value + self._b / 2

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        # Self._a is independent of b
        self._b = value
        self._c = self._a + value / 2
