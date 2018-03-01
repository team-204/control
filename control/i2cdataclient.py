""" An IPC client using zmq to gather data from our i2c devices.

Two of the current devices we're using are utilizing i2c... Since there isn't
an easy way to do i2c in python we've written a c++ program that acts as a
data server. It waits for a request before performing reads and sending the
data as a string. The I2cDataClient class handles getting data from server and
returning it in a usable way.
"""
import re
import zmq


class I2cDataClient:
    """This class acts as a client to the data server."""
    def __init__(self, server_location):
        """Opens a connection to server_location."""
        self.__server_location = server_location
        self.__context = zmq.Context()
        self.__socket = self.__context.socket(zmq.REQ)
        self.__socket.connect(server_location)

    def read(self):
        """Request data from the data server and return it as a dictionary.

        This functions is a blocking function, a call to recv() blocks till
        data is returned.

        :returns: dictionary -- The data read from MPL3115A2. Looks like
                                {'temperature': 'temp', altitude: 'alt'}.
                                Note that 'temp' and 'alt' are strings. Also
                                note that the units are degrees Celcius and
                                meters (from sea level).

        """
        self.__socket.send(b'totally arbitrary request message')
        data_string = self.__socket.recv()
        match = re.match(r'Temperature: (\S+) Altitude: (\S+)', data_string)
        data = {'temperature': match.group(1), 'altitude': match.group(2)}
        return data
