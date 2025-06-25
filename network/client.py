"""TCP client for handling network communication with the server."""
import json
import logging
import socket
from queue import Queue
from typing import Callable, Dict, Optional

from config import RECEIVE_BUFFER_SIZE, SOCKET_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from typing import Callable, Dict, Optional, Any
from threading import Thread
from queue import Queue

class TCPClient:
    """TCP client that handles connection and message passing with the server."""

    def __init__(self, host: str, port: int, message_callback: Callable[[Dict], Any]):
        """Initialize the TCP client.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
            message_callback: Function to call when a message is received
            
        Raises:
            ValueError: If host is empty or port is out of range
        """
        if not host or not isinstance(host, str):
            raise ValueError("Host must be a non-empty string")
        if not isinstance(port, int) or not (0 < port <= 65535):
            raise ValueError("Port must be an integer between 1 and 65535")
            
        self.host = host
        self.port = port
        self.message_callback = message_callback
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.message_queue: Queue[Dict] = Queue()
        self._buffer = ""  # Buffer for incomplete messages
        self._message_thread: Optional[Thread] = None
        
        logger.info("TCPClient initialized for %s:%s", host, port)

    def connect(self) -> bool:
        """Connect to the server.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self.socket:
            logger.warning("Already connected to server")
            return False
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(SOCKET_TIMEOUT)
            self.socket.connect((self.host, self.port))
            self.running = True
            self._buffer = ""  # Reset buffer on new connection
            logger.info("Connected to server at %s:%s", self.host, self.port)
            return True
            
        except (socket.error, ConnectionRefusedError) as e:
            logger.error("Failed to connect to %s:%s - %s", 
                        self.host, self.port, str(e))
            self._cleanup_socket()
            return False

    def disconnect(self) -> None:
        """Disconnect from the server and clean up resources."""
        self.running = False
        self._cleanup_socket()
        logger.info("Disconnected from server")

    def _cleanup_socket(self) -> None:
        """Safely close and clean up the socket."""
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except (socket.error, OSError) as e:
                logger.debug("Error closing socket: %s", e)
            finally:
                self.socket = None

    def send_message(self, message: Dict) -> bool:
        """Send a JSON message to the server.
        
        Args:
            message: Dictionary to be sent as JSON
            
        Returns:
            bool: True if message was sent successfully, False otherwise
            
        Raises:
            ValueError: If message is not a dictionary
        """
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary")
            
        if not self.socket or not self.running:
            logger.warning("Cannot send message - not connected to server")
            return False
            
        try:
            message_str = json.dumps(message, ensure_ascii=False) + "\n"
            self.socket.sendall(message_str.encode('utf-8'))
            return True
            
        except (socket.error, json.JSONEncodeError) as e:
            logger.error("Failed to send message: %s", e)
            self.disconnect()
            return False

    def receive_data(self) -> None:
        """Receive and process data from the server in a non-blocking way."""
        if not self.running or not self.socket:
            return
            
        try:
            while True:  # Process all available data
                try:
                    data = self.socket.recv(RECEIVE_BUFFER_SIZE)
                    if not data:
                        logger.info("Connection closed by server")
                        self.disconnect()
                        break
                        
                    self._buffer += data.decode('utf-8', errors='replace')
                    self._process_buffer()
                    
                except socket.timeout:
                    # No more data available
                    break
                    
        except (socket.error, ConnectionResetError) as e:
            logger.error("Network error: %s", e)
            self.disconnect()
            
    def _process_buffer(self) -> None:
        """Process the receive buffer and extract complete messages."""
        while "\n" in self._buffer:
            message_str, self._buffer = self._buffer.split("\n", 1)
            if not message_str.strip():
                continue
                
            try:
                message = json.loads(message_str)
                if self.message_callback and isinstance(message, dict):
                    self.message_callback(message)
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON received: %s - %s", message_str, e)
