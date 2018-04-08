""" A thin wrapper for using the dronekit library.

The main motivation behind putting this into its own class is that ability
to unit test this with the dronekit sitl and to make our main logic somewhat
easier to decouple from the dronekit library if the time ever comes.
"""
import logging
import time
import dronekit
from gps import get_distance
from helper import location_global_relative_to_gps_reading


class Controller:
    """This class acts as a wrapper for dronekit and controls the vehicle."""
    def __init__(self, connection_string, baud=None):
        """Open a connection to the vehicle.

        Args:
            connection_string (str): Location of the drone.
            baud (int): Baudrate of serial connection (if applicable).
        """
        self.logger = logging.getLogger(__name__)
        self.connection_string = connection_string
        self.vehicle = None
        if baud:
            self.logger.debug('Attempting connection to %s',
                              connection_string)
            self.vehicle = dronekit.connect(self.connection_string,
                                            wait_ready=True, baud=baud)
        else:
            self.logger.debug('Attempting connection to %s at baud %s',
                              connection_string, baud)
            self.vehicle = dronekit.connect(self.connection_string,
                                            wait_ready=True)
        self.logger.debug('Connected.')

        def _vehicle_state_callback(vehicle, attribute, value):
            """Logs vehicle state changes."""
            self.logger.debug("Attribute {}: {}".format(attribute, value))
        self.vehicle.add_attribute_listener('armed',
                                            _vehicle_state_callback)
        self.vehicle.add_attribute_listener('mode',
                                            _vehicle_state_callback)
        self.home = None  # Set right after arming (GPS can be trusted then)

    def arm(self):
        """Sets the mode to guided and arms the copter for flight."""
        while not self.vehicle.is_armable:
            self.logger.debug('Waiting for vehicle to initialise...')
            time.sleep(5)
        # Arm the copter
        self.vehicle.mode = dronekit.VehicleMode("GUIDED")
        while not self.vehicle.armed:
            self.logger.debug('Trying to arm...')
            self.vehicle.armed = True
            time.sleep(1)
        self.home = self.vehicle.location.global_relative_frame

    def takeoff(self, target_altitude):
        """Takes off the copter (must be armed first) to the target altitude.
        This function blocks until the height has been reached or takeoff
        has been cancelled by the user.
        """
        self.logger.debug("Attempting simple takeoff to {} m...".format(target_altitude))
        self.vehicle.simple_takeoff(target_altitude)
        self.home.alt = target_altitude  # This way home isn't 0 meters high when calling goto

        # Wait till target altitude reached
        while True:
            time.sleep(3)
            self.log_flight_info()
            self.check_geofence(10, target_altitude + 10)
            if self.vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
                self.logger.debug("Reached target altitude")
                break
            elif self.vehicle.mode.name != "GUIDED":
                # User took over control or geofence triggered
                break
        return

    def log_flight_info(self, destination=None):
        """Logs some info from the vehicle."""
        current_location = self.vehicle.location.global_relative_frame
        self.logger.debug("{}".format(current_location))
        self.logger.debug("Velocity: {}".format(self.vehicle.velocity))
        self.logger.debug("Groundspeed: {}".format(self.vehicle.groundspeed))
        self.logger.debug("Airspeed: {}".format(self.vehicle.airspeed))
        if destination:
            current_reading = location_global_relative_to_gps_reading(current_location)
            destination_reading = location_global_relative_to_gps_reading(destination)
            distance = get_distance(destination_reading, current_reading)
            self.logger.debug("Distance from destination: {}".format(distance))

    def check_geofence(self, max_distance, max_altitude):
        """Ensures the vehicle stays within our geofence (basically a cyclinder
        around the takeoff location)."""
        current = location_global_relative_to_gps_reading(
                    self.vehicle.location.global_relative_frame)
        home = location_global_relative_to_gps_reading(self.home)
        distance = get_distance(home, current)
        if distance > max_distance:
            self.logger.critical("Exceeded distance limit")
            self.logger.critical("Max Distance: {}".format(max_distance))
            self.logger.critical("Current Distance: {}".format(distance))
            if self.vehicle.mode.name == "GUIDED":
                self.logger.critical("LANDING...")
                self.land()
        elif current.altitude > max_altitude:
            self.logger.critical("Exceeded altitude limit")
            self.logger.critical("Max Altitude: {}".format(max_altitude))
            self.logger.critical("Current Altitude: {}".format(current.altitude))
            if self.vehicle.mode.name == "GUIDED":
                self.logger.critical("LANDING...")
                self.land()

    def goto(self, point):
        """Tells the drone to goto to a point (doesn't block, user responsible
        for verifying point is reached).

        point: expected to be a LocationGlobalRelative.
        """
        self.logger.debug("Going to destination: {}".format(point))
        self.vehicle.simple_goto(point)

    def land(self):
        """Lands the drone and blocks until landed."""
        self.logger.debug("Landing...")
        self.vehicle.mode = dronekit.VehicleMode("LAND")
        while True:
            time.sleep(3)
            self.log_flight_info()
            self.logger.debug("{}".format(self.vehicle.location.global_relative_frame))
            if self.vehicle.location.global_relative_frame.alt < 1:
                self.logger.debug("Reached Ground")
                break
            if self.vehicle.armed is False:
                self.logger.debug("Reached Ground (assuming since no longer armed)")
                break
