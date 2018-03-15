"""Tests the controller module using the simulator."""
import unittest
import dronekit_sitl
import control.controller


class ControllerTest(unittest.TestCase):
    """Tests the controller in charge of the drone itself."""
    def setUp(self):
        """Setup the drone simulator."""
        self.sitl = dronekit_sitl.start_default()
        self.connection = self.sitl.connection_string()
        self.controller = control.controller.Controller(self.connection)

    def tearDown(self):
        """Stop the simulator."""
        self.sitl.stop()
        self.sitl = None
        self.connection = None

    def test_vehicle_connection(self):
        """Confirm that the vehicle connects."""
        self.assertIsNotNone(self.controller)
        self.assertIsNotNone(self.controller.vehicle)

    def test_vehicle_arm_success(self):
        """Confirms that arm actually arms."""
        self.controller.arm()
        self.assertEqual(self.controller.vehicle.armed, True)
