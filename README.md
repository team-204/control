# control
[![Build Status](https://travis-ci.org/team-204/control.svg?branch=master)](https://travis-ci.org/team-204/control)
Dronekit based application for controlling our UAV

Python 2 program for autonomous UAV flight and data collection to a ground control station. 
This application connects to a Pixhawk flight controller via a serial connection and leverages
the dronekit library for communication between the program and the UAV. It connects to a
zeromq server for I2C data collection using a unix socket. It also connects to a radio communication
module using a serial connection for wireless transmission to a ground control station.

The entry point for this application is [main.py](control/main.py). A high level overview of this script is as follows:
 - Sets up logging
 - Connects to all devices
 - Awaits waypoints from ground control station (detailed in [main.py](control/main.py))
 - Arms UAV
 - Takes off to 10 meters
 - Flies to each waypoint
    - Transmits temperature, time, location data to ground control station every second
 - Returns to home
 - Lands
