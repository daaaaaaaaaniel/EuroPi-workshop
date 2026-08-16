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
    """A script with the default route map."""
    return midi2cv.Midi2CV()


def gate_cv():
    from europi import cvs

    return cvs[0]


def is_high(cv):
    """The outputs read back through a calibration table, so compare generously."""
    return cv.voltage() > 1.0


# ----------------------------------------------------------------------------------
# Pitch mapping
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


def test_bend_is_applied_before_clamping(midi2cv, script):
    script.handle_pitch_bend(16383)  # full bend up
    assert script.note_to_voltage(60) == pytest.approx(5 + 2 / 12, abs=1e-3)

    script.handle_pitch_bend(0)  # full bend down
    assert script.note_to_voltage(60) == pytest.approx(5 - 2 / 12, abs=1e-3)

    # Bending up at the top of the range clamps rather than wrapping
    script.handle_pitch_bend(16383)
    assert script.note_to_voltage(120) == pytest.approx(10.0)


def test_bend_can_be_disabled(midi2cv, monkeypatch):
    monkeypatch.setattr(midi2cv, "PITCH_BEND_SEMITONES", 0)
    script = midi2cv.Midi2CV()
    script.handle_pitch_bend(16383)
    assert script.note_to_voltage(60) == pytest.approx(5.0)


# ----------------------------------------------------------------------------------
# Note stack
# ----------------------------------------------------------------------------------


def test_last_note_wins(script):
    script.handle_note_on(60, 100)
    script.handle_note_on(64, 100)
    assert script.notes.current() == 64


def test_release_falls_back_to_a_held_note(script):
    script.handle_note_on(60, 100)
    script.handle_note_on(64, 100)
    script.handle_note_off(64)
    assert script.notes.current() == 60


def test_repressing_a_held_note_does_not_duplicate_it(script):
    script.handle_note_on(60, 100)
    script.handle_note_on(64, 100)
    script.handle_note_on(60, 100)
    assert script.notes.notes == [64, 60]


def test_pitch_holds_when_every_note_is_released(midi2cv, script):
    from europi import cvs

    script.handle_note_on(60, 100)
    pitch = cvs[1].voltage()
    script.handle_note_off(60)
    assert cvs[1].voltage() == pytest.approx(pitch)


def test_gate_falls_when_every_note_is_released(midi2cv, script):
    script.handle_note_on(60, 100)
    script.service_timers(utime.ticks_add(utime.ticks_ms(), midi2cv.GATE_RETRIGGER_MS + 1))
    assert is_high(gate_cv())

    script.handle_note_off(60)
    assert not is_high(gate_cv())


def test_note_on_at_velocity_zero_is_a_note_off(midi2cv, script):
    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 100)
    assert script.notes.notes == [60]

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90, 60, 0)
    assert script.notes.notes == []


def test_all_notes_off_clears_a_stuck_gate(midi2cv, script):
    script.handle_note_on(60, 100)
    script.service_timers(utime.ticks_add(utime.ticks_ms(), midi2cv.GATE_RETRIGGER_MS + 1))
    assert is_high(gate_cv())

    script.handle_event(midi2cv.CIN_CONTROL_CHANGE, 0xB0, midi2cv.CC_ALL_NOTES_OFF, 0)
    assert script.notes.notes == []
    assert not is_high(gate_cv())


# ----------------------------------------------------------------------------------
# Gate retrigger
# ----------------------------------------------------------------------------------


def test_the_first_note_of_a_phrase_attacks_immediately(script):
    """There is nothing to retrigger when the gate is already low.

    Dipping it anyway would delay the first note of every phrase by the dip length.
    """
    script.handle_note_on(60, 100)
    assert is_high(gate_cv())
    assert script.gate_raise_at[0] is None, "no dip should have been scheduled"


def test_note_on_over_a_held_note_dips_the_gate_then_raises_it(midi2cv, script):
    script.handle_note_on(60, 100)
    script.handle_note_on(64, 100)
    assert not is_high(gate_cv()), "gate should drop for the retrigger dip"

    script.service_timers(utime.ticks_add(utime.ticks_ms(), midi2cv.GATE_RETRIGGER_MS + 1))
    assert is_high(gate_cv())


def test_notes_faster_than_the_dip_do_not_hold_the_gate_low(midi2cv, script):
    """A dip already in progress finishes rather than restarting.

    Restarting it on every note-on lets a fast run of notes pin the gate low for as
    long as the run lasts.
    """
    now = utime.ticks_ms()
    script.handle_note_on(60, 100)

    elapsed = 0
    for step in range(6):
        elapsed += 1  # a note every 1ms, well inside the dip
        script.service_timers(utime.ticks_add(now, elapsed))
        script.handle_note_on(61 + step, 100)

    script.service_timers(utime.ticks_add(now, elapsed + midi2cv.GATE_RETRIGGER_MS + 1))
    assert is_high(gate_cv()), "gate should have recovered despite the run of notes"


def test_a_note_released_during_the_dip_leaves_the_gate_low(midi2cv, script):
    script.handle_note_on(60, 100)
    script.handle_note_on(64, 100)  # this one dips the gate
    script.handle_note_off(64)
    script.handle_note_off(60)
    script.service_timers(utime.ticks_add(utime.ticks_ms(), midi2cv.GATE_RETRIGGER_MS + 1))
    assert not is_high(gate_cv())


def test_note_off_does_not_retrigger(midi2cv, script):
    """Releasing back to a held note moves pitch without re-attacking."""
    script.handle_note_on(60, 100)
    script.handle_note_on(64, 100)
    script.service_timers(utime.ticks_add(utime.ticks_ms(), midi2cv.GATE_RETRIGGER_MS + 1))

    script.handle_note_off(64)
    assert is_high(gate_cv()), "gate should stay high across the release"
    assert script.gate_raise_at[0] is None, "no new dip should be pending"


# ----------------------------------------------------------------------------------
# Route resolution
# ----------------------------------------------------------------------------------


def test_default_route_map(script):
    assert script.route_map == ["gate", "pitch", "velocity", "cc", "transport", "clock"]


def test_unrecognised_route_falls_back_to_none(midi2cv, monkeypatch):
    monkeypatch.setattr(
        midi2cv, "ROUTES", ["gate", "wobble", "pitch", "clock", "none", "aftertouch"]
    )
    script = midi2cv.Midi2CV()
    assert script.route_map[1] == "none"
    assert script.route_map[5] == "aftertouch"


def test_a_short_routes_list_is_padded(midi2cv, monkeypatch):
    monkeypatch.setattr(midi2cv, "ROUTES", ["gate", "pitch"])
    script = midi2cv.Midi2CV()
    assert script.route_map == ["gate", "pitch", "none", "none", "none", "none"]


def test_duplicate_routes_are_allowed(midi2cv, monkeypatch):
    monkeypatch.setattr(midi2cv, "ROUTES", ["clock"] * 6)
    script = midi2cv.Midi2CV()
    assert len(script.clock_outs) == 6


@pytest.mark.parametrize(
    "route, attribute",
    [
        ("gate", "gate_outs"),
        ("pitch", "pitch_outs"),
        ("velocity", "velocity_outs"),
        ("cc", "cc_outs"),
        ("aftertouch", "aftertouch_outs"),
        ("transport", "transport_outs"),
        ("clock", "clock_outs"),
    ],
)
def test_every_route_type_reaches_its_output_list(midi2cv, monkeypatch, route, attribute):
    monkeypatch.setattr(midi2cv, "ROUTES", [route] + ["none"] * 5)
    script = midi2cv.Midi2CV()
    assert [index for index, _ in getattr(script, attribute)] == [0]


# ----------------------------------------------------------------------------------
# Clock and transport
# ----------------------------------------------------------------------------------


def clock_pulses_over(script, midi2cv, ticks):
    """Tick the MIDI clock and return the tick numbers a pulse started on."""
    from europi import cvs

    fired = []
    for tick in range(ticks):
        was_high = is_high(cvs[5])
        script.handle_realtime(midi2cv.MIDI_CLOCK)
        if is_high(cvs[5]) and not was_high:
            fired.append(tick)
        script.service_timers(utime.ticks_add(utime.ticks_ms(), midi2cv.TRIGGER_MS + 1))
    return fired


def test_clock_division(midi2cv, script):
    """24 PPQN in, 4 PPQN out, so a pulse every sixth tick."""
    script.handle_realtime(midi2cv.MIDI_START)
    assert clock_pulses_over(script, midi2cv, 24) == [0, 6, 12, 18]


def test_start_resets_the_beat(midi2cv, script):
    script.handle_realtime(midi2cv.MIDI_START)
    clock_pulses_over(script, midi2cv, 4)
    script.handle_realtime(midi2cv.MIDI_START)
    assert script.clock_tick == 0


def test_continue_preserves_the_beat(midi2cv, script):
    script.handle_realtime(midi2cv.MIDI_START)
    clock_pulses_over(script, midi2cv, 4)

    script.handle_realtime(midi2cv.MIDI_STOP)
    tick_at_stop = script.clock_tick
    script.handle_realtime(midi2cv.MIDI_CONTINUE)
    assert script.clock_tick == tick_at_stop


def test_transport_run_gate(midi2cv, script):
    from europi import cvs

    script.handle_realtime(midi2cv.MIDI_START)
    assert is_high(cvs[4])

    script.handle_realtime(midi2cv.MIDI_STOP)
    assert not is_high(cvs[4])

    script.handle_realtime(midi2cv.MIDI_CONTINUE)
    assert is_high(cvs[4])


# ----------------------------------------------------------------------------------
# Channel filtering
# ----------------------------------------------------------------------------------


def test_omni_accepts_every_channel(script):
    for channel in range(16):
        script.handle_event(0x9, 0x90 | channel, 60 + channel, 100)
    assert len(script.notes.notes) == 16


def test_a_set_channel_rejects_the_others(midi2cv, monkeypatch):
    monkeypatch.setattr(midi2cv, "MIDI_CHANNEL", 3)
    script = midi2cv.Midi2CV()

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90 | 0, 60, 100)  # channel 1
    assert script.notes.notes == []

    script.handle_event(midi2cv.CIN_NOTE_ON, 0x90 | 2, 60, 100)  # channel 3
    assert script.notes.notes == [60]


def test_clock_ignores_the_channel_filter(midi2cv, monkeypatch):
    """System real-time carries no channel, so filtering must not swallow it."""
    monkeypatch.setattr(midi2cv, "ROUTES", ["clock"] + ["none"] * 5)
    monkeypatch.setattr(midi2cv, "MIDI_CHANNEL", 9)
    script = midi2cv.Midi2CV()

    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_START, 0, 0)
    script.handle_event(midi2cv.CIN_SINGLE_BYTE, midi2cv.MIDI_CLOCK, 0, 0)
    assert script.pulse_off_at[0] is not None


# ----------------------------------------------------------------------------------
# Panic
# ----------------------------------------------------------------------------------


def test_panic_drops_everything(midi2cv, script):
    from europi import cvs

    script.handle_note_on(60, 100)
    script.handle_pitch_bend(16383)
    script.handle_event(midi2cv.CIN_CONTROL_CHANGE, 0xB0, midi2cv.CC_NUMBER, 127)
    script.handle_realtime(midi2cv.MIDI_START)

    script.panic()

    assert script.notes.notes == []
    assert script.bend_semitones == 0
    assert script.cc_value == 0
    assert script.transport_running is False
    assert script.clock_tick == 0
    for cv in cvs:
        assert cv.voltage() == pytest.approx(0.0)


def test_transport_restarts_after_panic(midi2cv, script):
    from europi import cvs

    script.handle_realtime(midi2cv.MIDI_START)
    script.panic()
    assert not is_high(cvs[4])

    script.handle_realtime(midi2cv.MIDI_START)
    assert is_high(cvs[4])


def test_buttons_only_request_panic(script):
    """The handlers run in an interrupt, so they must not do the work themselves."""
    from europi import b1, b2

    script.handle_note_on(60, 100)

    b1._falling_handler()
    assert script.panic_requested is True
    assert script.notes.notes == [60], "panic should not have run yet"

    script.panic_requested = False
    b2._falling_handler()
    assert script.panic_requested is True


# ----------------------------------------------------------------------------------
# Display
# ----------------------------------------------------------------------------------


def test_display_rows_fit_the_screen(midi2cv, script):
    """128x32 at an 8x8 font is 16 characters by 4 rows."""
    script.last_note = 61
    script.last_velocity = 96

    rows = [
        "{:<8}{:>8}".format("USB ok", "omni"),
        "{:<4} v{:<3} {:+.1f}".format(midi2cv.note_name(61), 96, 0.0),
        script.route_row(0),
        script.route_row(3),
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
