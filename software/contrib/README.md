# Contributions

Please see the [contributing guide](/contributing.md) for details on how to contribute a script to this
directory, specifically [the section on contrib scripts](/contributing.md#contrib-scripts).

# List of packaged scripts

### Arpeggiator \[ [documentation](/software/contrib/arp.md) | [script](/software/contrib/arp.py) \]

A quantized scale/arpeggio generator

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: quantizer, scale, arpeggio</i>

### Bernoulli Gates \[ [documentation](/software/contrib/bernoulli_gates.md) | [script](/software/contrib/bernoulli_gates.py) \]

A probability script based on Mutable Instruments Branches

Two channels of probability-based routing, where the digital input will be routed to one of two outputs based on a weighted random chance, controlled by a knob per channel, and the analogue input for channel 1

<i>Author: [Bridgee](https://github.com/Bridgee)</i>
<br><i>Labels: Random</i>

### Bezier Curves \[ [documentation](/software/contrib/bezier.md) | [script](/software/contrib/bezier.py) \]

Smooth random voltages based on bezier curves. Inspired by the ADDAC507 Random Bezier Waves module.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: Random</i>

### Binary Counter \[ [documentation](/software/contrib/binary_counter.md) | [script](/software/contrib/binary_counter.py) \]

A simple gate sequencer implemented using a 6-bit binary counter.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: gates, sequencer, binary</i>

### Bit Garden \[ [documentation](/software/contrib/bit_garden.md) | [script](/software/contrib/bit_garden.py) \]

Mirrors a gate/trigger input, with adjustable skip probability across channels.

<i>Author: [awonak](https://github.com/awonak)</i>
<br><i>Labels: random, triggers</i>

### Bouncing Pixels \[ [documentation](/software/contrib/bouncing_pixels.md) | [script](/software/contrib/bouncing_pixels.py) \]

Pixels bounce around on the display and trigger gates when hitting the edges.

<i>Author: [Jorin](https://github.com/jorins)</i>
<br><i>Labels: gates, random, simulation, triggers</i>

### Clock Modifier \[ [documentation](/software/contrib/clock_mod.md) | [script](/software/contrib/clock_mod.md) \]

A clock multiplier or divider. Each channel has an independently-controllable modifier, multiplying or dividing an external clock signal on `din`.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: clock, clock multiplier, clock divider, gates</i>

### Coin Toss \[ [documentation](/software/contrib/coin_toss.md) | [script](/software/contrib/coin_toss.py) \]

A probability utility with an output based on a percentage choice between 1 or 0

Using the threshold knob and analogue input, users can determine whether a 1 or a 0 is preferred by the weighted random choice each time the digital input is triggered, or an internal clock depending on the mode

<i>Author: [awonak](https://github.com/awonak)</i>
<br><i>Labels: Clock, Random, CV Generation</i>

### Consequencer \[ [documentation](/software/contrib/consequencer.md) | [script](/software/contrib/consequencer.md) \]

A gate and CV sequencer inspired by Mutable Instruments Grids and the Music Thing Modular Turing Machine

Users can morph between patterns and CV sequences during operation, with 3 gate and 3 CV outputs based on the current pattern, programmed randomness, and CV input, running from an external clock

<i>Author: [gamecat69](https://github.com/gamecat69)</i>
<br><i>Labels: sequencer, gates, triggers, drums, randomness</i>

### Conway \[ [documentation](/software/contrib/conway.md) | [script](/software/contrib/conway.md) \]

A semi-random LFO that uses [John Conway's Game Of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) to produce CV and gate signals.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: lfo, gates, randomness</i>

### CVecorder \[ [documentation](/software/contrib/cvecorder.md) | [script](/software/contrib/cvecorder.py) \]

6 channels of control voltage recording

Record 6 banks of 6 channels of control voltage, and then play them back at a consistent rate set by an external clock.
Recording of CV can be primed so that you can record a movement without missing a beat

<i>Author: [anselln](https://github.com/anselln)</i>
<br><i>Labels: sequencer, CV, performance</i>

### Daily Random \[ [documentation](/software/contrib/daily_random.md) | [script](/software/contrib/daily_random.md) \]

A pseudo-random gate and CV sequencer that uses a realtime clock to generate patterns.

Requires installing and configuring a realtime clock module, connected to EuroPi's external I2C interface for best results.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: sequencer, gate, cv, random, realtime clock</i>

### DCSN-2 \[ [documentation](/software/contrib/dscn2.md) | [script](/software/contrib/dcsn2.md) \]

A loopable random gate sequencer based on a binary tree.  Inspired by the Robaux DCSN3

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: sequencer, gates, triggers, randomness</i>

### DFAM Controller \[ [documentation](/software/contrib/dfam.md) | [script](/software/contrib/dfam.md) \]

A trigger sequencer designed to interact with the [Moog DFAM](https://www.moogmusic.com/products/dfam-drummer-another-mother).
Allows DFAM to play sequences of different lengths and adds a reset button & patch point.

Inspired by the [Sonoclast MAFD](https://sonoclast.com/products/mafd/).

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: trigger, dfam</i>

### Egressus Melodium \[ [documentation](/software/contrib/egressus_melodiam.md) | [script](/software/contrib/egressus_melodiam.py) \]

Clockable and free-running LFO and random CV pattern generator

<i>Author: [gamecat69](https://github.com/gamecat69)</i>
<br><i>Labels: clocked lfo, sequencer, CV, randomness</i>

### Envelope Generator \[ [documentation](/software/contrib/envelope_generator.md) | [script](/software/contrib/envelope_generator.py) \]

An attack release envelope with optional sustain and looping functionality.
Envelopes are triggered or gated by the digital input, and the envelope is output, along with a copy of the digital input and an inverted copy of the envelope.

<i>Author: [roryjamesallen](https://github.com/roryjamesallen)</i>
<br><i>Labels: Envelope Generator</i>

### Euclid \[ [documentation](/software/contrib/euclid.md) | [script](/software/contrib/euclid.py) \]

Euclidean rhythm generator. Each channel can generate an independent euclidean rhythm.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: sequencer, gates, triggers, euclidean</i>

### Gates and Triggers \[ [documentation](/software/contrib/gates_and_triggers.md) | [script](/software/contrib/gates_and_triggers.py) \]

Convert incoming triggers to gates or gates to triggers.  Buttons allow manually creating gates/triggers, knobs control
the duration of the output signals.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: gates, triggers</i>

### Gate Phaser \[ [documentation](/software/contrib/gate_phaser.md) | [script](/software/contrib/gate_phaser.py) \]

A script which attempts to answer the question "What would Steve Reich do if he had a EuroPi?"

<i>Author: [gamecat69](https://github.com/gamecat69)</i>
<br><i>Labels: sequencer, gates</i>

### Hamlet \[ [documentation](/software/contrib/hamlet.md) | [script](/software/contrib/hamlet.py) \]

A variation of the Consequencer script specifically geared towards driving voices

2pairs of gate and CV outputs are available to drive two voices, as well as 2 drum gate outputs.
As with the consequencer, the patterns can be smoothly morphed between while performing

<i>Author: [seanbechhofer](https://github.com/seanbechhofer)</i>
<br><i>Labels: sequencer, gates, triggers, drums, randomness</i>

### Harmonic LFOs \[ [documentation](/software/contrib/harmonic_lfos.md) | [script](/software/contrib/harmonic_lfos.py) \]

6 tempo-related LFOs with adjustable wave shape

Users can run up to 6 LFOs with one internal master clock, with wave shapes of either sine, saw, square, semi-random, or off.
The division of the master clock that each LFO runs at, as well as each of their wave shapes, can be adjusted during operation

<i>Author: [roryjamesallen](https://github.com/roryjamesallen)</i>
<br><i>Labels: LFO</i>

### HTTP Interface \[ [documentation](/software/contrib/http_control.md) | [script](/software/contrib/http_control.py) \]

Control the levels of CV1-6 using sliders in a web interface. Requires installation and configuration
of a Raspberry Pi Pico W or Pico 2 W.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: cv, http, wifi</i>

### Itty Bitty \[ [documentation](/software/contrib/itty_bitty.md) | [script](/software/contrib/itty_bitty.py) \]

Dual-channel 8-bit trigger+gate+cv sequencer based on the binary representation of an 8-bit number.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: sequencer, gate, trigger, cv</i>

### Kompari \[ [documentation](/software/contrib/kompari.md) | [script](/software/contrib/kompari.py) \]

Compares `AIN` to `K1` and `K2`, outputting 5V digital signals on `CV1`-`CV5`, and an analogue output signal based on
comparing all 3 sources.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: logic, gates, binary operators</i>

### Logic \[ [documentation](/software/contrib/logic.md) | [script](/software/contrib/logic.py) \]

Treats both inputs as digital on/off signals and outputs the results of binary AND, OR, XOR, NAND, NOR, and XNOR operations on outputs 1-6.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: logic, gates, binary operators</i>

### Lutra \[ [documentation](/software/contrib/lutra.md) | [script](/software/contrib/lutra.py) \]

Six syncable LFOs with variable wave shapes. The clock speed of each LFO is slightly different, with an adjustable base speed and CV-controllable spread.

Inspired by [Expert Sleepers' Otterley](https://expert-sleepers.co.uk/otterley.html) module.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: lfo</i>

### Master Clock \[ [documentation](/software/contrib/master_clock.md) | [script](/software/contrib/master_clock.md) \]

A master clock and clock divider.

<i>Author: [gamecat69](https://github.com/gamecat69)</i>
<br><i>Labels: clock, gates, triggers</i>

### Morse \[ [documentation](/software/contrib/morse.md) | [script](/software/contrib/morse.md) \]

A gate sequencer that uses Morse code to generate the on/off pattern.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: gates, sequencer</i>

### Noddy Holder \[ [documentation](/software/contrib/noddy_holder.md) | [script](/software/contrib/noddy_holder.py) \]

Two channels of sample/track and hold based on a single trigger and CV source

Users have a copy of the original trigger signal, a sample and hold and a track and hold of the analogue input, and the all above but with the gate inverted, available from the CV outputs

<i>Author: [seanbechhofer](https://github.com/seanbechhofer)</i>
<br><i>Labels: gates, sample&hold, track&hold</i>

### Ocean Surge \[ [documentation](/software/contrib/ocean_surge.md) | [script](/software/contrib/ocean_surge.py) \]

A clone of the Addac 508 "Swell Physics". Uses a trochoidal wave to simulate ocean surge, outputting control voltages and gates depending on the relative heights of 4 buoys floating on top of the wave.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: LFO, gate, sequencer, physics</i>

### OSC Interface \[ [documentation](/software/contrib/osc_control.md) | [script](/software/contrib/osc_control.py) \]

Interface program for sending & receiving Open Sound Control (OSC) packets over UDP. Compatible with TouchOSC and
other programs that support OSC over UDP.

Requires a Raspberry Pi Pico W or Pico 2 W with a properly-configured wifi connection to your other devices.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: osc, wifi</i>

### Pam's "EuroPi" Workout \[ [documentation](/software/contrib/pams.md) | [script](/software/contrib/pams.py) \]

A re-imaging of [ALM/Busy Circuit's Pamela's "NEW" Workout](https://busycircuits.com/alm017/). Turns the EuroPi into a clocked modulation
source with multiple wave shapes, optional quantization, euclidean rhythm outputs and external start/stop trigger input.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: clock, euclidean, gate, lfo, quantizer, random, trigger</i>

### Particle Physics \[ [documentation](/software/contrib/particle_physics.md) | [script](/software/contrib/particle_physics.py) \]

An irregular LFO based on a basic 1-dimensional physics simulation. Outputs triggers when a particle bounces under the effects of gravity. Outputs control signals
based on the particle's position and velocity.

While not technically random, the effects of changing the particle's initial conditions, gravity, and elasticity coefficient can create unpreditable rhythms.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: gate, lfo, sequencer, random, trigger</i>

### Pet Rock \[ [documentation](/software/contrib/pet_rock.md) | [script](/software/contrib/pet_rock.py) \]

A pseudo-random gate generator that uses the realtime clock to track the phase of the moon as a seed. Based on [Pet Rock by Jonah Senzel](https://petrock.site)

Requires installing and configuring a realtime clock module, connected to EuroPi's external I2C interface for best results.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: sequencer, gate, random, realtime clock</i>

### Piconacci \[ [documentation](/software/contrib/piconacci.md) | [script](/software/contrib/piconacci.py) \]

A clock divider whose divisions are based on the Fibonacci sequence.

<i>Author: [seanbechhofer](https://github.com/seanbechhofer)</i>
<br><i>Labels: triggers, sequencer</i>

### Poly Square \[ [documentation](/software/contrib/poly_square.md) | [script](/software/contrib/poly_square.py) \]

Six independent oscillators which output on CVs 1-6.

The base pitch is set by the analog input, which is interpreted as a V/oct input with 0V = C. Knob 1 allows for detuning of the 6 voices, and as the knob is turned clockwise, the spread between them increases. Button 2 toggles the maximum detune between a half step and a major 9th. Knob 2 sets the polyphony mode.

<i>Author: [t-schreibs](https://github.com/t-schreibs)</i>
<br><i>Labels: oscillator, poly</i>

### Polyrhythmic Sequencer \[ [script](/software/contrib/polyrhythmic_sequencer.py) \]

A sequencer that advances notes according to a polyrhythmic clock, inspired by the operation of the Moog Subharmonicon sequencer

Users can run two simultaneous polyrhythmic sequences clocked by the same external clock.
Quantised outputs are available, with the note for each step, and the polyrhythm it runs at, being easily changed to write the sequence

<i>Author: [awonak](https://github.com/awonak)</i>
<br><i>Labels: polyrhythms, sequencer, triggers</i>

### Probapoly \[ [documentation](/software/contrib/probapoly.md) | [script](/software/contrib/probapoly.py) \]

Creates interesting polyrhythmic gate patterns while also allowing probabilities to be set on gates.

Given values for and upper and lower rhythmic ratios, Probapoly will create a looping pattern as short as possible with no repetition of the pattern within the loop.

<i>Author: [gamecat69](https://github.com/gamecat69)</i>
<br><i>Labels: sequencer, performance, gates, polyrhythm, probability</i>

### Quantizer \[ [documentation](/software/contrib/quantizer.md) | [script](/software/contrib/quantizer.py) \]

Quantizes input analog signals to a customizable scale.  Additional signals output the same note shifted up or down to create harmonies across multiple oscillators.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: quantizer</i>

### Radio Scanner \[ [documentation](/software/contrib/radio_scanner.md) | [script](/software/contrib/radio_scanner.py) \]

A tool for exploring sounds and control voltage combinations by navigating a 2D plane

The two knobs allow users to scan in 2 separate axis, with the value of each knob available as a CV output.
There is also a CV output for the difference between the two knob positions, and then the lower row of CV outputs is the inverse of each jack above.
The outputs can also be rotated as inspired by the 4MS Rotating Clock Divider

<i>Author: [roryjamesallen](https://github.com/roryjamesallen)</i>
<br><i>Labels: n/a</i>

### Scope \[ [script](/software/contrib/scope.py) \]

An oscilloscope script to monitor the analogue and digital inputs

The current values of the analogue and digital inputs are displayed in an oscilloscope style on the OLED display, and copies of both signals, as well as an inverted gate signal, are available from the CV outputs

<i>Author: [mjaskula](https://github.com/mjaskula)</i>
<br><i>Labels: example, utility</i>

### Sequential Switch \[ [documentation](/software/contrib/sequential_switch.md) | [script](/software/contrib/sequential_switch.py) \]

A 2-6 output sequential switch.  The analogue input is mirrored to one of the outputs, with the specific output changed every time a trigger is received.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: random, sequential switch</i>

### Set Timer \[ [documentation](/software/contrib/set_timer.md) | [script](/software/contrib/set_timer.py) \]

A manual or CV-controlled stopwatch that displays elapsed & split time. Useful for timing your set or recording.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: timer, gate, trigger</i>

### Sigma \[ [documentation](/software/contrib/sigma.md) | [script](/software/contrib/sigma.py) \]

Random CV, optionally quantized, voltages based on controllable normal distributions. Inspired by Magnetic Freak's Gaussian module.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: random, quantizer</i>

### Slopes \[ [documentation](/software/contrib/slopes.md) | [script](/software/contrib/slopes.py) \]

CV analyzer that produces gates & CV outputs based on the slope of the incoming signal

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: gates, CV</i>

### Smooth Random Voltages \[ [script](/software/contrib/smooth_random_voltages.py) \]

Random CV with adjustable slew rate, inspired by: https://youtu.be/tupkx3q7Dyw.

3 random or analog input s&h voltages with changable slew smoothness. New voltages assigned upon each digital input trigger. Top row outputs move
towards target voltage according to slew rate set by knob 1. Bottom row outputs immediately change to new target voltage.

<i>Author: [awonak](https://github.com/awonak)</i>
<br><i>Labels: random, s&h</i>

### Strange Attractor \[ [documentation](/software/contrib/strange_attractor.md) | [script](/software/contrib/strange_attractor.py) \]

A source of chaotic modulation using systems of differential equations such as the Lorenz System

Users have the x, y, and z values of the output of each attractor model available as CV outputs, as well as 3 gate signals related to the relationships between these values

<i>Author: [seanbechhofer](https://github.com/seanbechhofer)</i>
<br><i>Labels: gates, triggers, randomness</i>

### Traffic \[ [documentation](/software/contrib/traffic.md) | [script](/software/contrib/traffic.py) \]

A re-imagining of [Jasmine and Olive Tree's Traffic](https://jasmineandolivetrees.com/products/traffic) module. Triggers are sent to both inputs
generating CV signals based on which trigger fired most recently and a pair of gains per channel.

<i>Author: [chrisib](http://github.com/chrisib)</i>
<br><i>Labels: sequencer, gate, triggers</i>

### Turing Machine \[ [documentation](/software/contrib/turing_machine.md) | [script](/software/contrib/turing_machine.py) \]

A script meant to recreate the [Music Thing Modular Turning Machine Random Sequencer](https://musicthing.co.uk/pages/turing.html)
as faithfully as possible on the EuroPi hardware.

<i>Author: [mjaskula](https://github.com/mjaskula)</i>
<br><i>Labels: sequencer, random, triggers</i>

### Volts \[ [documentation](/software/contrib/volts.md) | [script](/software/contrib/volts.py) \]

Generates static voltages on CV1-6. Useful for when you need a reliable, fixed voltage source as an input. Some useful applications include:
- transposing a sequencer
- shifting a bipolar LFO or VCO to be unipolar
- sending a fixed voltage to a VCA to amplify a signal to a fixed level
- calibrating other modules

<i>Author: [chrisib](http://github.com/chrisib)</i>
<br><i>Labels: cv, voltages, non-interactive</i>

---

<details>
<summary><h2>Proof of Concept Scripts</h2></summary>

These scripts are NOT included in the standard `menu.py`, but can be added if desired.

### Hello World \[ [script](/software/contrib/hello_world.py) \]

An example script for the menu system

This script can be copied and altered as a starting point for your own scripts that are to be menu compatible, and make use of the save state functionality

<i>Author: [mjaskula](https://github.com/mjaskula)</i>
<br><i>Labels: example</i>

### Custom Fonts \[ [script](/software/contrib/custom_font_demo.py) \]

An example demonstrating the use of custom fonts.

<i>Author: [François Georgy](https://github.com/francoisgeorgy)</i>
<br><i>Labels: example</i>

### Knob Playground \[ [script](/software/contrib/knob_playground.py) \]

An example showing the use of knob banks and lockable knobs.

<i>Author: [mjaskula](https://github.com/mjaskula)</i>
<br><i>Labels: example</i>

### Settings Menu Example \[ [script](/software/contrib/settings_menu_example.py) \]

A simple example showing how to use configuration points and the settings menu to create an application GUI.

<i>Author: [chrisib](https://github.com/chrisib)</i>
<br><i>Labels: example</i>

</details>

---

<details>
<summary><h2>Script Capability Reference</h2></summary>

The following tables classify all 54 packaged scripts by two properties: whether they need an
external signal on `din` to run, and whether they can drive a synth voice on their own. Derived
by reading each script's source; `menu.py` is excluded as it is the launcher rather than a script.

## Clock, gate & trigger requirements

### Requires a signal on `din` — no internal clock

Nothing free-runs in these scripts; each `din` edge is what advances the sequence or takes the
next sample.

| Script | Role of `din` |
|--------|---------------|
| `arp.py` | Trigger advances the arpeggio to the next note |
| `bernoulli_gates.py` | The trigger/clock routed by the coin toss |
| `binary_counter.py` | Each gate increments the 6-bit counter |
| `bit_garden.py` | Trigger/gate source that the outputs mirror |
| `clock_mod.py` | The clock being multiplied/divided |
| `cvecorder.py` | 50% duty-cycle gate; drives recording and the 32-step loop |
| `daily_random.py` | External clock; all other controls are unused |
| `dfam.py` | External clock, passed through `cv1` to the DFAM's ADV/CLOCK |
| `dscn2.py` \* | Each clock walks the binary tree one step |
| `euclid.py` \* | External clock advancing all six patterns |
| `hamlet.py` | Clock starts and advances the sequence |
| `itty_bitty.py` \* | Clock/gate/trigger advancing both sequences |
| `morse.py` | Clock/gate stepping through the Morse pattern |
| `piconacci.py` | The clock being divided by Fibonacci numbers |
| `polyrhythmic_sequencer.py` | Clock in; the script does not play without it |
| `probapoly.py` | 50% duty-cycle gate/clock driving the polyrhythm |
| `sigma.py` | Triggers sampling; its pulse width also sets output gate length |
| `smooth_random_voltages.py` | Trigger sets a new target voltage |
| `turing_machine.py` | Clock; the shift register only steps on a `din` edge |

\* Playable by hand as well as by clock. `euclid.py` and `dscn2.py` map `b1` as a manual clock for
all channels; `itty_bitty.py` gives each of its two sequencers its own button (`b1` and `b2`),
which call the same `advance()` method as the `din` handler.

### Requires an external gate or trigger, but not a periodic clock

| Script | Why |
|--------|-----|
| `gates_and_triggers.py` | Converts an input gate/trigger; `b1` is a manual equivalent |
| `logic.py` | `din` and `ain` are the two logic operands |
| `noddy_holder.py` | Needs a gate on `din` for sample/track-and-hold |
| `sequential_switch.py` | Needs a trigger to advance; `b1` shares the `on_trigger` handler |
| `traffic.py` | Triggers on `din` *and* `ain`; `b1`/`b2` are channel selectors, not manual triggers |

### Self-sufficient — no external clock, gate or trigger required

**Fully self-running (generate their own timing):** `bezier.py`, `bouncing_pixels.py`,
`conway.py`, `gate_phaser.py`, `harmonic_lfos.py`, `lutra.py`, `master_clock.py`,
`ocean_surge.py`, `pams.py`, `particle_physics.py`, `poly_square.py`, `strange_attractor.py`

**Self-running only in a non-default mode:**

| Script | How to free it |
|--------|----------------|
| `coin_toss.py` | `b1` toggles to internal clock |
| `consequencer.py` | Long-press `b1` (>3s) toggles to the internal clock; hold `b1` and turn `k1` for tempo |
| `egressus_melodiam.py` | Long-press `b2` for `unClockedMode` |
| `envelope_generator.py` | `LOOPING_MODE_LOOP` self-retriggers; the default is once |
| `pet_rock.py` | `k1`/`k2` run internal clocks; fully anticlockwise stops them |
| `quantizer.py` | `MODE_CONTINUOUS` ignores `din`; the default is triggered |

**No timing needed at all** (static, knob, CV or network driven): `http_control.py`,
`kompari.py`, `osc_control.py`, `radio_scanner.py`, `scope.py`, `set_timer.py`, `slopes.py`,
`volts.py`

**Examples/demos:** `custom_font_demo.py`, `hello_world.py`, `knob_playground.py`,
`settings_menu_example.py`

Note that `kompari.py`, `poly_square.py`, `quantizer.py` and `slopes.py` need no clock but are
inert without a CV signal on `ain`.

## Driving a synth voice

Scripts that place gates/triggers on some outputs and CV on others simultaneously, so that one
module can supply both the gate and the pitch/timbre CV for a voice.

### Purpose-built voice sequencers

| Script | Outputs | Needs external signal? |
|--------|---------|------------------------|
| `hamlet.py` | `out1`/`out2` triggers, `out3`/`out4` gates for tracks 1 & 2, `out5`/`out6` track CV — two voices | Yes |
| `polyrhythmic_sequencer.py` | `out1` pitch 1 + `out2` trigger 1; `out4` pitch 2 + `out5` trigger 2; `out3`/`out6` AND/XOR — two voices | Yes |
| `itty_bitty.py` | `cv1`-`cv3` trigger/gate/CV for sequence A, `cv4`-`cv6` for sequence B — two voices | No internal clock, but `b1`/`b2` step each sequencer by hand |
| `consequencer.py` | `out1`-`out3` gates, `out4`-`out6` stepped CV | No — internal clock selectable with a long press on `b1` |
| `turing_machine.py` | `cv1`-`cv5` pulses (bits + logical ANDs), `cv6` register voltage | Yes |
| `daily_random.py` | `cv1`-`cv3` gate sequences, `cv4`-`cv6` matching CV sequences | Yes |
| `pams.py` | Any of 6 channels as gate/trigger or quantized CV, with euclidean rhythms and per-channel clock division | No — internal 1-300 BPM clock |

### Gate + CV, where the CV is modulation rather than pitch

| Script | Outputs | Needs external signal? |
|--------|---------|------------------------|
| `sigma.py` | `cv1`-`cv3` gates, `cv4`-`cv6` Gaussian CV (optionally quantized) | Yes |
| `strange_attractor.py` | `out1`-`out3` attractor x/y/z CV, `out4`-`out6` triggers/gates | No |
| `ocean_surge.py` | `cv1`-`cv3` + `cv6` buoy-height CV, `cv4`/`cv5` comparison gates | No |
| `particle_physics.py` | `cv1`-`cv3` triggers/gates, `cv4`/`cv5` height and velocity CV | No |
| `conway.py` | `cv1`-`cv3` entropy/ratio CV, `cv4`-`cv6` gates | No |
| `traffic.py` | `cv1`-`cv5` channel and difference CV, `cv6` a 10ms gate per input trigger | Yes |

### Processors — gate + CV out, but they need a signal in

| Script | Outputs | Needs external signal? |
|--------|---------|------------------------|
| `quantizer.py` | `cv1` quantized pitch, `cv2`-`cv5` fixed-semitone harmonies, `cv6` note-change trigger | Continuous mode: CV on `ain` only. Triggered mode: also a trigger on `din` |
| `slopes.py` | `cv1`/`cv2`/`cv3` rising/falling/flat gates, `cv4`-`cv6` slope-magnitude CV | CV on `ain`; no clock |
| `noddy_holder.py` | `out1` gate copy, `out2`/`out3` S&H and T&H CV, `out4`-`out6` inverted-gate equivalents | Gate on `din`, CV on `ain` |
| `kompari.py` | `cv1`-`cv5` comparator gates plus an analogue output | CV on `ain`; no clock |

### Not usable alone

`arp.py` outputs quantized pitch on all six jacks but no gate. `egressus_melodiam.py` and
`cvecorder.py` are CV-only. `bernoulli_gates.py`, `binary_counter.py`, `bit_garden.py`,
`coin_toss.py`, `dscn2.py`, `euclid.py`, `gate_phaser.py`, `master_clock.py`, `morse.py`,
`pet_rock.py` and `probapoly.py` are gate/trigger-only. `poly_square.py` outputs audio directly
rather than gate and CV.

</details>
