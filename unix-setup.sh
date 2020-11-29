#!/bin/bash

### Create virtual env ###
if apt list virtualenv; then
	echo "Virtualenv alraedy installed"
else
	apt install -y virtualenv
fi

if apt list python3.8; then
	echo "Python 3.8 already installed"
else
	apt update
	apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3=dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev
	curl -O https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tar.xz
	tar -xf Python-3.8.6.tar.xz
	cd Python-3.8.6
	./configure --enable-optimizations
	make -j 4
	make altinstall
	# Verify installation
	if ! python3.8 --version; then
		echo "Python 3.8 was not installed"
	fi
fi

if [ -d "$HOME/.virtualenvs/weather_station" ]; then
	echo "Virtual environment already exists at $HOME/.virtualenvs/weather_station"
else
	virtualenv -p /usr/bin/python3.8 "$HOME/.virtualenvs/weather_station"
fi
source "$HOME/.virtualenvs/weather_station/bin/activate"

### Install python packages ###
pip install -r "$HOME/weather_station/requirements.txt"

if apt list virtualenv; then
    echo "Virtualenv is already installed";
fi
