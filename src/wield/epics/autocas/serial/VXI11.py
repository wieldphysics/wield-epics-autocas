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

from wield import declarative
from wield.bunch import Bunch
import vxi11
import socket
import errno

from .. import cascore
from .serial_base import (
    SerialConnection,
    SerialError,
    SerialTimeout,
)

# from . import utilities


class VXI11Connection(SerialConnection):
    @cascore.dproperty_ctree(default="192.168.1.253")
    def device_address(self, val):
        """
        path to the serial block device, usually something in /dev/serial/by-id/. Can use
        /dev/ttyUSBx, but it is better to use the identified values as they are stable through
        restarts and connection order.
        """
        return val

    @cascore.dproperty_ctree(default=0.2)
    def timeout_s(self, val):
        """
        Timeout for connection status
        """
        val = float(val)
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=1)
    def poll_rate_s(self, val=1):
        """
        Poll rate to attempt connections to the serial device in seconds
        """
        val = float(val)
        assert val > 0
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
            print("CHECKING: ", self.device_address)
            sdev = vxi11.Instrument(
                self.device_address,
            )
            sdev.timeout = self.timeout_s
            sdev.open()

        except socket.timeout as E:
            self.error(0, str(E))
        except socket.error as E:
            # E.errno == errno.EHOSTUNREACH
            self.error(0, E)
        except vxi11.rpc.RPCError as E:
            self.error(0, "VXI11/RPC Err: connect to wrong device?")
        except vxi11.vxi11.Vxi11Exception as E:
            self.error(0, E)
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
                return super(VXI11Connection, self).run()
            # TODO must also check RPCError in case it connects a socket to the wrong device!
            except SerialError as E:
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
        return b

    _debug_echo = False

    def _device_writeline(self, line):
        if self._debug_echo:
            print("serialw:", line)
        try:
            self._serial_obj.write(line)
        except socket.timeout as E:
            raise SerialTimeout(str(E))
        return

    def _device_readline(self, timeout_s=None):
        if timeout_s is not None:
            timeout_prev = self._serial_obj.timeout

        try:
            line = self._serial_obj.read()
            if line == "":
                # can only happen if timeout occured
                raise SerialTimeout("Timeout")
        except socket.timeout as E:
            raise SerialTimeout(str(E))
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
