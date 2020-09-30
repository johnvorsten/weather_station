# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 16:41:41 2020

@author: z003vrzk
"""

# Python imports
import requests
import unittest

# Third party imports

# Local imports
from weather_underground import API_KEY, STATION_KEY, STATION_ID


#%%
host = 'https://api.weather.com/'
version = 'v2'
response_format='json'

# Present observations
url = host + version + '/pws/observations/current?stationId={}&format=' + response_format + '&units=e&apiKey={}'


header = {'Accept-Encoding':'gzip',
          # Cache control headers?
          }

def TestAPI(unittest.TestCase):

    def setUp(self):
        return None

    def test_present_observations(self):

        station_id = 'KTXHOUST2765'
        url_test = url.format(station_id, API_KEY)
        response = requests.get(url_test)

        # Read response header data
        status_code = response.status_code
        self.assertEqual(status_code, 200)

        # Read body
        weather = response.json()

        return None
