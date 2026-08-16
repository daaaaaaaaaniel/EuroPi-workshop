"""
MicroPython USB device support, vendored from micropython-lib.

Provides the runtime needed to present EuroPi to a USB host as a device -- currently
used by contrib/midi2cv.py to appear as a USB MIDI device.

Source:    https://github.com/micropython/micropython-lib/tree/master/micropython/usb
Packages:  usb-device 0.2.1, usb-device-midi 0.1.0
Files:     device/__init__.py and device/core.py from usb-device
           device/midi.py from usb-device-midi
Modified:  no -- the files are byte-identical to upstream, so this copy can be
           refreshed by copying over it

The two upstream packages both install into the same ``usb/device`` namespace, which is
why they are flattened into one directory here.

Requires MicroPython 1.23 or newer, for ``machine.USBDevice``.

----------------------------------------------------------------------------------------

MIT License

Copyright (c) 2022-2024 Angus Gratton
Copyright (c) 2023 Paul Hamshere

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
