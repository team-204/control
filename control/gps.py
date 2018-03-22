"""Defines classes used to read and handle GPS data"""
import math
import pynmea2
import serial


def get_location_offset(origin, x_offset, y_offset):
    """
    Returns a GpsReading with calculated GPS latitude and longitude coordinates given a
    x and y offset in meters from original GPS coordinates. It keeps the same altitude as
    original GpsReading and passes in a null timestamp.
    Sources:
    https://github.com/dronekit/dronekit-python/blob/master/examples/mission_basic/mission_basic.py
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """

    earth_radius = 6378137.0  # Radius of "spherical" earth

    # Offsets coordinates in radians
    lat_offset = x_offset / earth_radius
    lon_offset = y_offset / (earth_radius*math.cos(math.pi*origin.latitude/180))

    # New position in decimal degrees
    new_lat = origin.latitude + (lat_offset * 180/math.pi)
    new_lon = origin.longitude + (lon_offset * 180/math.pi)
    return GpsReading(new_lat, new_lon, origin.altitude, 0)


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
        self.ser = serial.Serial(port, baudrate, timeout=1)

    def __repr__(self):
        """Returns representation of GPS"""
        return '{}({})'.format(self.__class__.__name__, self.ser)

    def read(self):
        """Returns a GpsReading object with the values supplied"""
        msg = None
        tries = 4
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
