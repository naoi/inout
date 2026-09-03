class InOutError(Exception):
    """Base exception for expected application failures."""


class ConfigurationError(InOutError):
    """Raised when configuration is missing or invalid."""


class BluetoothError(InOutError):
    """Raised when the Bluetooth adapter or BlueZ command fails."""


class SheetsError(InOutError):
    """Raised when Google Sheets cannot be read or updated."""
