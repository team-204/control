"""Defines classes used to read and handle GPS data"""
import math
import pynmea2
import serial


EARTH_RADIUS = 6371001.0  # Average radius of spherical earth in meters


def get_location_offset(origin, north_offset, east_offset):
    """
    Returns a GpsReading with calculated GPS latitude and longitude coordinates given a
    north and east offset in meters from original GPS coordinates. Note that
    an x offset corresponds to an east offset and a y offset corresponds to a north offset.
    For the new reading, the same altitude as the original GpsReading is kept and
    a null timestamp is used.

    Sources:
    https://github.com/dronekit/dronekit-python/blob/master/examples/mission_basic/mission_basic.py
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """

    # Offsets coordinates in radians
    lat_offset = north_offset / EARTH_RADIUS
    lon_offset = east_offset / (EARTH_RADIUS*math.cos(math.pi*origin.latitude/180))

    # New position in decimal degrees
    new_lat = origin.latitude + (lat_offset * 180/math.pi)
    new_lon = origin.longitude + (lon_offset * 180/math.pi)
    return GpsReading(new_lat, new_lon, origin.altitude, 0)


def get_relative_from_location(origin, point):
    """
    Returns the relative (x, y) values in meters of the GpsReading point based
    on the origin GpsReading (which is considered (0,0)). The inverse of
    get_location_offset.
    """
    lon_offset = (point.longitude - origin.longitude) * (math.pi / 180)
    lat_offset = (point.latitude - origin.latitude) * (math.pi / 180)
    x = lon_offset * (EARTH_RADIUS*math.cos(math.pi*origin.latitude/180))
    y = lat_offset * EARTH_RADIUS
    return (x, y)


def get_distance(reading_1, reading_2):
    """
    Returns distance in meters between two GpsReadings.
    The latitude is fairly accurate in this calculation
    but the longitude is off.

    Source:
    https://github.com/dronekit/dronekit-python/blob/master/examples/mission_basic/mission_basic.py
    """
    lat_diff = reading_1.latitude - reading_2.latitude
    lon_diff = reading_1.longitude - reading_2.longitude
    return math.sqrt((lat_diff*lat_diff) + (lon_diff*lon_diff)) * 1.113195e5


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
                                           self.altitude, self.time)

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
        max_tries = 4
        for attempt in range(1, max_tries + 1):
            try:
                while not isinstance(msg, pynmea2.GGA):
                    msg = pynmea2.parse(self.ser.readline())
            except pynmea2.ParseError:
                if attempt == max_tries:
                    raise GpsReadError('max number of parse attempts reached', attempt)
                else:
                    pass
            else:
                break
        return GpsReading(msg.latitude, msg.longitude, msg.altitude,
                          msg.timestamp)
