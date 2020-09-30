# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 15:39:34 2020

@author: z003vrzk
"""

# Python imports
import configparser
import requests
from datetime import datetime

# Third party imports

# Local imports

# Keys
config_path = './keys.env'
config = configparser.ConfigParser()
config.read(config_path)
sections = config.sections()
assert 'weather_underground' in sections
API_KEY = config['weather_underground']['API_KEY']
STATION_KEY = config['weather_underground']['STATION_KEY']
STATION_ID = config['weather_underground']['STATION_ID']
PASSWORD = config['weather_underground']['PASSWORD']

#%%
api_host = 'https://api.weather.com/'

# Present observations
url = api_host + 'v2/pws/observations/current?stationId={}&format=json&units=e&apiKey={}'

version = 'v2'
response_format='json'
header = {'Accept-Encoding':'gzip',
          # Cache control headers?
          }
units = {'altitude':['ft','m'],
         # feet, meters
         'temperature':['f','c'], # fahrenheit, celsius
         'pressure':['hg','mb'], # inches mercury, millibars mercury
         'precipitation_amount':['in','mm'], # inches, millimeters
         'distance':['ft','m'],
         'visibility':['mi','km'],
         'wind_speed':['mh','km'],
         'wave_height':['ft','mtr']}


def read_bacnet():
    """Read weather data from BACnet weather station"""
    humidity = None # TODO
    temperature = None # TODO
    co2 = None # TODO
    pressure = None # TODO

    data = {'humidity':humidity,
            'temperature':temperature,
            'co2':co2,
            'pressure':pressure,}

    return data


def format_data(data):
    """
    inputs
    -------
    data : (dict)
    outputs
    -------
    data : (dict)"""
    # Use 3 decimal places of accuracy for pressure
    data['pressure'] = "{0:.3f}".format(data['pressure'])

    # Use 2 decimal places of accuracy for temperature
    data['temperature'] = "{0:.2f}".format(data['temperature'])

    # Use whole numbers for humidity and co2
    data['humidity'] = "{0:1.0f}".format(data['humidity'])
    data['co2'] = "{0:1.0f}".format(data['co2'])

    return data


def post_station(url, data):
    """"""
    # Post URL
    post_base = 'https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
    cred = "&ID=" + STATION_ID + "&PASSWORD="+ PASSWORD
    # date = datetime.now().strftime('%Y%m%d%H%M')
    date = "&dateutc=now"
    action_str = "&action=updateraw"
    humidity_str = "&humidity=" + data['humidity']
    temperature_str = "&temperature=" + data['temperature']
    post_url = post_base + cred + date + humidity_str + temperature_str + action_str

    # Post data
    response = requests.get(post_url)


    return None









