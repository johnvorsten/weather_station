#!/bin/bash

### Create virtual env ###
if apt list virtualenv; then
    echo "Virtualenv is already installed"
else
    apt-get install -y virtualenv
fi
	
if [ -d "$HOME/.virtualenvs/weather_station" ]; then
    echo "Virtual environment already exists at $HOME/.virtualenvs/weather_station"
else
    virtualenv -p /usr/bin/python3.7 "$HOME/.virtualenvs/weather_station"
fi
source "$HOME/.virtualenvs/weather_station/bin/activate"

### Install python packages ###
pip install -r "$HOME/weather_station/requirements.txt"


if apt list virtualenv; then
    echo "Virtualenv is already installed";
fi