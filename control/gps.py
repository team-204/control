"""Defines classes used to read and handle GPS data"""
import pynmea2
import serial


class GpsReadError(Exception):
    """Error for invalid gps reading"""
    def __init__(self, message, data):
        super(GpsReadError, self).__init__((message, data))


class GpsReading:
    """A data class for GPS reading attributes"""
    def __init__(self, latitude, longitude, altitude, time):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.time = time

    def __repr__(self):
        """Returns representation of GPS reading"""
        return '{}({}, {}, {}, {})'.format(self.__class__.__name__,
                                           self.latitude, self.longitude,
                                           self.time, self.altitude)

    def __eq__(self, other):
        """Compares if two GpsReadings are equal"""
        return (self.latitude == other.latitude and
                self.longitude == other.longitude and
                self.altitude == other.altitude and
                self.time == other.time)


class Gps:
    """A class for gathering GPS data via serial"""
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)

    def __repr__(self):
        """Returns representation of GPS"""
        return '{}({})'.format(self.__class__.__name__, self.ser)

    def read(self):
        """Returns a GpsReading object with the values supplied"""
        msg = None
        tries = 4
        # TODO: Add timeout for reads using signal library
        for attempt in range(1, tries + 1):
            try:
                while not isinstance(msg, pynmea2.GGA):
                    msg = pynmea2.parse(self.ser.readline())
            except pynmea2.ParseError:
                if attempt == tries:
                    raise GpsReadError('max number of parse attempts reached', attempt)
                else:
                    pass
            else:
                break
        return GpsReading(msg.latitude, msg.longitude, msg.altitude,
                          msg.timestamp)
