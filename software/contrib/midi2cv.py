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
labels: midi, cv generation, clock

Turns EuroPi into a USB MIDI device, so a computer, phone or tablet can play it as a
monophonic voice: pitch, gate, velocity, CC, transport and clock on the six outputs.

Plug EuroPi into the host with the Pico's USB cable. It appears in the host's MIDI port
list as "EuroPi". No MIDI hardware or adaptor is needed -- the Pico's own USB port does
the work, which also means EuroPi is the MIDI *device* here, not a MIDI host: it cannot
have a keyboard plugged into it.

This is the first phase of a larger design. Everything is fixed in the constants below;
there is no config file and the knobs do nothing. Reassign the outputs by editing
ROUTES, then redeploy. Either button panics.

Requires MicroPython 1.23 or newer for machine.USBDevice. See midi2cv.md.
"""

# ----------------------------------------------------------------------------------
# Configuration
#
# Phase 1 has no config file and no menu. Edit these, redeploy, and rerun.
# ----------------------------------------------------------------------------------

# One entry per output, cv1 to cv6. Any of:
#   gate, pitch, velocity, cc, aftertouch, transport, clock, none
# Duplicates are allowed and useful -- two clock outputs at different divisions, say.
# Anything unrecognised falls back to none rather than raising.
ROUTES = [
    "gate",  # cv1
    "pitch",  # cv2
    "velocity",  # cv3
    "cc",  # cv4
    "transport",  # cv5
    "clock",  # cv6
]

MIDI_CHANNEL = 0  # 0 = omni, or 1-16
BASE_NOTE = 0  # the MIDI note that sits at 0V
PITCH_BEND_SEMITONES = 2  # bend range either side of centre; 0 disables bend
CC_NUMBER = 1  # which CC the "cc" route follows; 1 is the mod wheel
CLOCK_PPQN = 4  # clock pulses per quarter note; must divide into 24
TRIGGER_MS = 10  # width of clock pulses
GATE_RETRIGGER_MS = 5  # how long the gate drops on a retrigger
KEEP_USB_REPL = True  # keep the serial REPL alive alongside MIDI
USB_DEVICE_NAME = "EuroPi"  # the name the host lists in its MIDI ports

# ----------------------------------------------------------------------------------
# MIDI
# ----------------------------------------------------------------------------------

# USB-MIDI code index numbers. These are the top nibble of each 4-byte packet and say
# what the remaining three bytes mean.
CIN_SYSEX_END_1BYTE = 0x5
CIN_NOTE_OFF = 0x8
CIN_NOTE_ON = 0x9
CIN_POLY_KEYPRESS = 0xA
CIN_CONTROL_CHANGE = 0xB
CIN_PROGRAM_CHANGE = 0xC
CIN_CHANNEL_PRESSURE = 0xD
CIN_PITCH_BEND = 0xE
CIN_SINGLE_BYTE = 0xF

# System real-time. These carry no channel.
MIDI_CLOCK = 0xF8
MIDI_START = 0xFA
MIDI_CONTINUE = 0xFB
MIDI_STOP = 0xFC

CC_ALL_SOUND_OFF = 120
CC_ALL_NOTES_OFF = 123

MIDI_PPQN = 24  # MIDI clock always ticks 24 times per quarter note
MAX_MIDI_VALUE = 127
BEND_CENTRE = 8192

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

ROUTE_TYPES = (
    "gate",
    "pitch",
    "velocity",
    "cc",
    "aftertouch",
    "transport",
    "clock",
    "none",
)

# Three characters each, so the route map lines up on the display
ROUTE_ABBREVIATIONS = {
    "gate": "gat",
    "pitch": "pit",
    "velocity": "vel",
    "cc": "cc",
    "aftertouch": "aft",
    "transport": "trn",
    "clock": "clk",
    "none": "---",
}

DISPLAY_INTERVAL_MS = 250


def note_name(note):
    """Human-readable name for a MIDI note number, e.g. 60 -> C4."""
    return "{}{}".format(NOTE_NAMES[note % 12], note // 12 - 1)


class NoteStack:
    """Every note currently held, oldest first.

    Phase 1 always selects the most recently pressed note. The whole stack is kept
    anyway so that releasing one note of several falls back to another rather than
    dropping the gate, which is what makes trills sound right. Phase 2 adds per-output
    selection -- first, last, low, high -- reading from this same stack.
    """

    def __init__(self):
        self.notes = []
        self.velocities = {}

    def note_on(self, note, velocity):
        # Re-pressing a held note moves it to the top rather than duplicating it
        self.note_off(note)
        self.notes.append(note)
        self.velocities[note] = velocity

    def note_off(self, note):
        if note in self.notes:
            self.notes.remove(note)
            del self.velocities[note]

    def clear(self):
        self.notes = []
        self.velocities = {}

    def current(self):
        """The selected note, or None if nothing is held."""
        if self.notes:
            return self.notes[-1]
        return None

    def velocity_of(self, note):
        return self.velocities.get(note, 0)


class UsbMidiTransport(MIDIInterface):
    """Receives USB-MIDI packets and hands them straight to the script.

    on_midi_event is overridden rather than the on_note_on/on_control_change helpers
    because the base class only dispatches note on/off and control change, and drops
    everything else -- including the system real-time messages that clock and transport
    are built from.

    This is the only USB-specific class in the script. A Bluetooth or serial transport
    would replace it and leave the rest untouched.
    """

    def __init__(self, on_event):
        super().__init__()
        self._on_event = on_event

    def on_midi_event(self, cin, midi0, midi1, midi2):
        self._on_event(cin, midi0, midi1, midi2)


class Midi2CV(EuroPiScript):
    def __init__(self):
        super().__init__()

        self.max_voltage = europi_config.MAX_OUTPUT_VOLTAGE
        self.gate_voltage = europi_config.GATE_VOLTAGE

        # A clock pulse every this many MIDI ticks
        self.clock_divisor = max(1, MIDI_PPQN // CLOCK_PPQN)

        self.notes = NoteStack()
        self.bend_semitones = 0.0
        self.cc_value = 0
        self.aftertouch = 0
        self.transport_running = False
        self.clock_tick = 0

        # Shown on the display, not used to drive anything
        self.last_note = None
        self.last_velocity = 0

        self.transport = None
        self.usb_error = None

        # Pending output timings, one slot per output. None means nothing pending.
        self.pulse_off_at = [None] * len(cvs)
        self.gate_raise_at = [None] * len(cvs)

        self.panic_requested = False
        self.display_dirty = True
        self.display_at = ticks_ms()
        self.host_connected = False

        self.resolve_routes()

        # Buttons are serviced from the main loop rather than acted on here: these run
        # in a hardware interrupt, where allocating -- which clearing the note stack
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

    def resolve_routes(self):
        """Turn ROUTES into per-kind lists, once, at startup.

        A note event then walks a short list of note-driven outputs instead of testing
        all six routes every time.
        """
        self.route_map = []
        self.gate_outs = []
        self.pitch_outs = []
        self.velocity_outs = []
        self.cc_outs = []
        self.aftertouch_outs = []
        self.transport_outs = []
        self.clock_outs = []

        by_name = {
            "gate": self.gate_outs,
            "pitch": self.pitch_outs,
            "velocity": self.velocity_outs,
            "cc": self.cc_outs,
            "aftertouch": self.aftertouch_outs,
            "transport": self.transport_outs,
            "clock": self.clock_outs,
        }

        for index in range(len(cvs)):
            name = ROUTES[index] if index < len(ROUTES) else "none"
            if name not in ROUTE_TYPES:
                # A typo should not stop the module booting. The resolved map is on the
                # display, so a mistake is visible rather than silently wrong.
                name = "none"
            self.route_map.append(name)
            if name in by_name:
                by_name[name].append((index, cvs[index]))

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
    # may drive the outputs directly. Only timed work is left to the main loop.
    # ------------------------------------------------------------------------------

    def channel_matches(self, channel):
        # MIDI channels are 1-16 to a musician and 0-15 on the wire
        return MIDI_CHANNEL == 0 or channel + 1 == MIDI_CHANNEL

    def handle_event(self, cin, midi0, midi1, midi2):
        if cin == CIN_SINGLE_BYTE or cin == CIN_SYSEX_END_1BYTE:
            # Hosts differ over which of these two they use for single-byte messages
            if midi0 >= MIDI_CLOCK:
                self.handle_realtime(midi0)
            return

        if not self.channel_matches(midi0 & 0x0F):
            return

        if cin == CIN_NOTE_ON:
            if midi2 == 0:
                # Note-on at velocity 0 is the conventional note-off
                self.handle_note_off(midi1)
            else:
                self.handle_note_on(midi1, midi2)
        elif cin == CIN_NOTE_OFF:
            self.handle_note_off(midi1)
        elif cin == CIN_CONTROL_CHANGE:
            self.handle_control_change(midi1, midi2)
        elif cin == CIN_CHANNEL_PRESSURE:
            self.handle_aftertouch(midi1)
        elif cin == CIN_PITCH_BEND:
            # 14-bit, little end first
            self.handle_pitch_bend(midi1 | (midi2 << 7))
        # Poly key pressure and program change are consumed without acting: poly
        # pressure is per-note and would need associating with a sounding note.

    def handle_note_on(self, note, velocity):
        self.notes.note_on(note, velocity)
        self.last_note = note
        self.last_velocity = velocity

        # Phase 1 dips the gate on every note-on, full stop. Phase 2 makes this
        # conditional on the note actually changing what the output selected.
        now = ticks_ms()
        for index, cv in self.gate_outs:
            cv.off()
            self.gate_raise_at[index] = ticks_add(now, GATE_RETRIGGER_MS)

        self.update_note_outputs()
        self.display_dirty = True

    def handle_note_off(self, note):
        self.notes.note_off(note)
        if self.notes.current() is None:
            for index, cv in self.gate_outs:
                cv.off()
                self.gate_raise_at[index] = None
        else:
            # Fall back to another held note, moving pitch without re-attacking
            self.update_note_outputs()
        self.display_dirty = True

    def update_note_outputs(self):
        """Point pitch and velocity outputs at the selected note.

        Does nothing when no notes are held: phase 1 holds the last value, so a pitch
        output does not dive to 0V and drag any oscillator still tracking it.
        """
        note = self.notes.current()
        if note is None:
            return

        pitch_voltage = self.note_to_voltage(note)
        for index, cv in self.pitch_outs:
            cv.voltage(pitch_voltage)

        velocity_voltage = self.notes.velocity_of(note) / MAX_MIDI_VALUE * self.max_voltage
        for index, cv in self.velocity_outs:
            cv.voltage(velocity_voltage)

    def note_to_voltage(self, note):
        """1V per octave from BASE_NOTE, with pitch bend folded in.

        With BASE_NOTE at 0 this puts note 0 at 0V, middle C at 5V and note 120 at 10V,
        matching the C reference project. Notes past the top of the range clamp.
        """
        semitones = note - BASE_NOTE + self.bend_semitones
        return clamp(semitones / 12.0, 0, self.max_voltage)

    def handle_control_change(self, controller, value):
        if controller == CC_ALL_NOTES_OFF or controller == CC_ALL_SOUND_OFF:
            # The host's own way of clearing a stuck gate
            self.notes.clear()
            for index, cv in self.gate_outs:
                cv.off()
                self.gate_raise_at[index] = None
            self.display_dirty = True
            return

        if controller != CC_NUMBER:
            return

        self.cc_value = value
        voltage = value / MAX_MIDI_VALUE * self.max_voltage
        for index, cv in self.cc_outs:
            cv.voltage(voltage)

    def handle_aftertouch(self, pressure):
        self.aftertouch = pressure
        voltage = pressure / MAX_MIDI_VALUE * self.max_voltage
        for index, cv in self.aftertouch_outs:
            cv.voltage(voltage)

    def handle_pitch_bend(self, value):
        if PITCH_BEND_SEMITONES == 0:
            return
        self.bend_semitones = (value - BEND_CENTRE) / BEND_CENTRE * PITCH_BEND_SEMITONES
        self.update_note_outputs()
        self.display_dirty = True

    def handle_realtime(self, status):
        if status == MIDI_CLOCK:
            if self.clock_tick % self.clock_divisor == 0:
                now = ticks_ms()
                for index, cv in self.clock_outs:
                    cv.voltage(self.gate_voltage)
                    self.pulse_off_at[index] = ticks_add(now, TRIGGER_MS)
            self.clock_tick += 1
        elif status == MIDI_START:
            # Start restarts the bar; Continue picks up where Stop left off, so only
            # Start resets the tick count
            self.clock_tick = 0
            self.set_transport(True)
        elif status == MIDI_CONTINUE:
            self.set_transport(True)
        elif status == MIDI_STOP:
            self.set_transport(False)

    def set_transport(self, running):
        self.transport_running = running
        for index, cv in self.transport_outs:
            if running:
                cv.voltage(self.gate_voltage)
            else:
                cv.off()
        self.display_dirty = True

    # ------------------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------------------

    def panic(self):
        """Return to the power-on state without rebooting.

        Note this drops pitch outputs to 0V, unlike an ordinary note-off, where pitch
        holds. Anything ungated that tracks a pitch output will jump.
        """
        self.notes.clear()
        self.bend_semitones = 0.0
        self.cc_value = 0
        self.aftertouch = 0
        self.transport_running = False
        self.clock_tick = 0
        self.last_note = None
        self.last_velocity = 0

        for index in range(len(cvs)):
            self.pulse_off_at[index] = None
            self.gate_raise_at[index] = None
        turn_off_all_cvs()

        self.display_dirty = True

    def service_timers(self, now):
        """End clock pulses and raise gates whose retrigger dip has expired."""
        for index, cv in self.clock_outs:
            off_at = self.pulse_off_at[index]
            if off_at is not None and ticks_diff(now, off_at) >= 0:
                self.pulse_off_at[index] = None
                cv.off()

        for index, cv in self.gate_outs:
            raise_at = self.gate_raise_at[index]
            if raise_at is not None and ticks_diff(now, raise_at) >= 0:
                self.gate_raise_at[index] = None
                # The note may have been released during the dip
                if self.notes.current() is not None:
                    cv.voltage(self.gate_voltage)

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
            # Give the whole row to the error rather than squeezing it beside the channel
            oled.text(self.usb_error, 0, 0)
        else:
            link = "USB ok" if connected else "USB --"
            channel = "omni" if MIDI_CHANNEL == 0 else "ch {}".format(MIDI_CHANNEL)
            oled.text("{:<8}{:>8}".format(link, channel), 0, 0)

        if self.last_note is None:
            oled.text("--", 0, 8)
        else:
            oled.text(
                "{:<4} v{:<3} {:+.1f}".format(
                    note_name(self.last_note), self.last_velocity, self.bend_semitones
                ),
                0,
                8,
            )

        oled.text(self.route_row(0), 0, 16)
        oled.text(self.route_row(3), 0, 24)

        oled.show()

    def route_row(self, first):
        """Three outputs of the resolved route map, e.g. "1gat 2pit 3vel"."""
        return " ".join(
            "{}{:<3}".format(index + 1, ROUTE_ABBREVIATIONS[self.route_map[index]])
            for index in range(first, min(first + 3, len(self.route_map)))
        )

    def main(self):
        self.start_usb()

        while True:
            now = ticks_ms()

            if self.panic_requested:
                self.panic_requested = False
                self.panic()

            self.service_timers(now)
            self.update_display(now)


if __name__ == "__main__":
    Midi2CV().main()
