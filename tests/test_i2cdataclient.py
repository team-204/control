"""Tests the i2cdataclient module."""
import os
import sys
import unittest
from mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import control.i2cdataclient


class I2cDataClientTest(unittest.TestCase):
    @patch('zmq.Context')
    def test_data_string_correct(self, mock_context_class):
        """Confirms we're parsing strings correctly with re."""
        # Jump some hoops to set the return data for recv()
        context_mock = mock_context_class.return_value
        socket_mock = context_mock.socket.return_value
        socket_mock.recv.return_value = 'Temperature: 0 Altitude: 100'

        client = control.i2cdataclient.I2cDataClient('connection_string')
        data = client.read()
        expected_data = {'temperature': '0', 'altitude': '100'}
        self.assertEqual(data, expected_data)
