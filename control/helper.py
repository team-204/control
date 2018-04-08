"""Defines some helper functions."""
from dronekit import LocationGlobalRelative
from gps import GpsReading


def location_global_relative_to_gps_reading(global_relative):
    """Converts a LocationGlobalRelative to a GpsReading."""
    return GpsReading(global_relative.lat, global_relative.lon,
                      global_relative.alt, 0)


def gps_reading_to_location_global(gps_reading):
    """Converts a GpsReading to a LocationGlobalRelative."""
    return LocationGlobalRelative(gps_reading.latitude,
                                  gps_reading.longitude, gps_reading.altitude)
