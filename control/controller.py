""" A thin wrapper for using the dronekit library.

The main motivation behind putting this into its own class is that ability
to unit test this with the dronekit sitl and to make our main logic somewhat
easier to decouple from the dronekit library if the time ever comes.
"""
import time
import dronekit


class Controller:
    """This class acts as a wrapper for dronekit and controls the vehicle."""
    def __init__(self, connection_string, baud=None):
        """Open a connection to the vehicle.

        Args:
            connection_string (str): Location of the drone.
            baud (int): Baudrate of serial connection (if applicable).
        """
        self.connection_string = connection_string
        self.vehicle = None
        if baud:
            self.vehicle = dronekit.connect(self.connection_string,
                                            wait_ready=True, baud=57600)
        else:
            self.vehicle = dronekit.connect(self.connection_string,
                                            wait_ready=True)

    def arm(self):
        """Sets the mode to guided and arms the copter for flight."""
        # Arm the copter
        self.vehicle.mode = dronekit.VehicleMode("GUIDED")
        while not self.vehicle.armed:
            print("Trying to arm...")
            self.vehicle.armed = True
            time.sleep(1)
