"""Main program for autonomous drone flight and sensor data logging.

Uses the ttyO4 connection (UART4) on the beaglebone to connect to a Pixhawk flight controller.
Uses the ttyO1 connection (UART1) to connect to a xBee wireless communication module.
Uses tcp://localhost:5555 to connect to zmq server for reading i2c sensor data.
Installing the appropriate main.service file allows for this to start on boot.
"""

import logging
import sys
import time
import dronekit
from control.communication import Communication
from control.controller import Controller
from control.i2cdataclient import I2cDataClient
from control.gps import get_location_offset, get_distance, get_relative_from_location
from control.helper import location_global_relative_to_gps_reading, gps_reading_to_location_global

MAX_RADIUS = 50
MAX_ALTITUDE = 20
MIN_ALTITUDE = 3


def create_waypoints(logger, com, start_location, waypoints):
    start_gps = location_global_relative_to_gps_reading(start_location)
    location_points = []
    for point in waypoints:
        x = point[u'x']
        y = point[u'y']
        z = point[u'z']
        gps_waypoint = get_location_offset(start_gps, y, x)
        gps_waypoint.altitude = z
        if get_distance(start_gps, gps_waypoint) > MAX_RADIUS:
            logger.critical("Waypoint is {}".format(point))
            logger.critical("Waypoint exceeds max allowed radius of {}m".format(MAX_RADIUS))
            com.send("Waypoint is {}".format(point))
            com.send("Waypoint exceeds max allowed radius of {}m".format(MAX_RADIUS))
            return None
        elif gps_waypoint.altitude > MAX_ALTITUDE:
            logger.critical("Waypoint is {}".format(point))
            logger.critical("Waypoint exceeds max allowed altitude of {}m".format(MAX_ALTITUDE))
            com.send("Waypoint is {}".format(point))
            com.send("Waypoint exceeds max allowed altitude of {}m".format(MAX_ALTITUDE))
            return None
        elif gps_waypoint.altitude < MIN_ALTITUDE:
            logger.critical("Waypoint is {}".format(point))
            logger.critical("Waypoint under min allowed altitude of {}m".format(MIN_ALTITUDE))
            com.send("Waypoint is {}".format(point))
            com.send("Waypoint under min allowed altitude of {}m".format(MIN_ALTITUDE))
            return None
        location_points.append(gps_reading_to_location_global(gps_waypoint))
    return location_points


def package_data(home, location, data_client):
    data = {}
    location_gps = location_global_relative_to_gps_reading(location)
    home_gps = location_global_relative_to_gps_reading(home)
    x, y = get_relative_from_location(home_gps, location_gps)
    data[u'x'] = x
    data[u'y'] = y
    data[u'z'] = location.alt
    i2c_data = data_client.read()
    data[u'temp'] = float(i2c_data['temperature'])
    data[u'lat'] = location.lat
    data[u'lon'] = location.lon
    data[u'time'] = time.time()
    return data


def main():
    """Takes the drone up and then lands."""
    # Setup logging
    logger = logging.getLogger('control')
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler('main.log')
    filehandler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(filehandler)
    logger.addHandler(console)

    # Connect to xBee
    com = Communication(COM_CONNECTION_STRING, 0.1)
    logger.debug("Connected to wireless communication receiver")
    com.send(u"Connected to wireless communication receiver")

    # Connect to i2c data server
    data_client = I2cDataClient("tcp://localhost:5555")
    if not data_client.read():
        logger.critical("Can't connect to zmq data server")
        com.send(u"Can't connect to zmq data server")
        sys.exit(1)

    # Connect to the drone
    logger.debug("Starting program, attempting connection to flight controller.")
    com.send(u"Starting program, attempting connection to flight controller")
    vehicle_control = None
    try:
        vehicle_control = Controller(PIXHAWK_CONNECTION_STRING, baud=57600, com=com)
        logger.debug("Connected to flight controller")
        com.send(u"Connected to flight controller")
    except dronekit.APIException as err:
        logger.critical("dronekit.APIException: {}".format(err))
        logger.critical("Could not connect to flight controller.")
        com.send(u"Could not connect to flight controller.")
        sys.exit(1)

    # Wait until the waypoints flight path is received from GCS
    logger.debug("Waiting to receive flight path from GCS")
    com.send(u"Waiting to receive flight path from GCS")
    waypoints = com.receive()
    while not waypoints:
        waypoints = com.receive()

    # Create points
    start_location = vehicle_control.vehicle.location.global_relative_frame
    points = create_waypoints(logger, com, start_location, waypoints)

    if not points:
        logger.critical("Invalid points received from GCS")
        com.send(u"Invalid points received from GCS")
        sys.exit(1)

    # Arm and takeoff
    vehicle_control.arm()
    vehicle_control.takeoff(10)
    points.append(vehicle_control.home)

    # Log points
    for index, point in enumerate(points):
        logger.debug("Destination {}: {}".format(index, point))

    # Go to the points
    if vehicle_control.vehicle.mode.name == "GUIDED":
        logger.debug("Flying to points...")
        for point in points:
            com.send(u"Destination: {}".format(point))
            if vehicle_control.vehicle.mode.name != "GUIDED":
                com.send(u"Mode no longer guided")
                break
            vehicle_control.goto(point)

            # Wait for vehicle to reach destination before updating the point
            for sleep_time in range(10):
                if vehicle_control.vehicle.mode.name != "GUIDED":
                    com.send(u"Mode no longer guided")
                    break
                vehicle_control.log_flight_info(point)
                data_for_gcs = package_data(vehicle_control.home,
                                            vehicle_control.vehicle.location.global_relative_frame,
                                            data_client)
                com.send(data_for_gcs)
                # Don't let the vehicle go too far (could be stricter if get_distance
                # improved and if gps was more accurate. Also note that altitude
                # is looser here to avoid false landings (since gps altitude not
                # accurate at all).
                vehicle_control.check_geofence(MAX_RADIUS+10, MAX_ALTITUDE+10)
                current = vehicle_control.vehicle.location.global_relative_frame
                current_reading = location_global_relative_to_gps_reading(current)
                point_reading = location_global_relative_to_gps_reading(point)
                distance = get_distance(current_reading, point_reading)
                if distance < 1:
                    logger.debug('Destination Reached')
                    com.send(u"Destination Reached")
                    time.sleep(5)
                    break
                time.sleep(1)

    # Land if still in guided mode (i.e. no user takeover, no flight controller failure)
    if vehicle_control.vehicle.mode.name == "GUIDED":
        vehicle_control.land()

    # Always keep the programming running and logging until the vehicle is disarmed
    while vehicle_control.vehicle.armed:
        vehicle_control.log_flight_info()
        data_for_gcs = package_data(vehicle_control.home,
                                    vehicle_control.vehicle.location.global_relative_frame,
                                    data_client)
        time.sleep(1)

    # Program end
    logger.debug("Finished program.")
    com.send("Finished program.")
    sys.exit(0)


if __name__ == "__main__":
    PIXHAWK_CONNECTION_STRING = '/dev/ttyO4'
    COM_CONNECTION_STRING = '/dev/ttyO1'
    main()
