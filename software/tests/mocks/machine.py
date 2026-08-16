# Copyright 2024 Allen Synthesis
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
class ADC:
    def __init__(self, *args):
        pass

    def read_u16(self, *args):
        return 0


class I2C:
    def __init__(self, channel, sda, scl, freq=400000, timeout=50000, *args):
        pass

    def scan(self):
        return []


class Pin:
    IN = "in"

    def __init__(self, id, *args):
        pass

    def irq(self, handler=None, trigger=None):
        pass

    def value(self, *args):
        pass


class PWM:
    def __init__(self, *args):
        pass

    def freq(self, f):
        pass

    def duty_u16(self, f):
        pass


class Timer:
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, *, mode=1, freq=-1, period=-1, callback=None):
        pass

    def init(self, *, mode=1, freq=-1, period=-1, callback=None):
        pass

    def deinit(self):
        pass


def freq(f=None):
    if f is None:
        return 150_000_000
    return f


class mem:
    """
    Fakes underlying machine registers.

    Shouldn't be used directly, but any registers (e.g. mem32) can be instantiated with this
    """

    def __getitem__(self, _):
        return 0x00


mem32 = mem()


class _BuiltinUSBDriver:
    """Stands in for one of machine.USBDevice's BUILTIN_ descriptors.

    usb/device/core.py unpacks desc_dev with struct format "<BBHBBBBHHHBBBB" (18 bytes)
    and indexes desc_cfg[8], so these cannot be None.
    """

    desc_dev = bytes(18)
    desc_cfg = bytes(9)
    itf_max = 0
    ep_max = 0
    str_max = 0


class USBDevice:
    """Mock of machine.USBDevice, enough for usb/device/core.py to be constructed."""

    BUILTIN_NONE = _BuiltinUSBDriver()
    BUILTIN_DEFAULT = _BuiltinUSBDriver()

    def __init__(self, *args):
        self.builtin_driver = self.BUILTIN_NONE
        self._active = False

    def config(self, *args, **kwargs):
        pass

    def active(self, *optional_value):
        if optional_value:
            self._active = bool(optional_value[0])
        return self._active

    def submit_xfer(self, *args):
        pass

    def stall(self, *args):
        pass
