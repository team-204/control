"""Flies the drone in a "+" shape formation.

Uses the ttyO4 connection (UART4) on the beaglebone. Installing the appropriate
service file (also located in examples) allows for this to start on boot. A 1
minute delay exists in order to allow the user to setup the and secure the
device before attempting flight. You better be clear after 1 minute.
This can also be ran as a simulation by appending SIMULATION as a command line
argument. This allows you to test the functionality easily.
"""
import logging
import sys
import time
from control.controller import Controller
from control.gps import get_location_offset, get_distance
from control.helper import location_global_relative_to_gps_reading, gps_reading_to_location_global


def main(target_altitude, radius):
    """Takes the drone up and then lands."""
    # Setup logging
    logger = logging.getLogger('control')
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler('simpleflight.log')
    filehandler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(filehandler)
    logger.addHandler(console)

    # Connect to the drone
    logger.debug("Starting program, attempting connection to flight controller.")
    vehicle_control = Controller(CONNECTION_STRING, baud=57600)

    # Sleep to avoid immediate takeoff on boot
    if not SIMULATION:
        time.sleep(60)

    # Arm and takeoff
    logger.debug("Arming...")
    vehicle_control.arm()
    vehicle_control.takeoff(target_altitude)

    # Create points
    home_gps = location_global_relative_to_gps_reading(vehicle_control.home)
    north_gps = get_location_offset(home_gps, radius, 0)
    south_gps = get_location_offset(home_gps, -1*radius, 0)
    east_gps = get_location_offset(home_gps, 0, radius)
    west_gps = get_location_offset(home_gps, 0, -1*radius)
    points = [north_gps, south_gps, east_gps, west_gps, home_gps]

    # Transform GpsReading to LocationGlobalRelative
    for index, point in enumerate(points):
        points[index] = gps_reading_to_location_global(point)
        logger.debug("Destination {}: {}".format(index, points[index]))

    # Go to the points
    if vehicle_control.vehicle.mode.name == "GUIDED":
        logger.debug("Flying to points...")
        for point in points:
            if vehicle_control.vehicle.mode.name != "GUIDED":
                break
            vehicle_control.goto(point)

            # Wait for vehicle to reach destination before updating the point
            for sleep_time in range(10):
                if vehicle_control.vehicle.mode.name != "GUIDED":
                    break
                vehicle_control.log_flight_info(point)
                # Don't let the vehicle go too far (could be stricter if get_distance
                # improved and if gps was more accurate. Also note that altitude
                # is looser here to avoid false landings (since gps altitude not
                # accurate at all).
                vehicle_control.check_geofence(radius*2, target_altitude+20)
                current = vehicle_control.vehicle.location.global_relative_frame
                current_reading = location_global_relative_to_gps_reading(current)
                point_reading = location_global_relative_to_gps_reading(point)
                distance = get_distance(current_reading, point_reading)
                if distance < 1:
                    logger.debug('Destination Reached')
                    time.sleep(3)
                    break
                time.sleep(3)

    # Land if still in guided mode (i.e. no user takeover, no flight controller failure)
    if vehicle_control.vehicle.mode.name == "GUIDED":
        logger.debug("Landing...")
        vehicle_control.land()

    # Always keep the programming running and logging until the vehicle is disarmed
    while vehicle_control.vehicle.armed:
        vehicle_control.log_flight_info()
        time.sleep(3)
    logger.debug("Finshed program.")
    sys.exit(0)


if __name__ == "__main__":
    time.sleep(15)  # Sleep just a little to make sure serial is available on system
    SIMULATION = False
    SITL = None
    CONNECTION_STRING = '/dev/ttyO4'
    if 'SIMULATION' in sys.argv:
        # This is a simulation
        SIMULATION = True
        import dronekit_sitl
        SITL = dronekit_sitl.start_default()
        CONNECTION_STRING = SITL.connection_string()
    main(10, 10)
