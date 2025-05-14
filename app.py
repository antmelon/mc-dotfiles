"""Main application module for the Mission Computer Simulator (MCS)."""

import asyncio
import logging
from typing import Dict, Optional, Type, TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer

from config import DEFAULT_HOST, DEFAULT_PORT, THEME_DARK, THEME_LIGHT
from interrogations import Interrogations
from main_menu import Menu
from message_handler import MessageHandler
from network.client import TCPClient

if TYPE_CHECKING:
    from main_menu import Menu

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCS(App):
    """Main application class for the Mission Computer Simulator."""

    # Class constants
    CSS_PATH = "main.tcss"
    SCREENS: Dict[str, Type[Screen]] = {
        "Main": Menu,
        "Interrogations": Interrogations,
    }
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("i", "push_screen('Interrogations')", "Interrogations"),
        ("q", "quit", "Quit application"),
    ]

    def __init__(self) -> None:
        """Initialize the MCS application."""
        super().__init__()
        self.theme = THEME_DARK
        self.tcp_client: Optional[TCPClient] = None
        self.message_handler = MessageHandler()
        self.main_menu: Optional[Menu] = None
        self._network_worker = None  # Background network worker
        
        # Store default connection settings
        self.default_host = DEFAULT_HOST
        self.default_port = DEFAULT_PORT

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        yield Footer()
        self.push_screen("Main")

    def on_mount(self) -> None:
        """Configure the application when it's mounted."""
        self.title = "Mission Computer Simulator (MCS)"
        self.sub_title = "Disconnected"
        self.main_menu = self.get_screen("Main")
        self._start_network_worker()
        logger.info("MCS application started")

    def on_unmount(self) -> None:
        """Clean up resources when the app is closed."""
        if self.tcp_client:
            self.tcp_client.disconnect()
        logger.info("MCS application shutting down")

    # Network-related methods
    
    def _start_network_worker(self) -> None:
        """Start the network worker if not already running."""
        if not self._network_worker or self._network_worker.is_finished:
            self._network_worker = self.run_worker(
                self._network_worker_task,
                name="network_worker",
                group="network",
                exclusive=True,
                exit_on_error=False,
            )
    
    async def _network_worker_task(self) -> None:
        """Background task to handle network operations."""
        while True:
            if self.tcp_client and hasattr(self.tcp_client, 'receive_data'):
                self.tcp_client.receive_data()
            await asyncio.sleep(0.01)  # Small sleep to prevent busy-waiting

    def connect_to_server(self, host: str, port: int) -> bool:
        """Connect to the TCP server.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            if self.tcp_client:
                self.tcp_client.disconnect()
            
            logger.info("Attempting to connect to %s:%s", host, port)
            self.tcp_client = TCPClient(host, port, self._on_message_received)
            
            if self.tcp_client.connect():
                self.sub_title = f"Connected to {host}:{port}"
                self._start_network_worker()
                logger.info("Successfully connected to server")
                return True
            return False
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            self.notify(error_msg, severity="error")
            return False

    def send_message(self, message: Dict) -> bool:
        """Send a message to the connected server.
        
        Args:
            message: Dictionary to send as JSON
            
        Returns:
            bool: True if message was sent successfully, False otherwise
            
        Raises:
            ValueError: If message is not a dictionary
        """
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary")
            
        if not self.tcp_client:
            logger.warning("Cannot send message - not connected to server")
            return False
            
        try:
            return self.tcp_client.send_message(message)
        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            logger.error(error_msg)
            self.notify(error_msg, severity="error")
            return False

    def _on_message_received(self, message: Dict) -> None:
        """Handle an incoming message from the server.
        
        Args:
            message: Received message as a dictionary
        """
        self.call_after_refresh(self._process_message_in_ui_thread, message)

    def _process_message_in_ui_thread(self, message: Dict) -> None:
        """Process a received message in the UI thread."""
        try:
            # Update main menu if it exists and can handle messages
            if self.main_menu and hasattr(self.main_menu, 'add_message'):
                self.main_menu.add_message(message)
            
            # Also update current screen if it's different from main menu
            current_screen = self.screen
            if (current_screen is not self.main_menu and 
                    hasattr(current_screen, 'add_message')):
                current_screen.add_message(message)
                
        except Exception as e:
            logger.error("Error processing message in UI: %s", e, exc_info=True)

    # Actions
    
    def action_toggle_dark(self) -> None:
        """Toggle between dark and light theme."""
        self.theme = THEME_LIGHT if self.theme == THEME_DARK else THEME_DARK
        logger.info("Theme toggled to %s", self.theme)
        
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main() -> None:
    """Run the MCS application."""
    try:
        app = MCS()
        app.run()
    except Exception as e:
        logger.critical("Fatal error in MCS application: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()

