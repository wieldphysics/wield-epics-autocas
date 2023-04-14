#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""

import warnings
import serial
from wield import declarative
from wield.bunch import Bunch

# for exclusive device locks
import fcntl
import termios

from .. import cascore
from .serial_base import (
    SerialConnection,
    SerialTimeout,
)
from .gpib_base import GPIBAddressed

# from . import utilities


class USBPrologixGPIB(SerialConnection):
    @cascore.dproperty_ctree(default="/dev/serial/by-id/ttyUSB")
    def device_path(self, val):
        """
        path to the serial block device, usually something in /dev/serial/by-id/. Can use
        /dev/ttyUSBx, but it is better to use the identified values as they are stable through
        restarts and connection order.
        """
        if val.startswith("/dev/ttyUSB"):
            warnings.warn(
                "Currently using a generic device name {0}, please use objects in /dev/serial/by-id/ for serial-number keyed usb devices".format(
                    val
                )
            )
        return val

    @cascore.dproperty_ctree(default=1)
    def poll_rate_s(self, val=1):
        """
        Poll rate to attempt connections to the serial device in seconds
        """
        val = float(val)
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=True)
    def exclusive_lock(self, val):
        """
        Set the device into exclusive lock mode to prevent external manipulation
        """
        val = bool(val)
        return val

    @cascore.dproperty
    def rb_communicating(self):
        rb = cascore.RelayBool(False)
        self.cas_host(
            rb,
            name="COMM",
            interaction="report",
        )
        return rb

    def address_gpib_create(self, GPIB_addr, **kwargs):
        """
        Requires standard name/parent/prefix kwargs too since it is an instance
        """
        return GPIBAddressed(serial=self, GPIB_addr=GPIB_addr, **kwargs)

    _serial_obj = None

    def _connect_task(self):
        assert self._serial_obj is None
        try:
            print("CHECKING: ", self.device_path)
            sdev = serial.Serial(
                self.device_path,
                baudrate=9600,  # doesn't matter for this device
                timeout=1,
                xonxoff=0,
                rtscts=0,
            )

            if self.exclusive_lock:
                # https://stackoverflow.com/questions/49636520/how-do-you-check-if-a-serial-port-is-open-in-linux
                # put an exclusive lock on the device!
                fcntl.ioctl(sdev.fd, termios.TIOCEXCL)

            sdev.write(b"++mode 1\n")
            # MUST Be in controller mode or auto will freeze the device!
            sdev.write(b"++auto 0\n")
            sdev.write(b"++ifc\n")

        except serial.SerialException as E:
            self.error(0, str(E))
        else:
            self._serial_obj = sdev
            self.error.clear()
            # stop this task
            self.reactor.enqueue_looping(self._connect_task, period_s=None)

            self.queue_clear()
            self.rb_connected.assign(True)

    @cascore.dproperty
    def _startup(self):
        self.reactor.enqueue_looping(self._connect_task, period_s=self.poll_rate_s)

    def run(self):
        if self._serial_obj is not None:
            try:
                return super(USBPrologixGPIB, self).run()
            except serial.SerialException as E:
                self.error(0, str(E))
                self._serial_obj = None
                self.rb_connected.assign(False)
                self.rb_communicating.assign(False)
                self.reactor.enqueue_looping(
                    self._connect_task, period_s=self.poll_rate_s
                )
        else:
            # TODO, print warning or something? can't do anything if device isn't connected
            return

    def cmd_object(self):
        b = Bunch()
        b.writeline = self._device_writeline
        b.readline = self._device_readline
        b.flush = self._device_flush
        b.reset_in = self._device_reset_input
        b.reset_out = self._device_reset_output
        return b

    _debug_echo = False

    def _device_writeline(self, line):
        if self._debug_echo:
            print("serialw:", line)
        self._serial_obj.write((line + "\n").encode())
        return

    def _device_readline(self, timeout_s=None):
        if timeout_s is not None:
            timeout_prev = self._serial_obj.timeout

        try:
            # gpib devices have a read mode which must be activated at start
            self._serial_obj.write(b"++read eoi\n")
            line = self._serial_obj.readline().decode()
            if line == "":
                # can only happen if timeout occured
                raise SerialTimeout("Timeout")
        except Exception as E:
            if self._debug_echo:
                print("serialr:", E)
            raise
        else:
            if self._debug_echo:
                print("serialr:", line.strip())
        finally:
            if timeout_s is not None:
                self._serial_obj.timeout = timeout_prev

        return line.strip()

    def _device_flush(self):
        if self._debug_echo:
            print("serial flush")
        self._serial_obj.flush()
        return

    def _device_reset_input(self):
        if self._debug_echo:
            print("serial reset input")
        self._serial_obj.reset_input_buffer()
        return

    def _device_reset_output(self):
        if self._debug_echo:
            print("serial reset output")
        self._serial_obj.reset_output_buffer()
        return
