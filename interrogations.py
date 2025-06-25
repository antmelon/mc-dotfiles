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
    TabbedContent,
    TabPane
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

    PROBABILITY_OF_REPLY = [
        ("0: Probability of 1", 0),
        ("1: Probability of 1/2", 1),
        ("2: Probability of 1/4", 2),
        ("3: Probability of 1/8", 3),
        ("4: Probability of 1/16", 4),
        ("8: No Lockout, Probability of 1", 8),
        ("9: No Lockout, Probability of 1/2", 9),
        ("10: No Lockout, Probability of 1/4", 10),
        ("11: No Lockout, Probability of 1/8", 11),
        ("12: No Lockout, Probability of 1/16", 12),
    ]

    MODE_S_PROTOCOL = [
        ("0: No Action", 0),
        ("1: Non Selective All Call", 1),
        ("4: Close Out Comm B", 4),
        ("5: Close Out Uplink ELM", 5),
        ("6: Close Out Downlink ELM", 6),
    ]

    MODE_S_MES = [
        ("0: No Action", 0),
        ("1: Uplink ELM Reservation Request", 1),
        ("2: Uplink ELM Closeout", 2),
        ("3: ELM Reservation Request", 3),
        ("4: Downlink ELM Closeout", 4),
        ("5: Upplink Reservation Request/Downlink Closeout", 5),
        ("6: Downlink Reservation Request/Uplink Closeout", 6),
        ("7: Uplink ELM and Downlink Closeouts", 7),
    ]

    MODE_S_RSS = [
        ("0: No Request", 0),
        ("1: Comm B Reservation", 1),
        ("2: Uplink ELM Reservation", 2),
        ("3: Downlink ELM Reservation", 3)
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
            classes="interrogation-right"
        )

        # Each TabPane gets only the VerticalScroll (from _make_mode_s_grid)
        self.tab1 = TabPane("Mode S Interrogation", self._make_mode_s_grid("tab1"), id="tab1")
        self.tab2 = TabPane("Mode S Interrogation", self._make_mode_s_grid("tab2"), id="tab2")
        self.tab3 = TabPane("Mode S Interrogation", self._make_mode_s_grid("tab3"), id="tab3")
        self.tab4 = TabPane("Mode S Interrogation", self._make_mode_s_grid("tab4"), id="tab4")

    def _make_mode_s_grid(self, prefix: str):
        """
        Create a 4x5 grid of widgets for a Mode S tab.
        Prefix is used to make widget IDs unique per tab.
        """
        from textual.containers import Container, VerticalScroll
        from textual.widgets import Select, Input, RadioSet, RadioButton, Label

        # Helper to make Select options
        def make_select(options):
            return [(str(opt), opt) for opt in options]
        def make_bin_select(start, end, width):
            return [(format(i, f'0{width}b'), i) for i in range(start, end+1)]

        def cell(label, widget):
            return Container(
                Label(label),
                widget,
                classes="mode-s-grid-cell"
            )

        widgets = [
            # Row 1
            cell("Format", Select(make_select([4,5,11,17,20,21]), id=f"{prefix}-format")),
            cell("Aircraft Address", Input(placeholder="Hex", id=f"{prefix}-aircraft-address")),
            cell("Interrogation Ratio", Select(make_bin_select(0, 10, 4), id=f"{prefix}-interrogation-ratio")),
            cell("Probability of Reply", Select(self.PROBABILITY_OF_REPLY, id=f"{prefix}-prob-reply")),
            cell("Code Label", Select(make_bin_select(0, 4, 3), id=f"{prefix}-code-label")),
            # Row 2
            cell("Protocol", Select(make_select([0,1,4,5,6]), id=f"{prefix}-protocol")),
            cell("Reply Request", Input(placeholder="Number", id=f"{prefix}-reply-request")),
            cell("Designator", Select(make_select([0,1,2,3,7]), id=f"{prefix}-designator")),
            cell("IIS/IC", Select(make_bin_select(0, 15, 4), id=f"{prefix}-iis")),
            # Row 3
            cell("MBS", RadioSet(
                RadioButton("No Comm B", value=1),
                RadioButton("Air", value=0),
                RadioButton("Closeout", value=0),
                id=f"{prefix}-mbs"
            )),
            cell("MES", Select(make_select(list(range(8))), id=f"{prefix}-mes")),
            cell("LOS", RadioSet(
                RadioButton("No Change", value=1),
                RadioButton("Multisite Lock", value=0),
                id=f"{prefix}-los"
            )),
            cell("RSS", Select(make_select(list(range(4))), id=f"{prefix}-rss")),
            cell("TMS", Select(make_bin_select(0, 15, 4), id=f"{prefix}-tms")),
            # Row 4
            cell("RRS", Select(make_bin_select(0, 15, 4), id=f"{prefix}-rrs")),
            cell("TCS", Select(make_select(list(range(4))), id=f"{prefix}-tcs")),
            cell("RCS", Select(make_select(list(range(5))), id=f"{prefix}-rcs")),
            cell("SAS", Select(make_select(list(range(4))), id=f"{prefix}-sas")),
            cell("SIS", Input(placeholder="Integer", id=f"{prefix}-sis")),
            cell("LSS", RadioSet(
                RadioButton("No Change", value=1),
                RadioButton("Multisite Lock", value=0),
                id=f"{prefix}-lss"
            )),
        ]
        
        # Create a grid container for all widgets
        grid_container = Container(*widgets, classes="mode-s-grid")
        
        # Wrap the grid container in a VerticalScroll
        return VerticalScroll(grid_container, classes="mode-s-tab-scroll")

    def get_mode_s_data(self, prefix: str) -> tuple[int, int]:
        """
        Query all widgets in the grid for the given prefix and return:
        - mode_s_word: 32-bit integer containing the Mode S data
        - aircraft_address: integer representation of the 6-digit hex aircraft address
        """
        # Unified helper to get values from any widget type
        def get_widget_value(widget_id, default=0, as_type=int):
            try:
                w = self.query_one(f"#{prefix}-{widget_id}")
                from textual.widgets import RadioSet
                if isinstance(w, RadioSet):
                    self.notify(f"RadioSet {widget_id} value: {w.pressed_index}")
                    # RadioSet.value returns the selected RadioButton's value
                    # If nothing is selected, it returns None
                    if w.pressed_index is None:
                        return default
                    return int(w.pressed_index) if as_type == int else w.value
                if not hasattr(w, "value") or w.value is None:
                    return default

                if as_type == int:
                    if isinstance(w.value, str):
                        return int(w.value.strip()) if w.value.strip() else default
                    return int(w.value)
                elif as_type == str:
                    return str(w.value)
                return w.value
            except Exception as e:
                print(f"Error getting value for {widget_id}: {e}")
                return default
        
        # Get all values at once
        values = {
            "fmt": get_widget_value("format"),
            "protocol": get_widget_value("protocol"),
            "reply_request": max(0, min(31, get_widget_value("reply-request"))),
            "designator": get_widget_value("designator"),
            "iis": get_widget_value("iis"),
            "mbs": get_widget_value("mbs"),
            "mes": get_widget_value("mes"),
            "los": get_widget_value("los"),
            "rss": get_widget_value("rss"),
            "tms": get_widget_value("tms"),
            "rrs": get_widget_value("rrs"),
            "tcs": get_widget_value("tcs"),
            "rcs": get_widget_value("rcs"),
            "sas": get_widget_value("sas"),
            "sis": max(0, min(31, get_widget_value("sis"))),
            "lss": get_widget_value("lss"),
            "prob_reply": get_widget_value("prob-reply"),
            "interrogator_code": get_widget_value("iis"),
            "code_label": get_widget_value("code-label")
        }
        
        # Parse aircraft address as 6-digit hex
        aircraft_address_str = get_widget_value("aircraft-address", "", str).strip()
        try:
            aircraft_address = int(aircraft_address_str, 16) if aircraft_address_str else 0
        except ValueError:
            aircraft_address = 0

        # Initialize the 32-bit word
        mode_s_word = 0
        
        # Common bits for all formats
        fmt = values["fmt"]
        mode_s_word |= (fmt & 0x1F) << 27  # Bits 1-5: format (5 bits)
        
        # Format-specific bit packing
        if fmt in (4, 5, 20, 21):
            # Bits 6-16: Common for these formats
            mode_s_word |= (values["protocol"] & 0x7) << 24       # Bits 6-8: protocol (3 bits)
            mode_s_word |= (values["reply_request"] & 0x1F) << 19 # Bits 9-13: reply_request (5 bits)
            mode_s_word |= (values["designator"] & 0x7) << 16     # Bits 14-16: designator (3 bits)
            
            # Designator-specific bit packing (bits 17-32)
            designator = values["designator"]
            
            # Dictionary of designator handlers
            designator_handlers = {
                0: lambda: (values["iis"] & 0xF) << 12,  # Bits 17-20: IIS, rest 0
                
                1: lambda: ((values["iis"] & 0xF) << 12) |  # Bits 17-20: IIS
                           ((values["mbs"] & 0x3) << 10) |  # Bits 21-22: MBS
                           ((values["mes"] & 0x7) << 7) |   # Bits 23-25: MES
                           ((values["los"] & 0x1) << 6) |   # Bit 26: LOS
                           ((values["rss"] & 0x3) << 4) |   # Bits 27-28: RSS
                           (values["tms"] & 0xF),          # Bits 29-32: TMS
                
                2: lambda: ((values["tcs"] & 0x7) << 8) |   # Bits 22-24: TCS (bits 17-21 are 0)
                           ((values["rcs"] & 0x7) << 5) |   # Bits 25-27: RCS
                           ((values["sas"] & 0x3) << 3),    # Bits 28-29: SAS (bits 30-32 are 0)
                
                3: lambda: ((values["sis"] & 0x1F) << 11) |  # Bits 17-21: SIS
                           ((values["lss"] & 0x1) << 10) |   # Bit 22: LSS
                           ((values["rrs"] & 0xF) << 6),     # Bits 23-26: RRS (bits 27-32 are 0)
                
                7: lambda: ((values["iis"] & 0xF) << 12) |  # Bits 17-20: IIS
                           ((values["rrs"] & 0xF) << 8) |   # Bits 21-24: RRS
                           ((values["los"] & 0x1) << 6) |   # Bit 26: LOS (bit 25 is 0)
                           (values["tms"] & 0xF)           # Bits 29-32: TMS (bits 27-28 are 0)
            }
            
            # Apply the designator-specific bit packing
            if designator in designator_handlers:
                mode_s_word |= designator_handlers[designator]()
                
        elif fmt in (11, 17):
            # Bits 6-16 for formats 11 and 17
            mode_s_word |= (values["prob_reply"] & 0xF) << 23       # Bits 6-9: probability of reply
            mode_s_word |= (values["interrogator_code"] & 0xF) << 19 # Bits 10-13: interrogator code
            mode_s_word |= (values["code_label"] & 0x7) << 16       # Bits 14-16: code label
            # Bits 17-32 are 0
            
        # For any other format, we've already set bits 1-5 with the format
            
        return mode_s_word, aircraft_address


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
        with Container(classes="interrogation-right"):
            yield self.interrogation_params
            yield self.power_output_container
            yield self.buttons_container
            with TabbedContent(id ='mode-s-tabs'):
                yield self.tab1
                yield self.tab2
                yield self.tab3
                yield self.tab4

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
        mode_s_1_enable = False
        mode_s_2_enable = False
        mode_s_3_enable = False
        mode_s_4_enable = False
        mode_s_data_1 = None
        mode_s_data_2 = None
        mode_s_data_3 = None
        mode_s_data_4 = None
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

            if self.mode_s_select.value > 0:
                mode_s_1_enable = True
                mode_s_data_1 = self.get_mode_s_data("tab1")
            
            if self.mode_s_select.value > 1:
                mode_s_2_enable = True
                mode_s_data_2 = self.get_mode_s_data("tab2")
            
            if self.mode_s_select.value > 2:
                mode_s_3_enable = True
                mode_s_data_3 = self.get_mode_s_data("tab3")
            
            if self.mode_s_select.value > 3:
                mode_s_4_enable = True
                mode_s_data_4 = self.get_mode_s_data("tab4")
            
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

            # Get the Mode S Interrogation data
            mode_s_word, aircraft_address = self.get_mode_s_data("tab1")
            self.notify(f"Mode S Word: {mode_s_word}")
            self.notify(f"Aircraft Address: {aircraft_address}")

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