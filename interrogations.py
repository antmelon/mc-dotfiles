"""Interrogations screen for the MCS application."""

from datetime import datetime, timezone
from typing import List, Tuple

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Select,
)


class Interrogations(Screen):
    """Screen for configuring interrogations with various parameters."""

    # Keyboard bindings
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("escape", "app.pop_screen", "Back to Main Menu"),
    ]

    # Constants
    MODE_S_OPTIONS = [
        ("No Mode S Interrogations", 0),
        ("1 Mode S Interrogations", 1),
        ("2 Mode S Interrogations", 2),
        ("3 Mode S Interrogations", 3),
        ("4 Mode S Interrogations", 4),
    ]

    POWER_LEVELS = [
        ("0 dBm (0000)", 0),
        ("54 dBm (0001)", 1),
        ("57 dBm (0010)", 2),
        ("60 dBm (0011)", 3),
        ("63 dBm (0100)", 4),
        ("66 dBm (0101)", 5),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        self._init_inputs()
        self._init_containers()
        
        yield Header()
        yield Footer()
        yield from self._compose_main_content()

    def _init_inputs(self) -> None:
        """Initialize all input widgets."""
        # Basic inputs
        self.azimuth = Input(id="azimuth", placeholder="Azimuth", type="number", 
                           classes="interrogation-input")
        self.range = Input(id="range", placeholder="Range", type="number", 
                         classes="interrogation-input")
        self.pri = Input(id="pri", placeholder="PRI Length", type="number", 
                       classes="interrogation-input")
        
        # Checkboxes
        self.mode_s_squitter = Checkbox("Mode S Squitter Enable", id="mode_s_squitter")
        self.popup = Checkbox("POPUP", id="popup")
        self.real_time_test = Checkbox("Real Time Test", id="real_time_test")
        self.mode_3 = Checkbox("Mode 3/A", id="mode_3")
        self.mode_C = Checkbox("Mode C", id="mode_C")
        
        # Mode S selections
        self.mode_s_select = Select(
            self.MODE_S_OPTIONS, 
            id="mode_s_select", 
            allow_blank=False
        )
        
        # Mode 5 formats
        self.format0 = Checkbox("Format 0", id="format0")
        self.format1 = Checkbox("Format 1", id="format1")
        self.format2 = Checkbox("Format 2", id="format2")
        self.format3 = Checkbox("Format 3", id="format3")
        self.format4 = Checkbox("Format 4", id="format4")
        
        # Power output
        radio_buttons = [
            RadioButton(label, value=value) 
            for label, value in self.POWER_LEVELS
        ]
        self.power_output = RadioSet(*radio_buttons, id="power-output")
        
        # Buttons
        self.send_button = Button("Send", id="send")
        self.clear_button = Button("Clear", id="clear")
        self.back_button = Button("Back", id="back")
        
        # Other widgets

    def _init_containers(self) -> None:
        """Initialize all container widgets."""
        # MK XII Interrogations container with vertical layout
        self.sif_container = VerticalScroll(
            Label("MK XII Interrogations"),
            Container(
                self.mode_3,
                self.mode_C,
            ),
            classes="sif-container bordered-container"
        )

        # Mode 5 Interrogations container with vertical layout
        self.mode5_container = VerticalScroll(
            Label("Mode 5 Interrogations"),
            Container(
                self.format0,
                self.format1,
                self.format2,
                self.format3,
                self.format4,
            ),
            classes="mode5-container bordered-container"
        )

        # Horizontal container for both interrogation sections
        self.interrogation_params = Container(
            self.sif_container,
            self.mode5_container,
            classes="interrogation-params"
        )

        # Power output container
        self.power_output_container = Container(
            Label("Power Output"),
            self.power_output,
            classes="power-output-container"
        )
        
        # Buttons container
        self.buttons_container = Container(
            self.clear_button,
            self.send_button,
            self.back_button,
            classes="buttons-container"
        )

        # Right side container
        self.interrogations_right = Container(
            self.interrogation_params,
            self.power_output_container,
            self.buttons_container,
            classes="interrogation-right"
        )

    def _compose_main_content(self) -> ComposeResult:
        """Yield the main content widgets."""
        yield VerticalScroll(
            self.azimuth,
            self.range,
            self.pri,
            self.mode_s_squitter,
            self.popup,
            self.mode_s_select,
            self.real_time_test,
            classes="bordered-container"
        )
        yield self.interrogations_right

    def on_mount(self) -> None:
        """Configure the screen when it's mounted."""
        self.title = "Interrogations"

    @on(Button.Pressed, "#back")
    def back(self) -> None:
        """Handle back button press - return to previous screen."""
        self.app.pop_screen()

    def _validate_checkbox_selection(self, checkboxes: list) -> bool:
        """Validate that at most one checkbox is selected from the list."""
        selected = sum(1 for cb in checkboxes if cb.value)
        return selected <= 1

    @on(Button.Pressed, "#send")
    def send(self) -> None:
        """Handle send button press - send interrogation message."""
        try:
            # Validate format checkboxes (only 0 or 1 can be selected)
            format_checkboxes = [self.format0, self.format1, self.format2, self.format3, self.format4]
            mxii_checkboxes = [self.mode_3, self.mode_C]
            
            if not self._validate_checkbox_selection(format_checkboxes):
                self.notify("Error: Only one Format can be selected at a time", severity="error")
                return
                
            if not self._validate_checkbox_selection(mxii_checkboxes):
                self.notify("Error: Only one MXII Interrogation can be selected at a time", severity="error")
                return
            
            # Get selected format (0-4) or None if none selected
            selected_format = next(
                (i for i, cb in enumerate(format_checkboxes) if cb.value),
                None
            )
            
            # Get selected MXII (0 for mode_3, 1 for mode_C) or None if none selected
            selected_mxii = 0 if self.mode_3.value else (1 if self.mode_C.value else None)
            
            # Create the signals dictionary
            signals = {
                "MessageType": 0,
                "MessageSize": 64,
                "Sequence": 0,
                "Azimuth": float(self.azimuth.value) if self.azimuth.value else 0,
                "Range": float(self.range.value) if self.range.value else 0,
                "PRI_Length": float(self.pri.value) if self.pri.value else 0,
                "Mode_S_Squitter_Enable": self.mode_s_squitter.value,
                "POPUP": self.popup.value,
                "Interrogator_Power_Output": self.power_output.pressed_index or 0,
                "Mode_5_Format": selected_format if selected_format is not None else 0,
                "SIF_Mode": selected_mxii if selected_mxii is not None else -1,
                # Derived signals
                "Mode_S_Interrogation": self.mode_s_select.value != 0,  # True if not "No Mode S Interrogations"
                "Mode_5_Interrogation": selected_format is not None,  # True if any format is selected
                "SIF_Interrogation": selected_mxii is not None,  # True if any MXII is selected
            }
            
            # Create the message in the required format
            message = {
                "MessageName": "CM0",
                "Signals": signals,
                "Modifiers": {}
            }
            
            # Send the message through the app's TCP client
            if hasattr(self.app, 'send_message') and self.app.send_message(message):
                self.notify("Interrogation sent successfully", severity="success")
            else:
                self.notify("Failed to send interrogation", severity="error")
                
        except ValueError as e:
            self.notify(f"Invalid input: {str(e)}", severity="error")

    @on(Button.Pressed, "#clear")
    def clear(self) -> None:
        """Reset all input fields to their default values."""
        # Clear text inputs
        for field in [self.azimuth, self.range, self.pri]:
            field.value = ""
        
        # Reset checkboxes
        for checkbox in [
            self.mode_s_squitter,
            self.popup,
            self.real_time_test,
            self.mode_3,
            self.mode_C,
            self.format0,
            self.format1,
            self.format2,
            self.format3,
            self.format4,
        ]:
            checkbox.value = False
        
        # Reset other inputs
        self.mode_s_select.value = 0
        self.power_output.value = ""