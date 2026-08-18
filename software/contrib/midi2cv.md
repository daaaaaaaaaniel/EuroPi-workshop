# MIDI to CV

Turns EuroPi into a USB MIDI device. Plug it into a computer, phone or tablet with the
Pico's own USB cable — the same one you use for programming — and it appears in the host's
MIDI port list as `EuroPi`. No MIDI hardware, adaptor or interface circuit is needed.

**This is phase 1, and it is deliberately tiny.** It exists to answer one question on real
hardware: does USB MIDI reach EuroPi at all? Everything that could obscure that answer has
been left out. There is no output routing, no velocity, no CC, no aftertouch, no clock
division and no gate retrigger logic. Those arrive in phase 2 — see the roadmap at the
bottom.

**Labels:** MIDI, CV Generation, Controller

## Requirements

- **MicroPython 1.23 or newer.** The script uses `machine.USBDevice`, which does not exist
  in earlier builds. Official EuroPi release firmware is built on 1.25.0, so a stock
  release is fine. If you build your own firmware, note that `create_custom_firmware_uf2.md`
  still references v1.20.0, which is too old.
- **The `experimental/usb/` package must be on the module.** See "Deploying" below — the
  standard deploy script does not copy it.

If either is missing the script still starts and says so on the display, rather than
vanishing from the menu.

# Controls and Outputs

## Inputs

- `digital_in`: Unused
- `analog_in`: Unused

## Knobs

- `k1`: Unused
- `k2`: Unused

## Buttons

- `b1`: Panic, on release
- `b2`: Panic, on release

Both do the same thing. Panic returns the module to its power-on state without rebooting:
all six outputs to 0V, held notes cleared, transport stopped, and the message counter
reset to zero.

## Outputs

| Output       | Behaviour                                                |
| ------------ | -------------------------------------------------------- |
| `cv1`        | Transport gate — high between MIDI Start/Continue and Stop |
| `cv2`        | Pitch — 1V/octave from the most recent note               |
| `cv3` – `cv6`| Unused, held at 0V                                        |

These two were chosen because they share no logic. `cv1` is driven only by system
real-time messages and `cv2` only by note messages, so between them they prove both halves
of the MIDI path — and if one works while the other doesn't, that narrows the fault
immediately.

# The display

The display is the real deliverable of phase 1. A module that does nothing tells you
nothing; this tells you where it stopped.

```
USB ok      omni
msgs 2       RUN
pkt 9 90 3D 64
C#4       5.083V
```

- **Row 1** — link state and MIDI channel. `USB --` means the host has not enumerated the
  device yet. An error message replaces this row if USB could not start at all.
- **Row 2** — a running count of every packet received, and the transport state.
- **Row 3** — the last raw packet, as the code index number followed by the three MIDI
  bytes, in hex. Anything the script doesn't act on still shows up here.
- **Row 4** — the most recent note and the voltage on `cv2`.

The counter deliberately counts **every** packet, before any channel filtering. A count
that rises while the outputs stay dead is a completely different problem from a count stuck
at zero:

| What you see                     | What it means                                          |
| -------------------------------- | ------------------------------------------------------ |
| `USB --` forever                  | Host never enumerated it. USB cable, or C7 (see below) |
| `USB ok`, count stuck at 0        | Enumerated, but nothing is being sent. Check the DAW's output routing |
| Count rising, outputs dead        | MIDI is arriving. Wrong channel, or wrong message type — read row 3 |
| Count rising, `cv2` moves         | Working                                                 |

# Configuration

Edit the constants at the top of `midi2cv.py`, redeploy and rerun.

| Constant          | Default    | Meaning                                   |
| ----------------- | ---------- | ----------------------------------------- |
| `MIDI_CHANNEL`    | `0`        | 0 for omni, or 1-16                        |
| `BASE_NOTE`       | `0`        | The MIDI note that sits at 0V              |
| `KEEP_USB_REPL`   | `True`     | Keep the serial REPL alive alongside MIDI  |
| `USB_DEVICE_NAME` | `"EuroPi"` | The name the host lists in its MIDI ports  |

## If Windows doesn't see the module, try `KEEP_USB_REPL = False` first

With `KEEP_USB_REPL` true, EuroPi presents itself as a composite device: MicroPython's
usual CDC serial port *and* the MIDI interface. That is convenient — Thonny and mpremote
keep working while the script runs — but it is the configuration most likely to fail on
Windows.

[multi-midi](https://github.com/HLammers/multi-midi), another MicroPython USB MIDI library
for RP2, disables the REPL outright and gives the reason plainly: a Windows host will not
recognise the MIDI ports if CDC and MIDI are both enabled. Its documentation treats losing
the REPL as the accepted cost, advising you to disable USB MIDI when you need to debug.

Neither that library nor the one vendored here emits an Interface Association Descriptor,
which is what a composite device normally needs for a host to group its interfaces
correctly — so there is good reason to expect the same behaviour from ours.

Setting `KEEP_USB_REPL = False` drops the serial port and leaves MIDI alone on the bus.
You lose Thonny and mpremote for as long as the script runs, so plan how you will get back:
returning to the menu resets the module and brings the REPL back.

## Pitch range

Pitch is 1V per octave from `BASE_NOTE`, which defaults to 0 so MIDI note 0 sits at 0V:

| MIDI note | Name                    | Output            |
| --------- | ----------------------- | ----------------- |
| 0         | C-1                     | 0.000 V           |
| 21        | A0, bottom of an 88-key | 1.750 V           |
| 60        | C4, middle C            | 5.000 V           |
| 108       | C8, top of an 88-key    | 9.000 V           |
| 120       | C9                      | 10.000 V          |
| 121-127   | C#9 - G9                | 10.000 V, clamped |

This covers a full 88-key keyboard with headroom at both ends and uses the entire output
range, sacrificing only the seven notes above C9 that virtually nothing transmits. Middle C
landing on exactly 5V falls out of the same choice.

With nothing held, pitch holds its last value rather than falling to 0V, which would make
an audible dive on any oscillator still tracking it.

# Getting your host to send MIDI

Sending notes and sending clock or transport are often separate switches, and the second
one is easy to miss. In **Ableton Live**, `Preferences > MIDI` has a *Track* and a *Sync*
toggle per output — without *Sync*, Live sends no transport or clock at all, so `cv1` stays
dead while notes work perfectly. Most DAWs have an equivalent setting.

## EuroPi is a MIDI device, not a MIDI host

You cannot plug a keyboard into EuroPi. The Pico's USB port acts as a device, so it
connects *to* a computer, phone or tablet, and that host sends it MIDI. Playing from a
hardware keyboard means routing through the host, or waiting for the serial MIDI transport
on the roadmap.

## What the host sees

EuroPi appears under `USB_DEVICE_NAME`, defaulting to `EuroPi`, with manufacturer
`Allen Synthesis`. Hosts derive the port name from the product string and append their own
suffix, so expect `EuroPi` or `EuroPi MIDI 1` depending on platform — the vendored library
hardcodes `iJack = 0x00` with the comment "no string descriptor support yet"
(`midi.py:261`, `:278`), so individual jacks carry no name of their own. With
`KEEP_USB_REPL` true the serial port Thonny sees carries the same name, which is why the
default names the module rather than the script.

Naming the jacks is possible if we ever want it — [multi-midi](https://github.com/HLammers/multi-midi)
does it by appending each port name to the device's string table and using its index as
`iJack`, which is a small patch to the vendored file. Two caveats from that project: the
name is not shown on a Windows host anyway, and a name shorter than two characters makes
Windows fail to recognise the device at all.

VID and PID are left as MicroPython's. USB vendor IDs are assigned by USB-IF and cost
money. The serial number falls back to the Pico's flash unique ID, so two modules with
identical names are still distinguishable.

## Launching interrupts the USB connection

Starting the script reconfigures the USB interface, which forces the device to disconnect
and re-enumerate. Any live Thonny or mpremote session drops at that moment and comes back a
second later. Returning to the menu resets the module, so the MIDI device disappears and
plain serial returns.

**This is the main unknown in phase 1.** How hosts react to the device vanishing and
returning is not verifiable from source — DAWs vary, some rescan cleanly, some need the
port reselected. Testing it is a large part of what phase 1 is for.

# Deploying

**Deploy the whole firmware from source, not just this script.** On a stock release `.uf2`
the firmware is frozen into the image, and `/lib` shadows a frozen package *wholesale*
rather than merging with it — so dropping a lone `experimental/usb/` into `/lib` would
hide the frozen `experimental` package entirely and take `experimental_config` and `wifi`
with it. `europi.py:41-42` imports both at boot, for every script, so the module would stop
booting.

The supported route is the project's own deploy target, which copies the full firmware and
contrib tree into `/lib`:

```sh
make deploy_firmware
```

That leaves one gap. `scripts/deploy_firmware.rshell` copies `experimental/*.py` without
recursing, so it **does not deploy the nested `experimental/usb/` package** — the same gap
that already affects `experimental/clocks/` and `experimental/fonts/`. Add it afterwards:

```sh
mpremote mkdir :/lib/experimental/usb
mpremote mkdir :/lib/experimental/usb/device
mpremote cp software/firmware/experimental/usb/__init__.py :/lib/experimental/usb/
mpremote cp software/firmware/experimental/usb/device/*.py :/lib/experimental/usb/device/
```

If the package is missing, the display shows `no usb package` instead of the link state,
which is a clean failure rather than a broken boot.

Two caveats worth knowing before you start:

- **You cannot bring this up by deploying it as `/main.py`.** The release firmware freezes
  its own `main.py`, and a frozen `main.py` autostarts in preference to one in `/`. Launch
  it from the menu instead.
- **Import priority is worth confirming on your own module.** This project's
  `create_custom_firmware_uf2.md` states that `/` and `/lib` are searched before frozen
  modules, whereas upstream MicroPython's default `sys.path` puts `.frozen` ahead of
  `/lib`. The deploy workflow above assumes the project's version is right for this port.
  If it is not, `make deploy_firmware` would have no effect at all and the frozen firmware
  would keep running — so if your changes appear to do nothing, check this first.

# Bring-up checklist

Phase 1 is finished when all of these pass:

1. The module enumerates on a host and appears as `EuroPi`, not `Board in FS mode`
2. With `KEEP_USB_REPL` true, the serial port still works in Thonny or mpremote
3. **On Windows specifically**, the MIDI ports appear at all with `KEEP_USB_REPL` true —
   and if they do not, that they appear with it false
4. Playing notes moves `cv2`, and the voltage matches the table above on a meter
5. Pressing play in a DAW raises `cv1`; stop drops it
6. The message counter rises with incoming MIDI
7. Returning to the menu and launching another script leaves the host in a sane state
8. Power-cycling with midi2cv as the last-run script re-enumerates cleanly
9. Latency is acceptable by ear, playing a keyboard through a DAW

Items 7 and 8 are the ones nothing can be predicted about from source. Item 3 is the one
another project has already reported failing.

# Credits

The USB device support under `experimental/usb/` is vendored unmodified from
[micropython-lib](https://github.com/micropython/micropython-lib) (`usb-device` 0.2.1 and
`usb-device-midi` 0.1.0), MIT licensed. See `experimental/usb/__init__.py` for provenance
and the full licence text.

The note-to-voltage mapping follows
[Europi_BLE_MIDI](https://github.com/cob333/Europi_BLE_MIDI), a BLE MIDI firmware for
EuroPi written in C. [Winterbloom Sol](https://github.com/wntrblm/Sol), a CircuitPython USB
MIDI to CV module, informed the output choices and the gate handling that arrives in
phase 2.

# Roadmap

1. **Phase 1 — prove the transport.** This script. Two outputs and a monitor, so a hardware
   or enumeration problem cannot be confused with a logic problem.
2. **Phase 2 — the full output map.** All six outputs routable to gate, pitch, velocity,
   CC, aftertouch, transport, clock or none, with gate retrigger, clock division and pitch
   bend. Configured by editing a `ROUTES` list in the script.
3. **Phase 3 — per-output behaviour.** Per-output MIDI channel, note selection (first,
   last, low, high), release behaviour and gate mode, moved into a proper configuration
   file. Two gate/pitch/velocity trios on different channels become two genuinely
   independent voices.
4. **Phase 4 — panel UI.** Knobs, buttons and an interactive OLED, so the configuration can
   be changed without editing files.
5. **Phase 5 — Bluetooth MIDI.** A second transport behind the same seam. Requires a Pico W
   or Pico 2 W — a standard EuroPi has no radio.
6. **Phase 6 — serial MIDI.** A third transport, and the only one that accepts an
   instrument directly. Requires an opto-isolator circuit.
