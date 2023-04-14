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
    SerialError,
    SerialTimeout,
)

# from . import utilities


class USBDeviceRS232(SerialConnection):
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

    @cascore.dproperty_ctree(default=9600)
    def baud_rate(self, val):
        """
        Baud Rate for the connection. Must match settings of device
        """
        val = int(val)
        assert val > 0
        return val

    @cascore.dproperty_ctree(default="N")
    def parity(self, val):
        """
        configtype : serial_parity
        Parity of the connection, may be one of [N, O, E]. Must match settings of the device
        """
        assert val in ["N", "O", "E"]
        return val

    @cascore.dproperty_ctree(default=1)
    def stop_bits(self, val):
        """
        Stop Bits for the connection, may be one of [1, 2]
        """
        val = int(val)
        assert val in [1, 2]
        return val

    @cascore.dproperty_ctree(default=8)
    def byte_size(self, val):
        """
        byte size for the connection, may be one of [7, 8]
        """
        val = int(val)
        assert val in [7, 8]
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

    _serial_obj = None

    def _connect_task(self):
        assert self._serial_obj is None
        try:
            print("CHECKING: ", self.device_path)
            sdev = serial.Serial(
                self.device_path,
                baudrate=self.baud_rate,
                bytesize=self.byte_size,
                parity=self.parity,
                stopbits=self.stop_bits,
                timeout=1,
                xonxoff=0,
                rtscts=0,
            )
            print(sdev)

            if self.exclusive_lock:
                # https://stackoverflow.com/questions/49636520/how-do-you-check-if-a-serial-port-is-open-in-linux
                # put an exclusive lock on the device!
                fcntl.ioctl(sdev.fd, termios.TIOCEXCL)

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
                return super(USBDeviceRS232, self).run()
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
