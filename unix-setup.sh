#!/bin/bash

### Install Dependencies ###
installed_check=$(command -v virtualenv)
if [ -n $installed_check ]; then
	echo "Virtualenv is already installed"
else
	apt install -y virtualenv
fi

# Check if Python 3.8.6 is installed
installed_check=$(command -v python3.8)
if [ -n $installed_check ]; then
	echo "Python 3.8 already installed"
else
	# Build and install python 3.8.6 in subshell for directory change
	(
	apt update
	apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev
	cd /tmp/
	wget -P /tmp/ https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tar.xz
	tar -xf /tmp/Python-3.8.6.tar.xz --directory=/tmp/
	cd /tmp/Python-3.8.6
	/tmp/Python-3.8.6/configure --enable-optimizations
	# Makefile will be created in /tmp/Python-3.8.6
	make -f /tmp/makefile -j 4
	make altinstall
	)
	# Verify installation
	installed_check=$(command -v python3.8)
	if [ -n $installed_check ]; then
		echo "Python 3.8 was not installed"
		exit 2
	fi
fi

### Create virtual env ###
if [ -d "$HOME/.virtualenvs/weather_station" ]; then
	echo "Virtual environment already exists at $HOME/.virtualenvs/weather_station"
else
	virtualenv -p python3.8 "$HOME/.virtualenvs/weather_station"
fi
source "$HOME/.virtualenvs/weather_station/bin/activate"

### Install python packages ###
pip install -r "$HOME/weather_station/requirements.txt"

### Startup Supervisor ###
cp "$HOME/weather_station/supervisor_weather.conf" "/etc/supervisor/conf.d"
"$BINDIR/supervisord"
# To restart supervisord
# kill -HUP
# Restart programs
# supervsiorctl stop all
# supervisorctl start all
