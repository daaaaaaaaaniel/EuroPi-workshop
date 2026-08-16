# Copyright 2022 Allen Synthesis
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
from time import ticks_add, ticks_diff, ticks_ms
from random import randint, uniform
from europi_script import EuroPiScript
from experimental.knobs import KnobBank, LockableKnob
import configuration
import gc

"""
Consequencer
author: Nik Ansell (github.com/gamecat69)
date: 2022-02-05
labels: sequencer, triggers, drums, randomness

Consequencer is a gate and stepped CV sequencer inspired by Grids from Mutable Instruments and the randomness created by the Turing Machine.
Pattern changes and randomness are introduced as a consequence of both manual input and control voltages sent to the analogue input.
A large number of popular gate patterns are pre-loaded. Stepped CV sequences are automatically generated.

"""

"""
Version History
March-23    decreased maxRandomPatterns to 32 to avoid crashes on some systems
            pattern is now sum of ain and k2
            randomness is now sum of ain and k1
            added garbage collection to avoid memory allocation errors when creating new random sequences
            scroll pattern on display
            minor pattern updates and reshuffled the order

Jan-24      reduced number of calls to update screen to improve performance for incoming clocks < 7ms
            added grids patterns as an easter egg
            added methods to reduce hysteresis on ain - this reduces the number of ain reads too
            added methods to reduce hysteresis on k1 and k2 - this reduces the number of knob reads too
            added screen saver to improve performance
            changed the way the mode is displayed - replaced M1,M2,M3 with Mr,Mp,Mc for easier reading
            cleaned up some code comments
            added constants for easier code reading

Aug-26      added an internal clock so the script can run without an external clock on din
            b1 medium press now toggles output4isClock; b1 long press toggles the clock source
            b1 presses longer than 5s no longer fall through to the medium press action
            randomized hi-hats moved from a b1 gesture to the RANDOM_HH configuration option
            the internal clock indicator replaces the randomized hi-hat indicator on the display
            holding b1 and turning k1 sets the internal clock's tempo; the tempo is shown in
            place of the randomness while b1 is held, and turning k1 suppresses b1's own action
"""

# Operating modes for the internal state machine
MODE_RANDOM = 1
MODE_PATTERN = 2
MODE_CV_PATTERN = 3

# Change detection thresholds to trigger a value change
KNOB_CHANGE_TOLERANCE = 0.999
AIN_CHANGE_TOLERANCE = 1

# AIN Input Mode display chars
MODE_DISPLAY_CHARS = ["r", "p", "c"]

# Wake the screen upon detecting input at ain?
WAKE_SCREEN_ON_AIN_INPUT = False

# Button press duration thresholds in ms
LONG_PRESS_MS = 3000
MEDIUM_PRESS_MS = 300

# Patterns are 16 steps to the bar, so one step is a sixteenth note.
# Used to convert the configured BPM into a per-step interval.
STEPS_PER_BEAT = 4

# Range of the internal clock's tempo, in quarter notes per minute
MIN_BPM = 1
MAX_BPM = 300


class Consequencer(EuroPiScript):

    @classmethod
    def config_points(cls):
        return [
            # Randomize the hi-hat output on cv3. Was previously a b1 gesture.
            configuration.boolean(name="RANDOM_HH", default=False),
            # Starting tempo of the internal clock, in quarter notes per minute.
            # Can be adjusted at runtime by holding b1 and turning k1.
            configuration.integer(
                name="INTERNAL_BPM", minimum=MIN_BPM, maximum=MAX_BPM, default=120
            ),
        ]

    def __init__(self):
        super().__init__()

        self.loadState()

        self.initPatterns()

        # Initialize variables
        self.step = 0
        self.trigger_duration_ms = 50
        # Internal clock scheduling. next_step_at_ms is when the next step is due,
        # gate_off_at_ms is when the current step's gates should fall (None = no gates high)
        self.next_step_at_ms = ticks_ms()
        self.gate_off_at_ms = None
        self.calculateClockTiming()

        # While b1 is held, k1 adjusts the internal clock's tempo instead of the randomness.
        # b1_knob_moved records whether k1 was actually turned during the hold; if it was, the
        # button's own action is suppressed on release so that setting the tempo doesn't also
        # toggle a setting.
        self.b1_held = False
        self.b1_knob_moved = False
        self.b1_k1_at_press = 0

        # k1 controls randomness normally and the tempo while b1 is held. Banking the two keeps
        # the randomness value from jumping to wherever the knob was left after setting a tempo;
        # it stays put until k1 is swept back through it.
        self.k1_bank = (
            KnobBank.builder(k1)
            .with_unlocked_knob("randomness")
            .with_locked_knob(
                "bpm",
                initial_percentage_value=(self.internal_bpm - MIN_BPM) / (MAX_BPM - MIN_BPM),
            )
            .build()
        )
        self.clock_step = 0
        self.pattern = 0
        self.pattern_prev = 0
        self.minAnalogInputVoltage = 0.5
        self.randomness = 0
        self.randomness_prev = 0
        self.CvPattern = 0
        self.CvPattern_prev = 0
        self.reset_timeout = 1000
        self.maxRandomPatterns = 32  # This prevents a memory allocation error
        self.maxCvVoltage = clamp(europi_config.MAX_OUTPUT_VOLTAGE, 0, 9)  # The maximum is 9 to maintain single digits in the voltage list
        self.gateVoltage = europi_config.GATE_VOLTAGE
        self.gateVoltages = [0, self.gateVoltage]

        self.ainVal = 0
        self.ainValTemp = 0
        self.k1Val = 0
        self.k1ValTemp = 0
        self.k2Val = 0
        self.k2ValTemp = 0

        self.lastInteractionTimeMs = ticks_ms()
        self.screenOff = False
        self.screenOffTimeoutMs = 10 * 1000

        # State flag to determine if UI state has changed and display should update.
        self._updateUI = True

        # Calculate the longest pattern length to be used when generating random sequences
        self.maxStepLength = len(max(self.BD, key=len))

        # Generate random CV for cv4-6
        self.random4 = []
        self.random5 = []
        self.random6 = []
        self.generateNewRandomCVPattern()

        # Triggered when button 2 is released.
        @b2.handler_falling
        def b2Pressed():
            # grids patterns easter egg
            if (
                ticks_diff(ticks_ms(), b2.last_pressed()) > 3000
                and ticks_diff(ticks_ms(), b2.last_pressed()) < 5000
            ):
                self.gridsMode = not self.gridsMode
                self.saveState()
                self.initPatterns()

            elif ticks_diff(ticks_ms(), b2.last_pressed()) > 300:
                if self.analogInputMode < MODE_CV_PATTERN:
                    self.analogInputMode += 1
                else:
                    self.analogInputMode = MODE_RANDOM
                self.saveState()
            else:
                if self.analogInputMode == MODE_CV_PATTERN:  # Allow changed by CV only in mode 3
                    return

                if self.CvPattern < len(self.random4) - 1:  # change to next CV pattern
                    self.CvPattern += 1
                else:
                    if (
                        len(self.random4) < self.maxRandomPatterns
                    ):  # We need to try and generate a new CV value
                        if self.generateNewRandomCVPattern():
                            self.CvPattern += 1
            self._updateUI = True
            self.screenOff = False
            self.lastInteractionTimeMs = ticks_ms()

        # Triggered when button 1 is pressed. Hands k1 over to the tempo control for the
        # duration of the hold.
        @b1.handler
        def b1Held():
            self.b1_held = True
            self.b1_knob_moved = False
            # Sample the physical knob rather than the banked one; the banked tempo knob stays
            # locked until it is swept back to the current tempo, so it cannot tell us whether
            # the user actually touched k1
            self.b1_k1_at_press = k1.read_position()
            self.k1_bank.set_current("bpm")
            self._updateUI = True
            self.screenOff = False
            self.lastInteractionTimeMs = ticks_ms()

        # Triggered when button 1 is released
        @b1.handler_falling
        def b1Pressed():
            self.k1_bank.set_current("randomness")
            self.b1_held = False

            if self.b1_knob_moved:
                # k1 was used to set the tempo during this hold, so don't also fire the
                # button's own action
                self.saveState()
            elif ticks_diff(ticks_ms(), b1.last_pressed()) > LONG_PRESS_MS:
                # Toggle between the internal clock and an external clock on din.
                # Drop any gates that are currently high so switching mid-step
                # cannot strand an output.
                self.internal_clock = not self.internal_clock
                self.gatesOff()
                self.gate_off_at_ms = None
                self.next_step_at_ms = ticks_ms()
                self.saveState()
            elif ticks_diff(ticks_ms(), b1.last_pressed()) > MEDIUM_PRESS_MS:
                self.output4isClock = not self.output4isClock
                self.saveState()
            else:
                # Play previous CV Pattern, unless we are at the first pattern
                if self.CvPattern != 0:
                    self.CvPattern -= 1
            self._updateUI = True
            self.screenOff = False
            self.lastInteractionTimeMs = ticks_ms()

        # Triggered on each clock into digital input. Output triggers.
        @din.handler
        def clockTrigger():
            # Ignore the external clock while the internal clock is driving the sequence
            if not self.internal_clock:
                self.advanceStep()

        @din.handler_falling
        def clockTriggerEnd():
            if not self.internal_clock:
                self.gatesOff()

    def calculateClockTiming(self):
        """Recalculate the internal clock's step interval and gate length.

        The gate is clamped to half a step so that gates cannot outlast their own
        step at high tempos.
        """
        self.step_interval_ms = int(60000 / (self.internal_bpm * STEPS_PER_BEAT))
        self.gate_ms = min(self.trigger_duration_ms, self.step_interval_ms // 2)

    def advanceStep(self):
        """Output the current step and advance the sequence by one step"""

        # function timing code. Leave in and activate as needed
        # t = time.ticks_us()

        self.step_length = len(self.BD[self.pattern])

        # A pattern was selected which is shorter than the current step. Set to zero to avoid an error
        if self.step >= self.step_length:
            self.step = 0
        cv5.voltage(self.random5[self.CvPattern][self.step])
        cv6.voltage(self.random6[self.CvPattern][self.step])

        # How much randomness to add to cv1-3
        # As the randomness value gets higher, the chance of a randomly selected int being lower gets higher
        # The output will only trigger if the randint() is <= than the probability of the step in BdProb, SnProb and HhProb respectively
        # Random number 0-99
        randomNumber0_99 = randint(0, 99)
        # Random number 0-9
        randomNumber0_9 = randomNumber0_99 // 10
        if randomNumber0_99 < self.randomness:
            if randomNumber0_9 <= int(self.BdProb[self.pattern][self.step]):
                cv1.voltage(self.gateVoltages[randint(0, 1)])
            if randomNumber0_9 <= int(self.SnProb[self.pattern][self.step]):
                cv2.voltage(self.gateVoltages[randint(0, 1)])
            if randomNumber0_9 <= int(self.HhProb[self.pattern][self.step]):
                cv3.voltage(self.gateVoltages[randint(0, 1)])
        else:
            if randomNumber0_9 <= int(self.BdProb[self.pattern][self.step]):
                cv1.voltage(self.gateVoltages[int(self.BD[self.pattern][self.step])])
            if randomNumber0_9 <= int(self.SnProb[self.pattern][self.step]):
                cv2.voltage(self.gateVoltages[int(self.SN[self.pattern][self.step])])

            # If randomize HH is ON:
            if self.config.RANDOM_HH:
                cv3.value(randint(0, 1))
            else:
                if randomNumber0_9 <= int(self.HhProb[self.pattern][self.step]):
                    cv3.voltage(self.gateVoltages[int(self.HH[self.pattern][self.step])])

        # Set cv4-6 voltage outputs based on previously generated random pattern
        if self.output4isClock:
            cv4.voltage(self.gateVoltage)
        else:
            cv4.voltage(self.random4[self.CvPattern][self.step])

        # Incremenent the clock step
        self.clock_step += 1
        self.step += 1

        # Update the UI
        if not self.screenOff:
            self._updateUI = True

        # function timing code. Leave in and activate as needed
        # delta = time.ticks_diff(time.ticks_us(), t)
        # print('Function {} Time = {:6.3f}ms'.format('advanceStep', delta/1000))

    def gatesOff(self):
        """Drop the gate outputs at the end of a step"""
        cv1.off()
        cv2.off()
        cv3.off()
        if self.output4isClock:
            cv4.off()

    def initPatterns(self):

        # Initialize sequencer pattern arrays
        p = pattern()

        if self.gridsMode:

            self.BD = p.BDGrids
            self.SN = p.SNGrids
            self.HH = p.HHGrids

            # Initialize sequencer pattern probabiltiies
            self.BdProb = p.BdProbGrids
            self.SnProb = p.SnProbGrids
            self.HhProb = p.HhProbGrids

        else:

            self.BD = p.BD
            self.SN = p.SN
            self.HH = p.HH

            # Initialize sequencer pattern probabiltiies
            self.BdProb = p.BdProb
            self.SnProb = p.SnProb
            self.HhProb = p.HhProb

        # Load and populate probability patterns
        # If the probability string len is < pattern len, automatically fill out with the last digit:
        # - 9   becomes 999999999
        # - 95  becomes 955555555
        # - 952 becomes 952222222
        for pi in range(len(self.BD)):
            if len(self.BdProb[pi]) < len(self.BD[pi]):
                self.BdProb[pi] = self.BdProb[pi] + (
                    self.BdProb[pi][-1] * (len(self.BD[pi]) - len(self.BdProb[pi]))
                )
        for pi in range(len(self.SN)):
            if len(self.SnProb[pi]) < len(self.SN[pi]):
                self.SnProb[pi] = self.SnProb[pi] + (
                    self.SnProb[pi][-1] * (len(self.SN[pi]) - len(self.SnProb[pi]))
                )
        for pi in range(len(self.HH)):
            if len(self.HhProb[pi]) < len(self.HH[pi]):
                self.HhProb[pi] = self.HhProb[pi] + (
                    self.HhProb[pi][-1] * (len(self.HH[pi]) - len(self.HhProb[pi]))
                )

    """ Save working vars to a save state file"""

    def saveState(self):
        self.state = {
            "analogInputMode": self.analogInputMode,
            "output4isClock": self.output4isClock,
            "gridsMode": self.gridsMode,
            "internal_clock": self.internal_clock,
            "internal_bpm": self.internal_bpm,
        }
        self.save_state_json(self.state)

    """ Load a previously saved state, or initialize working vars, then save"""

    def loadState(self):
        self.state = self.load_state_json()
        self.analogInputMode = self.state.get("analogInputMode", 1)
        self.output4isClock = self.state.get("output4isClock", False)
        self.gridsMode = self.state.get("gridsMode", False)
        # Default to the external clock so existing users see no change in behaviour
        self.internal_clock = self.state.get("internal_clock", False)
        # INTERNAL_BPM provides the starting tempo; holding b1 and turning k1 overrides it.
        # Clamp in case the saved state predates a change to the supported range.
        self.internal_bpm = clamp(
            self.state.get("internal_bpm", self.config.INTERNAL_BPM), MIN_BPM, MAX_BPM
        )
        self.saveState()

    def generateNewRandomCVPattern(self):
        try:
            gc.collect()
            self.random4.append(
                self.generateRandomPattern(self.maxStepLength, 0, self.maxCvVoltage)
            )
            self.random5.append(
                self.generateRandomPattern(self.maxStepLength, 0, self.maxCvVoltage)
            )
            self.random6.append(
                self.generateRandomPattern(self.maxStepLength, 0, self.maxCvVoltage)
            )
            return True
        except Exception:
            return False

    def getPattern(self):
        # If mode 2 and there is CV on the analogue input use it, if not use the knob position
        if self.analogInputMode == MODE_PATTERN and self.ainVal > self.minAnalogInputVoltage:
            self.pattern = min(
                int((len(self.BD) / 100) * self.ainVal) + self.k2Val, len(self.BD) - 1
            )
        else:
            self.pattern = self.k2Val

        self.step_length = len(self.BD[self.pattern])

        if self.pattern_prev != self.pattern:
            self.pattern_prev = self.pattern
            if not self.screenOff:
                self._updateUI = True

    def getCvPattern(self):
        # If analogue input mode 3, get the CV pattern from CV input
        if self.analogInputMode == MODE_CV_PATTERN and self.ainVal > self.minAnalogInputVoltage:
            # Convert percentage value to a representative index of the pattern array
            self.CvPattern = int((len(self.random4) / 100) * self.ainVal)

        if self.CvPattern_prev != self.CvPattern:
            self.CvPattern_prev = self.CvPattern

            if not self.screenOff:
                self._updateUI = True

    def generateRandomPattern(self, length, min, max):
        self.t = []
        for i in range(0, length):
            self.t.append(uniform(0, 9))
        return self.t

    def getRandomness(self):
        # If mode 1 and there is CV on the analogue input use it, if not use the knob position
        if self.analogInputMode == MODE_RANDOM and self.ainVal > self.minAnalogInputVoltage:
            self.randomness = min(self.ainVal + self.k1Val, 99)
        else:
            self.randomness = self.k1Val

        if self.randomness_prev != self.randomness:
            self.randomness_prev = self.randomness

            if not self.screenOff:
                self._updateUI = True

    def getAinVal(self):
        # Read ain val and update if > threshold
        self.ainValTemp = 100 * ain.percent()
        if abs(self.ainValTemp - self.ainVal) > AIN_CHANGE_TOLERANCE:
            self.ainVal = self.ainValTemp


    def getKnobVals(self):
        if self.b1_held:
            # b1 is held, so k1 is setting the internal clock's tempo. Watch the physical knob
            # for movement so that the button's own action can be suppressed on release
            if abs(k1.read_position() - self.b1_k1_at_press) > KNOB_CHANGE_TOLERANCE:
                self.b1_knob_moved = True

            # The tempo knob has to be read on every pass for it to unlock, but its value is
            # only taken once it has. Until then it reports the position it was locked at,
            # which does not survive the round trip through the knob's resolution exactly and
            # would otherwise nudge the tempo simply by holding b1
            bpm_knob = self.k1_bank["bpm"]
            bpm = bpm_knob.read_position(steps=MAX_BPM - MIN_BPM + 1) + MIN_BPM
            if bpm_knob.state == LockableKnob.STATE_UNLOCKED and bpm != self.internal_bpm:
                self.internal_bpm = bpm
                self.calculateClockTiming()
                self._updateUI = True

            self.screenOff = False
            self.lastInteractionTimeMs = ticks_ms()
        else:
            # Read knob vals and update if > threshold
            self.k1ValTemp = self.k1_bank["randomness"].read_position()
            if abs(self.k1ValTemp - self.k1Val) > KNOB_CHANGE_TOLERANCE:
                self.k1Val = self.k1ValTemp
                self.screenOff = False
                self.lastInteractionTimeMs = ticks_ms()

        self.k2ValTemp = k2.read_position(len(self.BD))
        if abs(self.k2ValTemp - self.k2Val) > KNOB_CHANGE_TOLERANCE:
            self.k2Val = self.k2ValTemp
            self.screenOff = False
            self.lastInteractionTimeMs = ticks_ms()

    def main(self):
        while True:
            self.getAinVal()
            self.getKnobVals()
            self.getPattern()
            self.getRandomness()
            self.getCvPattern()

            # Drive the sequence from the internal clock, if selected
            if self.internal_clock:
                now = ticks_ms()
                if ticks_diff(now, self.next_step_at_ms) >= 0:
                    self.next_step_at_ms = ticks_add(now, self.step_interval_ms)
                    self.gate_off_at_ms = ticks_add(now, self.gate_ms)
                    self.advanceStep()
                elif self.gate_off_at_ms is not None and ticks_diff(now, self.gate_off_at_ms) >= 0:
                    self.gate_off_at_ms = None
                    self.gatesOff()

            # Update screen if updateUI flag has been set
            if self._updateUI:
                self.updateScreen()
                self._updateUI = False
            # If I have been running, then stopped for longer than reset_timeout, reset the steps and clock_step to 0
            # Only applies to the external clock; din.last_triggered() never advances when
            # the internal clock is running, which would otherwise reset the sequence every pass
            if (
                not self.internal_clock
                and self.clock_step != 0
                and ticks_diff(ticks_ms(), din.last_triggered()) > self.reset_timeout
            ):
                self.step = 0
                self.clock_step = 0

            # Has the module been left along for a while, turn off the screen
            if (
                not self.screenOff
                and ticks_diff(ticks_ms(), self.lastInteractionTimeMs) > self.screenOffTimeoutMs
            ):
                self.drawBlankScreen()
                self.screenOff = True

    def visualizePattern(self, pattern, prob):
        output = ""
        for s in range(len(pattern)):
            if pattern[s] == "1":
                char = "^" if prob[s] == "9" else "-"
                output = output + char
            else:
                output = output + " "
        return output

    def drawBlankScreen(self):
        oled.fill(0)
        oled.show()

    def updateScreen(self):
        # oled.clear() - dont use this, it causes the screen to flicker!
        oled.fill(0)

        # Show selected pattern visually

        # Calculate the length of the current pattern
        current_pattern_length = len(self.BD[self.pattern])

        # Calculate the width of one full pattern in pixels
        lpos_offset = current_pattern_length * CHAR_WIDTH

        # Calculate the x position of the first pattern to be drawn
        normal_lpos = lpos = 8 - (self.step * 8)

        # Calculate the number of patterns required to fill the OLED width
        number_of_offset_patterns = 2 * max(int(OLED_WIDTH / lpos_offset), 1)

        # Draw as many offset patterns as required to fill the OLED
        for pattern_offset in range(number_of_offset_patterns):
            # Draw the current pattern
            oled.text(
                self.visualizePattern(self.BD[self.pattern], self.BdProb[self.pattern]),
                normal_lpos,
                0,
                1,
            )
            oled.text(
                self.visualizePattern(self.SN[self.pattern], self.SnProb[self.pattern]),
                normal_lpos,
                10,
                1,
            )
            oled.text(
                self.visualizePattern(self.HH[self.pattern], self.HhProb[self.pattern]),
                normal_lpos,
                20,
                1,
            )
            normal_lpos += lpos_offset

        # If the internal clock is driving the sequence, show a rectangle
        if self.internal_clock:
            oled.fill_rect(0, 29, 10, 3, 1)

        # Show self.output4isClock indicator
        if self.output4isClock:
            oled.rect(12, 29, 10, 3, 1)

        if self.b1_held:
            # While b1 is held k1 sets the tempo, so show that in place of the randomness.
            # "T300" is one character wider than "R99" and would collide with the CV pattern,
            # which isn't relevant while setting a tempo, so that is hidden for the duration
            oled.text("T" + str(self.internal_bpm), 26, 25, 1)
        else:
            # Show randomness
            oled.text("R" + str(int(self.randomness)), 26, 25, 1)

            # Show CV pattern
            oled.text("C" + str(self.CvPattern), 56, 25, 1)

        # Show the analogInputMode
        oled.text("M" + str(MODE_DISPLAY_CHARS[self.analogInputMode - 1]), 85, 25, 1)

        # Show the pattern number
        if self.gridsMode:
            oled.text(".", 102, 25, 1)

        oled.text(str(self.pattern), 110, 25, 1)

        oled.show()


class pattern:

    # Initialize pattern lists
    BD = []
    SN = []
    HH = []

    BDGrids = []
    SNGrids = []
    HHGrids = []

    # Initialize pattern probabilities

    BdProb = []
    SnProb = []
    HhProb = []

    BdProbGrids = []
    SnProbGrids = []
    HhProbGrids = []

    # 11 interesting patterns
    BD.append("1000100010001000")
    SN.append("0000000000000000")
    HH.append("0000000000000000")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000000000000000")
    HH.append("0010010010010010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000000000")
    HH.append("0010010010010010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000001000")
    HH.append("0010010010010010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000000000")
    HH.append("0000000000000000")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000001000")
    HH.append("0000000000000000")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000001000")
    HH.append("0000100010001001")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000001000")
    HH.append("1010101010101010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000000000000000")
    HH.append("1111111111111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000001000")
    HH.append("1111111111111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000100010001000")
    SN.append("0000100000000000")
    HH.append("0001001000000000")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    # 10 commonly found patterns
    # Source: https://docs.google.com/spreadsheets/d/19_3BxUMy3uy1Gb0V8Wc-TcG7q16Amfn6e8QVw4-HuD0/edit#gid=0
    BD.append("1000000010000000")
    SN.append("0000100000001000")
    HH.append("1010101010101010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1010001000100100")
    SN.append("0000100101011001")
    HH.append("0000000100000100")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000000110000010")
    SN.append("0000100000001000")
    HH.append("1010101110001010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1100000100110000")
    SN.append("0000100000001000")
    HH.append("1010101010101010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000000110100000")
    SN.append("0000100000001000")
    HH.append("0010101010101010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1010000000110001")
    SN.append("0000100000001000")
    HH.append("1010101010101010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000000110100001")
    SN.append("0000100000001000")
    HH.append("0000100010101011")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1001001010000000")
    SN.append("0000100000001000")
    HH.append("0000100000001000")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1010001001100000")
    SN.append("0000100000001000")
    HH.append("1010101010001010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1010000101110001")
    SN.append("0000100000001000")
    HH.append("1010101010001010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    # 5 interesting patterns?
    BD.append("1000100010001000")
    SN.append("0000101001001000")
    HH.append("1010101010101010")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1100000001010000")
    SN.append("0000101000001000")
    HH.append("0101010101010101")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1100000001010000")
    SN.append("0000101000001000")
    HH.append("1111111111111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1001001001000100")
    SN.append("0001000000010000")
    HH.append("0101110010011110")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1001001001000100")
    SN.append("0001000000010000")
    HH.append("1111111111111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    # 5 Mixed probability patterns
    BD.append("10111111111100001011000000110000")
    SN.append("10001000100010001010000001001000")
    HH.append("10101010101010101010101010101010")
    BdProb.append("99992111129999999999999999969999")
    SnProb.append("95")
    HhProb.append("92939495969792939495969792939492")

    BD.append("10111111111100001011000000110000")
    SN.append("10001000100010001010000001001000")
    HH.append("11111111111111111111111111111111")
    BdProb.append("99992222229999999999999999999999")
    SnProb.append("95")
    HhProb.append("44449999555599996666999922229999")

    BD.append("1000100010001000")
    SN.append("0000101001001000")
    HH.append("0101010101010101")
    BdProb.append("999995")
    SnProb.append("5")
    HhProb.append("99995")

    BD.append("1000110010001100")
    SN.append("0000101001001000")
    HH.append("1111111111111111")
    BdProb.append("9999939999999299")
    SnProb.append("9")
    HhProb.append("9293949592939495")

    BD.append("1000100010001000")
    SN.append("0000101000001000")
    HH.append("1111111111111111")
    BdProb.append("9")
    SnProb.append("9999995999999999")
    HhProb.append("9293949592939495")

    # 5 African Patterns
    BD.append("10110000001100001011000000110000")
    SN.append("10001000100010001010100001001010")
    HH.append("00001011000010110000101100001011")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10101010101010101010101010101010")
    SN.append("00001000000010000000100000001001")
    HH.append("10100010101000101010001010100000")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("11000000101000001100000010100000")
    SN.append("00001000000010000000100000001010")
    HH.append("10111001101110011011100110111001")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10001000100010001000100010001010")
    SN.append("00100100101100000010010010110010")
    HH.append("10101010101010101010101010101011")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10010100100101001001010010010100")
    SN.append("00100010001000100010001000100010")
    HH.append("01010101010101010101010101010101")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    # 13 patterns with < 16 steps - can sound disjointed when using CV to select the pattern!

    BD.append("10010000010010")
    SN.append("00010010000010")
    HH.append("11100110111011")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1001000001001")
    SN.append("0001001000001")
    HH.append("1110011011101")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("100100000100")
    SN.append("000100100000")
    HH.append("111001101110")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10010000010")
    SN.append("00010010000")
    HH.append("11100110111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10010000010")
    SN.append("00010010000")
    HH.append("11111010011")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1001000010")
    SN.append("0001000000")
    HH.append("1111101101")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("100100010")
    SN.append("000100000")
    HH.append("111110111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10010010")
    SN.append("00010000")
    HH.append("11111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1001001")
    SN.append("0001000")
    HH.append("1111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("100100")
    SN.append("000100")
    HH.append("111111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("10000")
    SN.append("00001")
    HH.append("11110")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    BD.append("1000")
    SN.append("0000")
    HH.append("1111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9595")

    BD.append("100")
    SN.append("000")
    HH.append("111")
    BdProb.append("9")
    SnProb.append("9")
    HhProb.append("9")

    # Grids patterns
    # Node: 0
    # Threshold: 180
    BDGrids.append("10000000000010000000100000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000010000010000000100000000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000000010000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000000010000010001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010000000100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000101010001000100010001000")
    HhProbGrids.append("9")

    # Node: 1
    # Threshold: 180
    BDGrids.append("10000000100000001000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000100000001000000010001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00100000100000000000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00100000100010000010000010000000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010000000100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10101000101010001000100010001000")
    HhProbGrids.append("9")

    # Node: 2
    # Threshold: 180
    BDGrids.append("10000000000000100000100000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000000100010100000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000101000000000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000101000000000000010000010")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10000000000000001000100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000000000001010101000001000")
    HhProbGrids.append("9")

    # Node: 3
    # Threshold: 180
    BDGrids.append("10100000000000001000100000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10100000001000001000100000100000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000101000000000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00001000101000000000000010001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10101010000000001000000000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10101010100000001000000010001000")
    HhProbGrids.append("9")

    # Node: 4
    # Threshold: 180
    BDGrids.append("10000000000010001000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000010001000100000000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000000000000010101000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000000000100010101000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010000000100000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("00001000100010000000100010001000")
    HhProbGrids.append("9")

    # Node: 5
    # Threshold: 180
    BDGrids.append("10000000000000001010000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000000001010001000100000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000010100000000000000010000010")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("10001010100000000000000010000010")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010000000100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000000010001000100000001000")
    HhProbGrids.append("9")

    # Node: 6
    # Threshold: 180
    BDGrids.append("10001000000000000000000000001000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10001000000000000000100000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00100000100000000010000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00100000100000100010000010100000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10101010100000000000000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10101010100010001000000010000000")
    HhProbGrids.append("9")

    # Node: 7
    # Threshold: 180
    BDGrids.append("10000000000010001000000000001000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000010001000100000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100010000000000010001000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100010000000100010001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10001000100000001000100010000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000100010001000100010000000")
    HhProbGrids.append("9")

    # Node: 8
    # Threshold: 180
    BDGrids.append("10001000000010001000100000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10001000000010001000100000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000000000100010001000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("10000000100000000000100010001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10000000000000000000000010101010")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10000000000000001000000010101010")
    HhProbGrids.append("9")

    # Node: 9
    # Threshold: 180
    BDGrids.append("10000000000010000000100000100000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000010000010000000100000101000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000100000100010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000100000100010000010")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001010000010001000100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("00001010100010001000101010001000")
    HhProbGrids.append("9")

    # Node: 10
    # Threshold: 180
    BDGrids.append("00000000000010000010000000001000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000010000010000000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000001010001000000000000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00001000101010001000000000000000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10000000100000001000000010001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000100000001000000010001000")
    HhProbGrids.append("9")

    # Node: 11
    # Threshold: 180
    BDGrids.append("10000000000000001000100000100000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000000001000100000100010")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100100100000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100100100000000010001100")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010001000100010001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000100010001000100010001000")
    HhProbGrids.append("9")

    # Node: 12
    # Threshold: 180
    BDGrids.append("10001010000000000000101000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10001010000000000000101000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000100000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000100010000010000010")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10001000100010001000000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000100010001000100010001010")
    HhProbGrids.append("9")

    # Node: 13
    # Threshold: 180
    BDGrids.append("10000000100000101000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000100000101000000010000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000000000000010100000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000000000000010101000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10001000100010001000100000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10101010100010101000100010001000")
    HhProbGrids.append("9")

    # Node: 14
    # Threshold: 180
    BDGrids.append("10000000000000001000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000000001000100000000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100010000000000000001010")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100010000000000010001010")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10000000000000001000000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000000000001000100000000000")
    HhProbGrids.append("9")

    # Node: 15
    # Threshold: 180
    BDGrids.append("10000000000010001000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000010001000000000001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100010000000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100010000000000010001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10001000100000000000000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000100000001000100000000000")
    HhProbGrids.append("9")

    # Node: 16
    # Threshold: 180
    BDGrids.append("10000000000000001000000010000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000000000001000000010001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00001000000010000000100000000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00001000000010000000100000001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00000000000000001000100010000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10000000000000001000100010001000")
    HhProbGrids.append("9")

    # Node: 17
    # Threshold: 180
    BDGrids.append("10000000100000001000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000100000001000000010000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000000000001000001000001000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000101000001000001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00000000000000000010000010001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("00001000000010000010000010001000")
    HhProbGrids.append("9")

    # Node: 18
    # Threshold: 180
    BDGrids.append("10000000100000001000000010000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000100000001000000010101010")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000000000000000001000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100000000000000000001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10001000000000100010000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10001000000000100010001000000000")
    HhProbGrids.append("9")

    # Node: 19
    # Threshold: 180
    BDGrids.append("10000010100000000000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000010100000101000000000000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000000010100000000000001010")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000000010100000100000001010")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10000010000000000000000010000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10000010000010000000100010000000")
    HhProbGrids.append("9")

    # Node: 20
    # Threshold: 180
    BDGrids.append("10000000100000001000100000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000100000001000100010001000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100000100010000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000101000100010000010000000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00000000000010000000100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("00001000000010000000100000001000")
    HhProbGrids.append("9")

    # Node: 21
    # Threshold: 180
    BDGrids.append("10001000000000001000000010000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10001000100000001000000010000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000100010000000000000000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000100010000000000000100000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010000010100000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("00001000000010001010100000001000")
    HhProbGrids.append("9")

    # Node: 22
    # Threshold: 180
    BDGrids.append("10000000100000100000000010000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000000100000101000000010000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("10000000100000100000000000000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("10000000100000100010000010000000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("00001000000010000000000000001000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("00001000000010000010001000001000")
    HhProbGrids.append("9")

    # Node: 23
    # Threshold: 180
    BDGrids.append("10001000101000000000000000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10001000101000001010001010000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("00000000000010000000001000001000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("00000000000010000000001100001000")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10101111000000001010000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10101111000000001010111110000000")
    HhProbGrids.append("9")

    # Node: 24
    # Threshold: 180
    BDGrids.append("00000100100000000000010000000000")
    BdProbGrids.append("9")
    # Threshold: 127
    BDGrids.append("10000100100000001000010000000000")
    BdProbGrids.append("9")
    # Threshold: 180
    SNGrids.append("10000000000001000000000010000000")
    SnProbGrids.append("9")
    # Threshold: 127
    SNGrids.append("10000000000001001000010010000100")
    SnProbGrids.append("9")
    # Threshold: 180
    HHGrids.append("10000100000001000000000000000000")
    HhProbGrids.append("9")
    # Threshold: 127
    HHGrids.append("10000100100001000000000000000000")
    HhProbGrids.append("9")


if __name__ == "__main__":
    # Reset module display state.
    turn_off_all_cvs()
    dm = Consequencer()
    dm.main()
