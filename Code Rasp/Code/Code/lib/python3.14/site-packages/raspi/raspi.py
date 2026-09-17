#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2009-2015 Joao Carlos Roseta Matos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Helper functions to use with the Raspberry Pi and the RPi.GPIO."""

# Python 3 compatibility
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# import builtins  # Python 3 compatibility
# import future  # Python 3 compatibility
# import io  # Python 3 compatibility
import time

import numpy as np
import RPi.GPIO as GPIO


HIGH = GPIO.HIGH
LOW = GPIO.LOW


def set_pins_same_signal(pins, signal=LOW, pause=0):
    """Activates same signal on pins."""
    GPIO.output(pins, signal)
    time.sleep(pause)


def set_pins_signals(pins, signals, pause=0):
    """Activates signal on pins."""
    GPIO.output(pins, signals)
    time.sleep(pause)


def pins_low(pins, pause=0):
    """Activates low (0 volts/GND) signal on pins."""
    set_pins_same_signal(pins, LOW, pause)


def pins_high(pins, pause=0):
    """Activates high (3.3 volts) signal on pins."""
    set_pins_same_signal(pins, HIGH, pause)


def led_blink(led, pause=0.5, nr_times=3):
    """Blink LED."""
    for _ in range(nr_times):
        pins_high(led, pause)
        pins_low(led, pause)


def leds_blink(leds, pause=0.5, nr_times=3):
    """Blink LEDs, one at a time."""
    for pin in leds:
        led_blink(pin, pause, nr_times)


def leds_sequence(leds, pause=1):
    """Light LEDs in sequence."""
    for pin in leds:
        pins_high(pin, pause)
    for pin in leds:
        pins_low(pin, pause)


def leds_out_sequence(leds, pause=1):
    """Lights pairs of LEDs in sequence from inside out.

    Requires even number of LEDs.
    """
    nr_leds = len(leds)
    for pos in range(nr_leds // 2, 0, -1):  # reverse order
        # activate pair
        pins_high(leds[pos - 1])
        pins_high(leds[-pos + nr_leds])
        # pause
        time.sleep(pause)
        # deactivate pair
        pins_low(leds[pos - 1])
        pins_low(leds[-pos + nr_leds])
    time.sleep(pause)


def leds_random(leds, pause=1):
    """Lights LEDs in random order."""
    random_leds = leds[:]
    np.random.shuffle(random_leds)
    for led in random_leds:
        pins_high(led)
        time.sleep(pause)
    return random_leds


def is_high(pin):
    """True if pin has a high signal."""
    return GPIO.input(pin) == HIGH


def is_low(pin):
    """True if pin has a low signal."""
    return GPIO.input(pin) == LOW


def is_pressed(button, pressed=HIGH):
    """True if button is pressed."""
    if pressed == HIGH:
        return GPIO.input(button) == HIGH
    else:
        return GPIO.input(button) == LOW


def check_buttons(buttons, pause=0):
    """Checks if list of buttons are (short or long) pressed."""
    pressed = {}
    for pin in buttons:  # short pressed
        pressed[pin] = 0
        if is_high(pin):
            pressed[pin] += 1
    if pause:  # long pressed
        time.sleep(pause)
        for pin in buttons:
            if is_high(pin):
                pressed[pin] += 1
    return pressed


def buzz(buzzer, pause=1):
    """Activates buzzer."""
    pins_high(buzzer, pause)
    pins_low(buzzer)


def define_in_pins(pins, pull_up_down=GPIO.PUD_DOWN):
    """Setup pins as input."""
    if pull_up_down is None:  # don't activate pull up/dn resistor
        GPIO.setup(pins, GPIO.IN)
    else:  # activate pull up/dn resistor
        GPIO.setup(pins, GPIO.IN, pull_up_down=pull_up_down)


def define_out_pins(pins, initial=LOW):
    """Setup pins as output."""
    if initial is None:  # don't define initial state
        GPIO.setup(pins, GPIO.OUT)
    else:  # define initial state
        GPIO.setup(pins, GPIO.OUT, initial=initial)


def setup(in_pins=[], out_pins=[], in_pull=GPIO.PUD_DOWN, out_initial=LOW,
          pins_numbering=GPIO.BOARD):
    """Setup procedure."""
    GPIO.setmode(pins_numbering)
    GPIO.setwarnings(False)
    if in_pins:
        define_in_pins(in_pins, in_pull)
    if out_pins:
        define_out_pins(out_pins, out_initial)


def cleanup():
    """Cleanup procedure."""
    GPIO.cleanup()


if __name__ == '__main__':
    # import doctest
    # doctest.testmod(verbose=True)
    pass
