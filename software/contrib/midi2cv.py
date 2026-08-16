# Copyright 2026 Allen Synthesis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from europi import *
from europi_script import EuroPiScript
from time import ticks_add, ticks_diff, ticks_ms

try:
    from experimental.usb.device import get as usb_device_get
    from experimental.usb.device.midi import MIDIInterface

    USB_PACKAGE_PRESENT = True
except ImportError:
    # experimental/usb/ is not on the module. deploy_firmware.rshell copies
    # experimental/*.py without recursing, so the nested package needs deploying by
    # hand until that is fixed. See midi2cv.md.
    MIDIInterface = object
    usb_device_get = None
    USB_PACKAGE_PRESENT = False

"""
MIDI to CV
author: daaaaaaaaaniel (github.com/daaaaaaaaaniel)
date: 2026-08-16
labels: midi, cv generation

Turns EuroPi into a USB MIDI device. Plug it into a computer, phone or tablet with the
Pico's own USB cable and it appears in the host's MIDI port list as "EuroPi".

This is phase 1 of a larger design, and it is deliberately tiny. It exists to answer one
question on real hardware: does USB MIDI reach EuroPi at all? Everything that could
obscure that answer has been left out -- there is no routing, no velocity, no CC, no
clock division and no retrigger logic. Two outputs and a monitor:

    cv1  transport gate -- high between MIDI Start/Continue and Stop
    cv2  pitch          -- 1V/octave from the most recent note
    cv3 to cv6          -- unused, held at 0V

cv1 is driven only by system real-time messages and cv2 only by note messages, so
between them they prove both halves of the MIDI path with no shared logic. The display
shows the raw packet count and the last packet received, so a silent module can still be
diagnosed.

Either button panics: outputs to 0V and counters reset.

Requires MicroPython 1.23 or newer for machine.USBDevice. See midi2cv.md.
"""

# ----------------------------------------------------------------------------------
# Configuration. Edit these, redeploy, and rerun.
# ----------------------------------------------------------------------------------

MIDI_CHANNEL = 0  # 0 = omni, or 1-16
BASE_NOTE = 0  # the MIDI note that sits at 0V
USB_DEVICE_NAME = "EuroPi"  # the name the host lists in its MIDI ports

# Keep the serial REPL alive alongside MIDI. Worth knowing before you test on Windows:
# HLammers/multi-midi, another MicroPython USB MIDI library for RP2, disables the REPL
# outright, reporting that a Windows host will not recognise the MIDI ports if CDC and
# MIDI are both enabled. Neither library emits an Interface Association Descriptor,
# which is what a composite device normally needs. If Windows does not see the module,
# set this to False first -- at the cost of losing Thonny and mpremote while it runs.
KEEP_USB_REPL = True

# ----------------------------------------------------------------------------------
# MIDI
# ----------------------------------------------------------------------------------

# USB-MIDI code index numbers -- the top nibble of each 4-byte packet
CIN_SYSEX_END_1BYTE = 0x5
CIN_NOTE_OFF = 0x8
CIN_NOTE_ON = 0x9
CIN_SINGLE_BYTE = 0xF

# System real-time. These carry no channel.
MIDI_CLOCK = 0xF8
MIDI_START = 0xFA
MIDI_CONTINUE = 0xFB
MIDI_STOP = 0xFC

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

TRANSPORT_CV = 0
PITCH_CV = 1

DISPLAY_INTERVAL_MS = 250


def note_name(note):
    """Human-readable name for a MIDI note number, e.g. 60 -> C4."""
    return "{}{}".format(NOTE_NAMES[note % 12], note // 12 - 1)


class UsbMidiTransport(MIDIInterface):
    """Receives USB-MIDI packets and hands them straight to the script.

    on_midi_event is overridden rather than the on_note_on/on_control_change helpers
    because the base class only dispatches note on/off and control change, and drops
    everything else -- including the system real-time messages the transport gate is
    built from.

    This is the only USB-specific class in the script. A Bluetooth or serial transport
    would replace it and leave the rest untouched.
    """

    def __init__(self, on_event):
        # 64 matches the endpoint's declared wMaxPacketSize (midi.py:297). The library
        # defaults to a 16-byte receive buffer, which is smaller than a single packet
        # the host is entitled to send -- USB requires a bulk OUT endpoint to accept a
        # full max-size packet. HLammers/multi-midi aligns the two the same way.
        super().__init__(rxlen=64)
        self._on_event = on_event

    def on_midi_event(self, cin, midi0, midi1, midi2):
        self._on_event(cin, midi0, midi1, midi2)


class Midi2CV(EuroPiScript):
    def __init__(self):
        super().__init__()

        self.max_voltage = europi_config.MAX_OUTPUT_VOLTAGE
        self.gate_voltage = europi_config.GATE_VOLTAGE

        self.transport = None
        self.usb_error = None

        # Every note currently held, oldest first. Phase 1 always plays the most
        # recent one; keeping the whole stack means releasing one note of several
        # falls back to another rather than going silent.
        self.held_notes = []

        self.transport_running = False
        self.message_count = 0
        self.last_packet = None

        self.panic_requested = False
        self.display_dirty = True
        # Backdated so the first frame draws immediately rather than leaving whatever
        # the menu left on screen for the length of one refresh interval
        self.display_at = ticks_add(ticks_ms(), -DISPLAY_INTERVAL_MS)
        self.host_connected = False

        # Buttons are serviced from the main loop rather than acted on here: these run
        # in a hardware interrupt, where allocating -- which clearing the note list
        # does -- is not safe.
        @b1.handler_falling
        def b1_released():
            self.panic_requested = True

        @b2.handler_falling
        def b2_released():
            self.panic_requested = True

    @classmethod
    def display_name(cls):
        return "MIDI to CV"

    # ------------------------------------------------------------------------------
    # USB
    # ------------------------------------------------------------------------------

    def start_usb(self):
        """Bring up the USB MIDI interface, or record why it could not start.

        Calling init() forces the device to disconnect and re-enumerate, so any live
        Thonny or mpremote session drops here and comes back a moment later.
        """
        if not USB_PACKAGE_PRESENT:
            self.usb_error = "no usb package"
            return

        self.transport = UsbMidiTransport(self.handle_event)
        try:
            usb_device_get().init(
                self.transport,
                builtin_driver=KEEP_USB_REPL,
                manufacturer_str="Allen Synthesis",
                product_str=USB_DEVICE_NAME,
            )
        except AttributeError:
            # machine.USBDevice arrived in MicroPython 1.23, and core.py only touches
            # it inside _Device.__init__ -- so an older build imports the package
            # happily and fails here instead.
            self.transport = None
            self.usb_error = "need uPy 1.23+"

    def is_connected(self):
        return self.transport is not None and self.transport.is_open()

    # ------------------------------------------------------------------------------
    # MIDI handling
    #
    # These run from micropython.schedule, a soft interrupt, so they may allocate and
    # may drive the outputs directly.
    # ------------------------------------------------------------------------------

    def handle_event(self, cin, midi0, midi1, midi2):
        # Counting every packet, before any filtering, is what makes a silent module
        # diagnosable: a rising count with nothing on the outputs is a very different
        # problem from a count stuck at zero.
        self.message_count += 1
        self.last_packet = (cin, midi0, midi1, midi2)
        self.display_dirty = True

        if cin == CIN_SINGLE_BYTE or cin == CIN_SYSEX_END_1BYTE:
            # Hosts differ over which of these two they use for single-byte messages
            if midi0 >= MIDI_CLOCK:
                self.handle_realtime(midi0)
            return

        # MIDI channels are 1-16 to a musician and 0-15 on the wire
        if MIDI_CHANNEL != 0 and (midi0 & 0x0F) + 1 != MIDI_CHANNEL:
            return

        if cin == CIN_NOTE_ON:
            if midi2 == 0:
                # Note-on at velocity 0 is the conventional note-off
                self.note_off(midi1)
            else:
                self.note_on(midi1)
        elif cin == CIN_NOTE_OFF:
            self.note_off(midi1)

    def note_on(self, note):
        if note in self.held_notes:
            self.held_notes.remove(note)
        self.held_notes.append(note)
        cvs[PITCH_CV].voltage(self.note_to_voltage(note))

    def note_off(self, note):
        if note in self.held_notes:
            self.held_notes.remove(note)
        if self.held_notes:
            # Fall back to another held note rather than jumping
            cvs[PITCH_CV].voltage(self.note_to_voltage(self.held_notes[-1]))
        # With nothing held, pitch holds its last value: dropping to 0V would make an
        # audible dive on any oscillator still tracking it.

    def note_to_voltage(self, note):
        """1V per octave from BASE_NOTE.

        With BASE_NOTE at 0 this puts note 0 at 0V, middle C at 5V and note 120 at 10V.
        Notes past the top of the range clamp.
        """
        return clamp((note - BASE_NOTE) / 12.0, 0, self.max_voltage)

    def handle_realtime(self, status):
        if status == MIDI_START or status == MIDI_CONTINUE:
            self.transport_running = True
            cvs[TRANSPORT_CV].voltage(self.gate_voltage)
        elif status == MIDI_STOP:
            self.transport_running = False
            cvs[TRANSPORT_CV].off()
        # MIDI clock is counted but not acted on: clock division is phase 2

    # ------------------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------------------

    def panic(self):
        """Return to the power-on state without rebooting."""
        self.held_notes = []
        self.transport_running = False
        self.message_count = 0
        self.last_packet = None
        turn_off_all_cvs()
        self.display_dirty = True

    def update_display(self, now):
        connected = self.is_connected()
        if connected != self.host_connected:
            self.host_connected = connected
            self.display_dirty = True

        if not self.display_dirty:
            return
        if ticks_diff(now, self.display_at) < DISPLAY_INTERVAL_MS:
            return

        self.display_at = now
        self.display_dirty = False

        oled.fill(0)

        if self.usb_error is not None:
            oled.text(self.usb_error, 0, 0)
        else:
            link = "USB ok" if connected else "USB --"
            channel = "omni" if MIDI_CHANNEL == 0 else "ch {}".format(MIDI_CHANNEL)
            oled.text("{:<8}{:>8}".format(link, channel), 0, 0)

        transport = "RUN" if self.transport_running else "stop"
        oled.text("{:<11}{:>5}".format("msgs {}".format(self.message_count), transport), 0, 8)

        oled.text(self.packet_row(), 0, 16)
        oled.text(self.note_row(), 0, 24)

        oled.show()

    def packet_row(self):
        """The last raw packet, so an unexpected message is still visible."""
        if self.last_packet is None:
            return "pkt --"
        cin, midi0, midi1, midi2 = self.last_packet
        return "pkt {:X} {:02X} {:02X} {:02X}".format(cin, midi0, midi1, midi2)

    def note_row(self):
        if not self.held_notes:
            return "--"
        note = self.held_notes[-1]
        return "{:<6}{:>10}".format(note_name(note), "{:.3f}V".format(self.note_to_voltage(note)))

    def main(self):
        self.start_usb()

        while True:
            if self.panic_requested:
                self.panic_requested = False
                self.panic()

            self.update_display(ticks_ms())


if __name__ == "__main__":
    Midi2CV().main()
