"""Configuration constants for the MCS application."""
from typing import Dict, List, Tuple

# Network settings
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 9000
SOCKET_TIMEOUT: float = 0.1
RECEIVE_BUFFER_SIZE: int = 4096

# UI Settings
THEME_DARK: str = "textual-dark"
THEME_LIGHT: str = "textual-light"

# Table Configuration
TABLE_COLUMNS: List[Tuple[str, str]] = [
    ("Message Name", "message_name"),
    ("Time", "time"),
    ("Raw", "raw"),
]

# CSS Classes
CSS_CLASSES = {
    "sidebar_label": "sidebar-label",
    "sidebar_container": "sidebar-container",
    "bordered_container": "bordered-container",
    "left_placeholder": "left-placeholder",
    "connection_container": "connection-container",
}

# Message Formats
TIMESTAMP_FORMAT: str = "%H:%M:%S.%f"
TIMESTAMP_PRECISION: int = 3  # milliseconds
