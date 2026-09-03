import unittest
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from unittest.mock import patch

from inout_tracker.bluetooth import BluetoothctlScanner
from inout_tracker.dashboard import handler_factory


class DisconnectTests(unittest.TestCase):
    def _handler(self) -> BaseHTTPRequestHandler:
        handler_class = handler_factory(Path("config.yaml"), BluetoothctlScanner(1))
        handler = handler_class.__new__(handler_class)
        handler.client_address = ("127.0.0.1", 54321)
        handler.close_connection = False
        return handler

    def test_client_disconnect_does_not_propagate(self) -> None:
        for error in (BrokenPipeError, ConnectionResetError):
            with self.subTest(error=error.__name__):
                handler = self._handler()
                with patch.object(BaseHTTPRequestHandler, "handle_one_request", side_effect=error):
                    handler.handle_one_request()
                self.assertTrue(handler.close_connection)

    def test_other_errors_still_propagate(self) -> None:
        handler = self._handler()
        failure = patch.object(
            BaseHTTPRequestHandler, "handle_one_request", side_effect=OSError("boom")
        )
        with failure, self.assertRaises(OSError):
            handler.handle_one_request()


if __name__ == "__main__":
    unittest.main()
