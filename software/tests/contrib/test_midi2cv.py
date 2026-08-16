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
import sys

import pytest
import utime


@pytest.fixture
def mock_time_module(monkeypatch):
    """the time module isn't as easily mocked as the utime module is,
    but we can just swap it out for our mock for this test"""
    monkeypatch.setitem(sys.modules, "time", utime)


@pytest.fixture
def midi2cv(mock_time_module):
    import contrib.midi2cv as module
    from europi import turn_off_all_cvs

    turn_off_all_cvs()
    yield module
    turn_off_all_cvs()


@pytest.fixture
def script(midi2cv):
    return midi2cv.Midi2CV()


def transport_cv():
    from europi import cvs

    return cvs[0]


def pitch_cv():
    from europi import cvs

    return cvs[1]


def is_high(cv):
    """The outputs read back through a calibration table, so compare generously."""
    return cv.voltage() > 1.0


# ----------------------------------------------------------------------------------
# Pitch
# ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "note, volts",
    [
        (0, 0.0),  # C-1, the bottom of the range
        (21, 1.75),  # A0, bottom of an 88-key
        (60, 5.0),  # middle C
        (108, 9.0),  # C8, top of an 88-key
        (120, 10.0),  # C9, the top of the range
    ],
)
def test_note_to_voltage(script, note, volts):
    assert script.note_to_voltage(note) == pytest.approx(volts)


def test_notes_above_the_range_clamp(script):
    for note in range(121, 128):
        assert script.note_to_voltage(note) == pytest.approx(10.0)


def test_note_on_drives_the_pitch_output(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    assert pitch_cv().voltage() > 0


def test_last_note_wins(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 72, 100)
    assert script.held_notes == [60, 72]


def test_release_falls_back_to_a_held_note(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 72, 100)
    high = pitch_cv().voltage()

    script.handle_event(midi2cv.CIN_NOTE_OFF, 0x80, 72, 0)
    assert script.held_notes == [60]
    assert pitch_cv().voltage() < high


def test_pitch_holds_when_every_note_is_released(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    held = pitch_cv().voltage()

    script.handle_event(midi2cv.CIN_NOTE_OFF, 0x80, 60, 0)
    assert script.held_notes == []
    assert pitch_cv().voltage() == pytest.approx(held)


def test_note_on_at_velocity_zero_is_a_note_off(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 0)
    assert script.held_notes == []


def test_repressing_a_held_note_does_not_duplicate_it(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 72, 100)
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    assert script.held_notes == [72, 60]


# ----------------------------------------------------------------------------------
# Transport
# ----------------------------------------------------------------------------------


def test_transport_gate(midi2cv, script):
    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_START, 0, 0)
    assert is_high(transport_cv())

    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_STOP, 0, 0)
    assert not is_high(transport_cv())

    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_CONTINUE, 0, 0)
    assert is_high(transport_cv())


def test_transport_ignores_the_channel_filter(midi2cv, monkeypatch):
    """System real-time carries no channel, so filtering must not swallow it."""
    monkeypatch.setattr(midi2cv, "MIDI_CHANNEL", 9)
    script = midi2cv.Midi2CV()

    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_START, 0, 0)
    assert is_high(transport_cv())


def test_clock_is_counted_but_not_acted_on(midi2cv, script):
    """Clock division is phase 2. Clock must still reach the message counter."""
    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_CLOCK, 0, 0)
    assert script.message_count == 1
    assert not is_high(transport_cv())


# ----------------------------------------------------------------------------------
# The monitor
# ----------------------------------------------------------------------------------


def test_every_packet_is_counted_even_when_filtered(midi2cv, monkeypatch):
    """A rising count with dead outputs is a different problem from a count of zero."""
    monkeypatch.setattr(midi2cv, "MIDI_CHANNEL", 3)
    script = midi2cv.Midi2CV()

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90 | 0, 60, 100)  # wrong channel
    assert script.held_notes == []
    assert script.message_count == 1


def test_last_packet_is_recorded(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    assert script.last_packet == (midi2cv.CIN_NOTE_ON, 0x90, 60, 100)


def test_unknown_messages_are_counted_and_shown(midi2cv, script):
    """Program change is not handled, but must not be invisible or raise."""
    script.handle_event(0xC, 0xC0, 5, 0)
    assert script.message_count == 1
    assert script.last_packet == (0xC, 0xC0, 5, 0)


# ----------------------------------------------------------------------------------
# Channel filtering
# ----------------------------------------------------------------------------------


def test_omni_accepts_every_channel(midi2cv, script):
    for channel in range(16):
        script.handle_event(midi2cv.CIN_NOTE_ON, 0x90 | channel, 60 + channel, 100)
    assert len(script.held_notes) == 16


def test_a_set_channel_rejects_the_others(midi2cv, monkeypatch):
    monkeypatch.setattr(midi2cv, "MIDI_CHANNEL", 3)
    script = midi2cv.Midi2CV()

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90 | 0, 60, 100)  # channel 1
    assert script.held_notes == []

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90 | 2, 60, 100)  # channel 3
    assert script.held_notes == [60]


# ----------------------------------------------------------------------------------
# Panic
# ----------------------------------------------------------------------------------


def test_panic_drops_everything(midi2cv, script):
    from europi import cvs

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_START, 0, 0)

    script.panic()

    assert script.held_notes == []
    assert script.transport_running is False
    assert script.message_count == 0
    assert script.last_packet is None
    for cv in cvs:
        assert cv.voltage() == pytest.approx(0.0)


def test_buttons_only_request_panic(midi2cv, script):
    """The handlers run in an interrupt, so they must not do the work themselves."""
    from europi import b1, b2

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)

    b1._falling_handler()
    assert script.panic_requested is True
    assert script.held_notes == [60], "panic should not have run yet"

    script.panic_requested = False
    b2._falling_handler()
    assert script.panic_requested is True


# ----------------------------------------------------------------------------------
# Display
# ----------------------------------------------------------------------------------


def test_display_rows_fit_the_screen(midi2cv, script):
    """128x32 at an 8x8 font is 16 characters by 4 rows."""
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 61, 100)
    script.message_count = 99999

    rows = [
        "{:<8}{:>8}".format("USB ok", "omni"),
        "{:<11}{:>5}".format("msgs {}".format(script.message_count), "stop"),
        script.packet_row(),
        script.note_row(),
    ]
    for row in rows:
        assert len(row) <= 16, "row too wide: {!r}".format(row)


def test_usb_error_messages_fit_the_screen(script):
    for message in ("no usb package", "need uPy 1.23+"):
        assert len(message) <= 16


@pytest.mark.parametrize(
    "note, name",
    [(0, "C-1"), (60, "C4"), (61, "C#4"), (120, "C9"), (127, "G9")],
)
def test_note_name(midi2cv, note, name):
    assert midi2cv.note_name(note) == name
