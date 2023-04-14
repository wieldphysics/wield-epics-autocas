#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
Script for EPICS communication with Newport 3040 Temperature controller
"""

import time
import serial

# from epics import PV
import re
from wield import declarative


terminator_string = "\r\n"


class TempControllerScript(declarative.OverridableObject):
    """ """

    @declarative.dproperty
    def reactor(self):
        from YALL.controls.core.coroutine.main_reactor import PolyReactor, reactor

        if isinstance(reactor, PolyReactor):
            from YALL.controls.core.coroutine.main_reactor_sync import reactor

            print("BOOTUP STD")
            reactor.bootup_from_poly()
            # reactor.elevate_to_thread()
        return reactor

    @declarative.dproperty
    def state_connect(self):
        rb = declarative.RelayBool(True)
        return rb

    @declarative.dproperty
    def ebridge(self, ebr):
        self.reactor
        ebr.state_connect_local.assign(True)
        ebr.state_connect.bool_register(self.state_connect)
        ebr.rv_connect_mode.value = "master"
        return ebr

    @declarative.dproperty
    def port(self, port="/dev/ttyUSB1"):
        return port

    @declarative.dproperty
    def serial(self):
        # configure the serial connections (The port may change after the computer reboots or device is unplugged...set up with udev rule?)
        ser = serial.Serial(
            port=self.port,
            baudrate=38400,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
        )
        return ser

    def setMonitorValue(self, chan, RS232cmd, inputType):
        # Read the temp controller value and write value to appropriate EPICS channel

        self.serial.flushInput()
        self.serial.write(RS232cmd + terminator_string)
        mon_val = ""
        stime = time.time()
        while terminator_string != mon_val[-2:]:
            mon_val += self.serial.read(1)
            ctime = time.time()
            if ctime - stime > 1:
                print("Read Timeout")
                self.serial.flushInput()
                return
        mon_val = mon_val.strip()
        # convert from string if necessary
        if inputType == float:
            vals = re.findall(r"-?\d+.\d\d\d\d", mon_val)
            if vals == []:
                mon_val = ""
                # Do Nothing...Read Error don't update EPICS Channel
            else:
                # print("PUTTING: ", vals)
                chan.value = float(vals[0])

        # String output: Strip, but don't convert to float
        elif inputType == str:
            if len(mon_val) == 0:
                pass
                # Do Nothing...Read Error don't update EPICS Channel
            else:
                chan.put(mon_val)
        elif inputType == bool:
            vals = re.findall(r"(-?\d+)(\.\d+)?", mon_val)
            if vals:
                tval = "".join(vals[0])
                chan.assign(bool(int(tval)))
        else:
            print("Unkown command")
            print(RS232cmd, mon_val.strip())

    def localMode(self):
        # Go to local mode: Uself.serial can manually operate TEC controller until another RS232 command is sent
        # An RS232 command will trigger REMOTE mode, at which point the buttons on the TEC controller won't do anything.
        # Toggle local mode switch again to return to local operation.
        if self.ebridge.local_control:
            self.serial.write("LOCAL 1" + terminator_string)
        else:
            self.serial.write("LOCAL 0" + terminator_string)

    def reset_local_mode(self):
        if self.ebridge.local_control:
            self.localMode()

    @declarative.dproperty
    def gain_cb_setup(self):
        def set_gain(value):
            self.serial.write("TEC:GAIN " + str(value) + terminator_string)
            self.setMonitorValue(self.ebridge.gain_mon, "TEC:GAIN?", str)
            self.reset_local_mode()

        self.ebridge.gain.register(
            callback=set_gain,
            call_immediate=False,
        )

    @declarative.dproperty
    def temp_set_cb_setup(self):
        def set_temp(value):
            self.serial.write("TEC:T " + str(value) + terminator_string)
            self.setMonitorValue(self.ebridge.temp_set_mon, "TEC:SET:T?", float)
            self.reset_local_mode()

        self.ebridge.temp_set.register(
            callback=set_temp,
            call_immediate=False,
        )

    @declarative.dproperty
    def current_limit_cb_setup(self):
        def set_val(value):
            self.serial.write("TEC:LIMIT:ITE " + str(value) + terminator_string)
            self.setMonitorValue(
                self.ebridge.current_limit_mon, "TEC:LIMIT:ITE?", float
            )
            self.reset_local_mode()

        self.ebridge.current_limit.register(
            callback=set_val,
            call_immediate=False,
        )

    @declarative.dproperty
    def current_set_cb_setup(self):
        def set_val(value):
            self.serial.write("TEC:ITE " + str(value) + terminator_string)
            self.setMonitorValue(self.ebridge.current_out_set_mon, "TEC:ITE?", float)
            self.reset_local_mode()

        self.ebridge.current_out_set.register(
            callback=set_val,
            call_immediate=False,
        )

    @declarative.dproperty
    def mode_cb_setup(self):
        def set_val(value):
            print("SET MODE: ", value)
            self.serial.write("TEC:MODE:" + str(value) + terminator_string)
            # setting the mode seems to kill the output enable, so reset it
            self.output_enable_cb_setup.set_val(bool(self.ebridge.out_enable))
            self.setMonitorValue(self.ebridge.mode_mon, "TEC:MODE?", str)
            self.reset_local_mode()

        self.ebridge.mode.register(
            callback=set_val,
            call_immediate=False,
        )

    @declarative.dproperty
    def temp_max_cb_setup(self):
        def set_val(value):
            self.serial.write("TEC:LIM:THI " + str(value) + terminator_string)
            self.setMonitorValue(self.ebridge.temp_max_mon, "TEC:LIM:THI?", float)
            self.reset_local_mode()

        self.ebridge.temp_max.register(
            callback=set_val,
            call_immediate=False,
        )

    @declarative.dproperty
    def temp_min_cb_setup(self):
        def set_val(value):
            self.serial.write("TEC:LIM:TLO " + str(value) + terminator_string)
            self.setMonitorValue(self.ebridge.temp_min_mon, "TEC:LIM:TLO?", float)
            self.reset_local_mode()

        self.ebridge.temp_min.register(
            callback=set_val,
            call_immediate=False,
        )

    @declarative.dproperty
    def output_enable_cb_setup(self):
        def set_val(bval):
            print("OUTPUT ENABLE: ", bval, str(int(bval)))
            self.serial.write("TEC:OUT " + str(int(bval)) + terminator_string)
            self.setMonitorValue(self.ebridge.out_enable_mon, "TEC:OUT?", bool)
            self.reset_local_mode()

        self.ebridge.out_enable.register(
            callback=set_val,
            assumed_value=False,
        )
        return Bunch(locals())

    def main(self):
        ctime = time.time()
        lfulltime = 0
        while True:
            self.reactor.flush(to_time=ctime + 1 / 4)
            ctime = time.time()
            self.serial.flushInput()
            self.reactor.capture()

            checktime = 2
            # check way less frequently if local control is on
            if self.ebridge.local_control:
                checktime = 30

            # only get the other monitors every 2 seconds
            if ctime - lfulltime > checktime:
                self.setMonitorValue(self.ebridge.temp_measured, "TEC:T?", float)
                self.setMonitorValue(
                    self.ebridge.current_out_measured, "TEC:ITE?", float
                )
                self.setMonitorValue(self.ebridge.R_measured, "TEC:R?", float)
                self.setMonitorValue(self.ebridge.temp_set_mon, "TEC:SET:T?", float)
                self.setMonitorValue(self.ebridge.gain_mon, "TEC:GAIN?", str)
                self.setMonitorValue(
                    self.ebridge.current_limit_mon, "TEC:LIMIT:ITE?", float
                )
                self.setMonitorValue(
                    self.ebridge.current_out_set_mon, "TEC:ITE?", float
                )
                self.setMonitorValue(self.ebridge.out_enable_mon, "TEC:OUT?", bool)
                self.setMonitorValue(self.ebridge.temp_max_mon, "TEC:LIM:THI?", float)
                self.setMonitorValue(self.ebridge.temp_min_mon, "TEC:LIM:TLO?", float)
                self.setMonitorValue(self.ebridge.mode_mon, "TEC:MODE?", str)
                lfulltime = ctime
            elif not self.ebridge.local_control:
                # don't check these so regularly if local control is on
                self.setMonitorValue(self.ebridge.temp_measured, "TEC:T?", float)
                self.setMonitorValue(
                    self.ebridge.current_out_measured, "TEC:ITE?", float
                )

            # since we just did a serialcommand, reset local control
            if self.ebridge.local_control:
                self.localMode()

            self.reactor.release()


if __name__ == "__main__":
    from YALL.controls.systems.TST3040.TST import EBridge

    ebr = EBridge(
        ifo="T1",
        local=True,
    )
    prg = TempControllerScript(
        ebridge=ebr.NF3040,
    )
    prg.main()
