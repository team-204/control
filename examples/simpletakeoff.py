"""Flies the drone up 10 meters, delays 30 seconds, and then lands.

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


def main(connection_string, target_altitude):
    """Takes the drone up and then lands."""
    # Setup logging
    logger = logging.getLogger('control')
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler('simpletakeoff.log')
    filehandler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(filehandler)
    logger.addHandler(console)

    # Connect to flight controller
    logger.debug("Starting program, attempting connection to flight controller.")
    vehicle_control = Controller(connection_string, baud=57600)

    if not SIMULATION:
        time.sleep(60)  # Sleep to avoid immediate takeoff on boot

    # Arm and takeoff
    logger.debug("Arming...")
    vehicle_control.arm()
    vehicle_control.takeoff(target_altitude)

    # Give time for user controller to takeover (if you desire to test controller takeover)
    logger.debug("Hovering for 30 seconds...")
    for second in range(30):
        vehicle_control.check_geofence(10, target_altitude + 10)
        if vehicle_control.vehicle.mode.name != "GUIDED":
            break
        time.sleep(1)

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
    time.sleep(5)  # Sleep just a little to make sure serial is available on system
    SIMULATION = False
    SITL = None
    CONNECTION_STRING = '/dev/ttyO4'
    if 'SIMULATION' in sys.argv:
        # This is a simulation
        SIMULATION = True
        import dronekit_sitl
        SITL = dronekit_sitl.start_default()
        CONNECTION_STRING = SITL.connection_string()
    main(CONNECTION_STRING, 10)
    if SIMULATION:
        SITL.stop()
