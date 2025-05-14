"""Message handling for the MCS application."""
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

from config import TIMESTAMP_FORMAT, TIMESTAMP_PRECISION


class MessageHandler:
    """Handles processing and formatting of incoming messages."""

    @classmethod
    def process_message(cls, message: Dict) -> Optional[Tuple[str, str, str]]:
        """Process an incoming message and extract relevant information.
        
        Args:
            message: Raw message dictionary from the server
            
        Returns:
            Optional tuple containing (message_name, timestamp, raw_data) or None if invalid
            
        Raises:
            TypeError: If message is not a dictionary
        """
        if not isinstance(message, dict):
            raise TypeError(f"Expected dict, got {type(message).__name__}")
            
        try:
            # Extract message name with fallback for both old and new formats
            message_name = str(message.get("MessageName", message.get("type", "Unknown"))).strip()
            
            # Get current timestamp with millisecond precision
            timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
            timestamp = timestamp[:-(6-TIMESTAMP_PRECISION)]  # Truncate to desired precision
            
            # Convert message to pretty-printed JSON
            raw_data = json.dumps(
                message,
                indent=2,
                default=str,  # Handle non-serializable types
                ensure_ascii=False  # Support non-ASCII characters
            )
            
            return message_name, timestamp, raw_data
            
        except (TypeError, ValueError, json.JSONEncodeError) as e:
            print(f"Error processing message: {e}")
            return None
