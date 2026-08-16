# MIDI to CV

Turns EuroPi into a USB MIDI device, so a computer, phone or tablet can play it as a monophonic
voice. Pitch, gate, velocity, CC, transport and clock come out of the six CV outputs.

Plug EuroPi into the host with the Pico's own USB cable — the same one you use for programming. No
MIDI hardware, adaptor or interface circuit is needed.

This is the first phase of a larger design. Everything is fixed in constants at the top of
`midi2cv.py`; there is no configuration file, and the knobs do nothing. Reassign the outputs by
editing `ROUTES`, then redeploy. Either button panics.

## Requirements

- **MicroPython 1.23 or newer.** The script uses `machine.USBDevice`, which does not exist in
  earlier builds. Official EuroPi release firmware is built on 1.25.0, so a stock release is fine.
  If you build your own firmware, note that `create_custom_firmware_uf2.md` still references
  v1.20.0, which is too old.
- **The `experimental/usb/` package must be on the module.** See "Deploying" below — the standard
  deploy script does not copy it.

If either is missing the script still starts and says so on the display, rather than vanishing from
the menu.

# Controls and Outputs

## Inputs

- `digital_in`: Unused
- `analog_in`: Unused

## Knobs

- `k1`: Unused in phase 1
- `k2`: Unused in phase 1

## Buttons

- `b1`: Panic, on release
- `b2`: Panic, on release

Both buttons do the same thing deliberately. Panic is a safety net rather than an interface, and
there is nothing to remember while something is stuck on.

Panic returns the module to its power-on state without rebooting:

- All held notes released and the note stack emptied
- Pitch bend reset to centre
- CC and aftertouch values reset to zero
- Transport stopped and the run gate dropped
- Clock divider phase reset
- All six outputs set to 0V, whatever their route

One consequence worth knowing: a pitch output driving something ungated — a drone oscillator, a
filter cutoff — jumps to 0V rather than holding its last note. That is inherent to a full reset. It
differs from an ordinary note-off, where pitch holds precisely to avoid that jump.

Sending All Notes Off (CC 123) or All Sound Off (CC 120) from the host also clears a stuck gate.

## Outputs

The default map:

| Output | Route       | Behaviour                                                        |
| ------ | ----------- | ---------------------------------------------------------------- |
| `cv1`  | `gate`      | High while a note is held; dips low briefly so envelopes re-fire |
| `cv2`  | `pitch`     | 1V/octave, including pitch bend                                   |
| `cv3`  | `velocity`  | Velocity of the sounding note                                     |
| `cv4`  | `cc`        | CC number 1 — the mod wheel                                       |
| `cv5`  | `transport` | High between MIDI Start/Continue and Stop                         |
| `cv6`  | `clock`     | 4 pulses per quarter note — sixteenth notes                       |

This default exercises every class of MIDI message across all six jacks, which is the point of it:
if all six behave, the MIDI path works end to end.

# Configuration

Phase 1 has no configuration file. Edit the constants at the top of `midi2cv.py`, redeploy and
rerun. `consequencer.py` sets the precedent here — it directs you to edit its pattern arrays in the
`.py` directly.

## Reassigning the outputs

`ROUTES` has one entry per output, `cv1` to `cv6`:

```python
ROUTES = [
    "gate",       # cv1
    "pitch",      # cv2
    "velocity",   # cv3
    "cc",         # cv4
    "transport",  # cv5
    "clock",      # cv6
]
```

Any output can take any route type:

| Type         | Behaviour                                                    |
| ------------ | ------------------------------------------------------------ |
| `gate`       | High while a note is held                                     |
| `pitch`      | 1V/octave from the held note, plus pitch bend                 |
| `velocity`   | Velocity of the held note, as a fraction of full scale        |
| `cc`         | CC value as a fraction of full scale                          |
| `aftertouch` | Channel pressure as a fraction of full scale                  |
| `transport`  | High between Start/Continue and Stop                          |
| `clock`      | Pulses at `CLOCK_PPQN` per quarter note                       |
| `none`       | Held at 0V                                                    |

Duplicates are allowed and useful — two `clock` outputs work fine, and once phase 2 adds per-output
clock divisions they can run at different rates. An unrecognised entry falls back to `none` rather
than stopping the script, and the resolved map is shown on the display so a typo is visible.

## Other settings

| Constant               | Default    | Meaning                                              |
| ---------------------- | ---------- | ---------------------------------------------------- |
| `MIDI_CHANNEL`         | `0`        | 0 for omni, or 1-16                                   |
| `BASE_NOTE`            | `0`        | The MIDI note that sits at 0V                         |
| `PITCH_BEND_SEMITONES` | `2`        | Bend range either side of centre; 0 disables bend     |
| `CC_NUMBER`            | `1`        | Which CC the `cc` route follows                       |
| `CLOCK_PPQN`           | `4`        | Clock pulses per quarter note; must divide into 24    |
| `TRIGGER_MS`           | `10`       | Width of clock pulses                                 |
| `GATE_RETRIGGER_MS`    | `5`        | How long the gate drops on a retrigger                |
| `KEEP_USB_REPL`        | `True`     | Keep the serial REPL alive alongside MIDI             |
| `USB_DEVICE_NAME`      | `"EuroPi"` | The name the host lists in its MIDI ports             |

### Pitch range

Pitch is 1V per octave from `BASE_NOTE`, which defaults to 0 so MIDI note 0 sits at 0V:

| MIDI note | Name                    | Output           |
| --------- | ----------------------- | ---------------- |
| 0         | C-1                     | 0.000 V          |
| 21        | A0, bottom of an 88-key | 1.750 V          |
| 60        | C4, middle C            | 5.000 V          |
| 108       | C8, top of an 88-key    | 9.000 V          |
| 120       | C9                      | 10.000 V         |
| 121-127   | C#9 - G9                | 10.000 V, clamped |

This covers a full 88-key keyboard with headroom at both ends and uses the entire output range,
sacrificing only the seven notes above C9 that virtually nothing transmits. Middle C landing on
exactly 5V falls out of the same choice.

Raising `BASE_NOTE` shifts the window up: every note below it clamps to 0V and the top of the range
becomes unreachable. At 36, for instance, the bottom fifteen notes of a piano all produce 0V and
nothing above 7.58V is ever output.

### Sustain pedal

There is no special sustain handling. CC 64 is an ordinary CC, so setting `CC_NUMBER = 64` gives you
a control voltage that follows the pedal. Note this is a voltage, not note-level sustain — gate and
pitch still fall when you release the keys. Patch it into a VCA or envelope hold if you want a
sustain-like result.

# The display

Read-only, and refreshed a few times a second so it never competes with the MIDI path:

```
USB ok      omni
C#4  v96   +0.0
1gat 2pit 3vel
4cc  5trn 6clk
```

- **Row 1** — link state and MIDI channel. `USB --` means the host has not enumerated the device
  yet. An error message replaces this row if the script could not start USB at all.
- **Row 2** — the last note received, its velocity, and the current pitch bend in semitones.
- **Rows 3 and 4** — the resolved route map, so you can see at a glance what each output is doing.

# What the host sees

EuroPi appears in the host's MIDI port list under `USB_DEVICE_NAME`, which defaults to `EuroPi`.
The manufacturer string is `Allen Synthesis`.

Some things worth knowing:

- **The port name is not exactly controllable.** Hosts derive it from the device's product string
  and append their own suffix, so expect `EuroPi` or `EuroPi MIDI 1` depending on platform. The
  vendored library has no string descriptor support for individual jacks.
- **The name covers the whole device, not just MIDI.** With `KEEP_USB_REPL` true, the serial port
  Thonny sees carries the same name. That is why the default is the module's name rather than the
  script's.
- **VID and PID are left as MicroPython's.** USB vendor IDs are assigned by USB-IF and cost money.
  The serial number falls back to the Pico's flash unique ID, so two modules with identical names
  are still distinguishable.

## EuroPi is a MIDI device, not a MIDI host

You cannot plug a keyboard into EuroPi. The Pico's USB port acts as a device, so it connects *to* a
computer, phone or tablet, and that host sends it MIDI. Playing from a hardware keyboard means
routing through the host, or waiting for the serial MIDI transport on the roadmap.

## Launching interrupts the USB connection

Starting the script reconfigures the USB interface, which forces the device to disconnect and
re-enumerate. Any live Thonny or mpremote session drops at that moment and comes back a second
later. Returning to the menu resets the module, so the MIDI device disappears and plain serial
returns.

# Deploying

The vendored USB package lives at `software/firmware/experimental/usb/`, which is a nested package.
`scripts/deploy_firmware.rshell` copies `experimental/*.py` without recursing, so **it does not
deploy this package**. The same gap already affects `experimental/clocks/` and `experimental/fonts/`.

Until the deploy script is fixed, copy the package to the module by hand — with `mpremote`:

```sh
mpremote mkdir :/lib/experimental/usb
mpremote mkdir :/lib/experimental/usb/device
mpremote cp software/firmware/experimental/usb/__init__.py :/lib/experimental/usb/
mpremote cp software/firmware/experimental/usb/device/*.py :/lib/experimental/usb/device/
```

If the package is missing, the display shows `no usb package` instead of the link state.

# Credits

The USB device support under `experimental/usb/` is vendored unmodified from
[micropython-lib](https://github.com/micropython/micropython-lib) (`usb-device` 0.2.1 and
`usb-device-midi` 0.1.0), MIT licensed. See `experimental/usb/__init__.py` for provenance and the
full licence text.

The note-to-voltage mapping and the gate retrigger technique follow
[Europi_BLE_MIDI](https://github.com/cob333/Europi_BLE_MIDI), a BLE MIDI firmware for EuroPi
written in C.

# Roadmap

Phase 1, above, is deliberately minimal: fixed behaviours, no UI, outputs reassigned by editing the
script. Its job is to prove the MIDI path and the outputs on real hardware with nothing else able to
obscure the result. Planned after that:

1. **Per-output behaviour.** Per-output MIDI channel, note selection (first, last, low, high),
   release behaviour and gate mode, moved into a proper configuration file. Two gate/pitch/velocity
   trios on different channels become two genuinely independent voices.
2. **Panel UI.** Knobs, buttons and an interactive OLED, so the configuration can be changed without
   editing files.
3. **Bluetooth MIDI.** A second transport behind the same seam. Requires a Pico W or Pico 2 W — a
   standard EuroPi has no radio.
4. **Serial MIDI.** A third transport, and the only one that accepts an instrument directly.
   Requires an opto-isolator circuit.
