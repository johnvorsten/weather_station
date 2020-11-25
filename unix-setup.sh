#!/bin/bash

### Create virtual env ###
<<<<<<< HEAD
if apt list virtualenv; then
    echo "Virtualenv is already installed"
else
    apt-get install -y virtualenv
fi
	
if [ -d "$HOME/.virtualenvs/weather_station" ]; then
    echo "Virtual environment already exists at $HOME/.virtualenvs/weather_station"
else
    virtualenv -p /usr/bin/python3.7 "$HOME/.virtualenvs/weather_station"
=======
if apt list virtualenv; then
	echo "Virtualenv alraedy installed"
else
	apt install -y virtualenv
fi

if apt list python3; then
	echo "Python 3 already installed"
else
	apt install -y python3
fi

if [ -d "$HOME/.virtualenvs/weather_station" ]; then
	echo "Virtual environment already exists at $HOME/.virtualenvs/weather_station"
else
	virtualenv -p /usr/bin/python3 "$HOME/.virtualenvs/weather_station"
>>>>>>> ab29f74142af5353e25a9888207ff6f09c888e75
fi
source "$HOME/.virtualenvs/weather_station/bin/activate"

### Install python packages ###
pip install -r "$HOME/weather_station/requirements.txt"
<<<<<<< HEAD


if apt list virtualenv; then
    echo "Virtualenv is already installed";
fi
=======
>>>>>>> ab29f74142af5353e25a9888207ff6f09c888e75
