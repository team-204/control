import pynmea2
import serial


class GpsReading:
    """A data class for GPS reading attributes"""
    def __init__(self, latitude, longitude, time, altitude):
        self.latitude = latitude
        self.longitude = longitude
        self.time = time
        self.altitude = altitude


class Gps:
    """A class for gathering GPS data via serial"""
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)

    def read(self):
        """Returns a GpsReading object with the values supplied"""
        msg = None
        # TODO: Add try except chain to catch any dirty GPS output exceptions
        while not isinstance(msg, pynmea2.GGA):
            msg = pynmea2.parse(self.ser.readline())
        return GpsReading(msg.latitude, msg.longitude, msg.timestamp,
                          msg.altitude)
