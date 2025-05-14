"""Main menu screen for the MCS application."""

import json
import os
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Set, Tuple

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, DataTable, Footer, Header, Input, Label

from config import CSS_CLASSES as CSS, DEFAULT_HOST, DEFAULT_PORT, TABLE_COLUMNS


class Menu(Screen):
    """Main menu screen with navigation and connection controls."""

    # Table columns from config
    TABLE_COLUMNS: ClassVar[List[Tuple[str, str]]] = TABLE_COLUMNS
    
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the main menu screen."""
        super().__init__(*args, **kwargs)
        self.table: Optional[DataTable] = None
        self.ip_input: Optional[Input] = None
        self.port_input: Optional[Input] = None
        self.interrogation_button: Optional[Button] = None
        self.save_checkbox: Optional[Checkbox] = None
        self.filename_input: Optional[Input] = None
        
        # File handling
        self._file_queue = queue.Queue()
        self._file_worker_running = False
        self._file_worker_thread: Optional[threading.Thread] = None
        self._current_file = None
        self._messages_since_last_flush = 0
        self._last_flush_time = 0
        self._file_lock = threading.Lock()

    def compose(self) -> ComposeResult:
        """Compose the main menu layout."""
        yield Header()
        yield Footer()
        yield from self._compose_layout()

    def on_mount(self) -> None:
        """Configure the screen when it's mounted."""
        # Initialize the data table
        self.table = self.query_one(DataTable)
        self.table.add_columns(*(col[0] for col in self.TABLE_COLUMNS))
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        
        # Set default connection values
        if self.ip_input and self.port_input:
            self.ip_input.value = getattr(self.app, "default_host", DEFAULT_HOST)
            self.port_input.value = str(getattr(self.app, "default_port", DEFAULT_PORT))
        
        # Start file worker thread
        self._start_file_worker()
    
    def on_unmount(self) -> None:
        """Clean up resources when the screen is unmounted."""
        self._stop_file_worker()
    
    def _start_file_worker(self) -> None:
        """Start the background file writer thread."""
        if self._file_worker_thread and self._file_worker_thread.is_alive():
            return
            
        self._file_worker_running = True
        self._file_worker_thread = threading.Thread(
            target=self._file_writer_loop,
            daemon=True,
            name="file-writer"
        )
        self._file_worker_thread.start()
    
    def _stop_file_worker(self) -> None:
        """Stop the background file writer thread and clean up."""
        self._file_worker_running = False
        if self._file_worker_thread and self._file_worker_thread.is_alive():
            self._file_worker_thread.join(timeout=2.0)
        self._close_file()
    
    def _get_save_directory(self) -> Path:
        """Get or create the save directory."""
        save_dir = Path.home() / "mcs_saved_data"
        save_dir.mkdir(exist_ok=True, parents=True)
        return save_dir
    
    def _get_current_filename(self) -> str:
        """Get the current filename from the input field."""
        if not self.filename_input or not self.filename_input.value:
            return f"mcs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        return self.filename_input.value
    
    def _open_file(self) -> None:
        """Open or create the save file."""
        if self._current_file is not None:
            return
            
        try:
            save_dir = self._get_save_directory()
            filename = self._get_current_filename()
            filepath = save_dir / filename
            
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Open in append mode to preserve existing data
            self._current_file = open(filepath, 'a', buffering=1)  # Line buffered
            self._messages_since_last_flush = 0
            self._last_flush_time = datetime.now().timestamp()
            
        except Exception as e:
            self.notify(f"Error opening save file: {e}", severity="error")
            if self.save_checkbox:
                self.save_checkbox.value = False
    
    def _close_file(self) -> None:
        """Close the current save file."""
        if self._current_file is not None:
            try:
                with self._file_lock:
                    self._current_file.flush()
                    self._current_file.close()
            except Exception as e:
                self.notify(f"Error closing save file: {e}", severity="error")
            finally:
                self._current_file = None
    
    def _file_writer_loop(self) -> None:
        """Background thread that writes messages to the save file."""
        while self._file_worker_running:
            try:
                # Get message with timeout to allow thread to be stopped
                try:
                    message = self._file_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Only process if saving is enabled
                if not (self.save_checkbox and self.save_checkbox.value):
                    continue
                
                # Open file if needed
                if self._current_file is None:
                    self._open_file()
                
                # Write message
                if self._current_file is not None:
                    with self._file_lock:
                        try:
                            self._current_file.write(json.dumps(message) + '\n')
                            self._messages_since_last_flush += 1
                            
                            # Flush periodically (every 100 messages or 1 second)
                            current_time = datetime.now().timestamp()
                            if (self._messages_since_last_flush >= 100 or 
                                current_time - self._last_flush_time >= 1.0):
                                self._current_file.flush()
                                self._messages_since_last_flush = 0
                                self._last_flush_time = current_time
                                
                        except Exception as e:
                            self.notify(f"Error writing to save file: {e}", severity="error")
                            self._close_file()
                            if self.save_checkbox:
                                self.save_checkbox.value = False
                
            except Exception as e:
                self.notify(f"Error in file writer: {e}", severity="error")
    
    def _queue_message_for_saving(self, message: Dict) -> None:
        """Add a message to the save queue if saving is enabled."""
        if self.save_checkbox and self.save_checkbox.value:
            try:
                self._file_queue.put_nowait(message)
            except queue.Full:
                self.notify("Save queue full, some messages may be lost", severity="warning")
    
    @on(Checkbox.Changed, "#save")
    def on_save_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle save checkbox state changes."""
        if event.value:
            # Ensure we have a valid filename
            if not self.filename_input or not self.filename_input.value.strip():
                self.filename_input.value = f"mcs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            self._open_file()
        else:
            self._close_file()
    
    @on(Button.Pressed, "#open-save-location")
    def on_open_save_location(self) -> None:
        """Open the save directory in the file explorer."""
        try:
            save_dir = self._get_save_directory()
            import platform
            system = platform.system()
            
            if system == 'Windows':
                import os
                os.startfile(save_dir)
            elif system == 'Darwin':  # macOS
                import subprocess
                subprocess.Popen(['open', str(save_dir)])
            else:  # Linux and others
                import subprocess
                subprocess.Popen(['xdg-open', str(save_dir)])
                
        except Exception as e:
            self.notify(f"Could not open save location: {e}", severity="error")

    def _create_connection_container(self) -> VerticalScroll:
        """Create the connection settings container."""
        self.ip_input = Input(
            placeholder="IP Address",
            id="ip-address",
            classes="connection-input"
        )
        self.port_input = Input(
            placeholder="Port",
            id="port",
            classes="connection-input"
        )
        
        return VerticalScroll(
            Label("Connection", classes=CSS["sidebar_label"]),
            self.ip_input,
            self.port_input,
            Button("Connect", id="connect", variant="primary"),
            Button("Disconnect", id="disconnect", variant="error", disabled=True),
            classes=f"{CSS['connection_container']} {CSS['sidebar_container']}"
        )

    def _create_commands_container(self) -> VerticalScroll:
        """Create the commands container."""
        self.interrogation_button = Button("Interrogations", id="interrogations")
        
        return VerticalScroll(
            Label("Commands", classes=CSS["sidebar_label"]),
            self.interrogation_button,
            Button("Data Recorder", id="data-recorder-commands"),
            classes=CSS["sidebar_container"]
        )

    def _create_display_container(self) -> VerticalScroll:
        """Create the display options container."""
        return VerticalScroll(
            Label("Display", classes=CSS["sidebar_label"]),
            Button("Reports", id="reports-display"),
            Button("Data Recorder", id="data-recorder-display"),
            classes=CSS["sidebar_container"]
        )

    def _create_save_container(self) -> VerticalScroll:
        """Create the save options container."""
        self.filename_input = Input(
            value=f"mcs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl",
            placeholder="File Name",
            id="file-name"
        )
        self.save_checkbox = Checkbox("Save", id="save")
        
        return VerticalScroll(
            Label("Save Raw to File", classes=CSS["sidebar_label"]),
            self.filename_input,
            self.save_checkbox,
            Button("Open Save Location", id="open-save-location"),
            classes=CSS["sidebar_container"]
        )

    def _compose_layout(self) -> ComposeResult:
        """Yield the main layout components."""
        # Left sidebar with controls
        yield Container(
            self._create_connection_container(),
            self._create_commands_container(),
            self._create_display_container(),
            self._create_save_container(),
            id="sidebar"
        )
        
        # Main content area with data table
        yield VerticalScroll(
            DataTable(classes=f"{CSS['left_placeholder']} {CSS['bordered_container']}"),
            id="content"
        )

    # Event Handlers
    
    @on(Button.Pressed, "#connect")
    def on_connect_click(self) -> None:
        """Handle connect button press."""
        try:
            host = self.ip_input.value.strip()
            port = int(self.port_input.value.strip())
            
            if not host:
                self.notify("Please enter a valid host", severity="error")
                return
                
            if not (0 < port <= 65535):
                self.notify("Port must be between 1 and 65535", severity="error")
                return
            
            if hasattr(self.app, 'connect_to_server') and self.app.connect_to_server(host, port):
                self.query_one("#connect").disabled = True
                self.query_one("#disconnect").disabled = False
                self.notify(f"Connected to {host}:{port}", severity="success")
            else:
                self.notify("Failed to connect to server", severity="error")
                
        except ValueError:
            self.notify("Invalid port number", severity="error")
    
    @on(Button.Pressed, "#disconnect")
    def on_disconnect_click(self) -> None:
        """Handle disconnect button press."""
        if hasattr(self.app, 'disconnect_from_server'):
            self.app.disconnect_from_server()
        
        self.query_one("#connect").disabled = False
        self.query_one("#disconnect").disabled = True
        self.notify("Disconnected from server", severity="warning")
    
    @on(Button.Pressed, "#interrogations")
    def on_interrogations_click(self) -> None:
        """Handle interrogation button press - navigate to interrogations screen."""
        if hasattr(self.app, 'push_screen'):
            self.app.push_screen("Interrogations")
    
    # Public Methods
    
    def add_message(self, message: Dict) -> None:
        """Add a message to the data table and optionally save it to a file.
        
        Args:
            message: The message dictionary to add
            
        Returns:
            bool: True if message was added successfully, False otherwise
        """
        if not self.table:
            return False
            
        try:
            # Process the message for display
            processed = getattr(self.app, 'message_handler', None).process_message(message)
            if not processed:
                return False
                
            message_name, timestamp, raw_data = processed
            
            # Add to table
            self.table.add_row(message_name, timestamp, raw_data)
            
            # Limit table size to 250 most recent messages
            if self.table.row_count > 250:
                self.table.remove_row(0)
                
            # Scroll to the bottom
            if self.table.row_count > 0:
                self.table.scroll_to(self.table.row_count - 1)
            
            # Queue message for saving if enabled
            self._queue_message_for_saving(message)
            
            return True
            
        except Exception as e:
            self.notify(f"Error adding message: {str(e)}", severity="error")
            return False