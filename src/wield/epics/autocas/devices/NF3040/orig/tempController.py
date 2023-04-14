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
from time import sleep
import serial
from epics import PV
import re

Tset = PV("M1:SQZMON-SHG_TEMP_TSET")
TsetMon = PV("M1:SQZMON-SHG_TEMP_TSET_MON")
Tmeas = PV("M1:SQZMON-SHG_TEMP_TMEAS")
Gain = PV("M1:SQZMON-SHG_TEMP_GAIN")
GainMon = PV("M1:SQZMON-SHG_TEMP_GAIN_MON")
ILim = PV("M1:SQZMON-SHG_TEMP_ILIM")
ILimMon = PV("M1:SQZMON-SHG_TEMP_ILIM_MON")
IOut = PV("M1:SQZMON-SHG_TEMP_IOUT")
ISet = PV("M1:SQZMON-SHG_TEMP_ISET")
ISetMon = PV("M1:SQZMON-SHG_TEMP_ISET_MON")
Rmeas = PV("M1:SQZMON-SHG_TEMP_RMEAS")
Mode = PV("M1:SQZMON-SHG_TEMP_MODE")
ModeMon = PV("M1:SQZMON-SHG_TEMP_MODE_MON")
OutEn = PV("M1:SQZMON-SHG_TEMP_OUT_EN")
OutEnMon = PV("M1:SQZMON-SHG_TEMP_OUT_EN_MON")
TMin = PV("M1:SQZMON-SHG_TEMP_TMIN")
TMinMon = PV("M1:SQZMON-SHG_TEMP_TMIN_MON")
TMaxMon = PV("M1:SQZMON-SHG_TEMP_TMAX_MON")
TMax = PV("M1:SQZMON-SHG_TEMP_TMAX")
Local = PV("M1:SQZMON-SHG_TEMP_LOCAL")

# configure the serial connections (The port may change after the computer reboots or device is unplugged...set up with udev rule?)
ser = serial.Serial(
    port="/dev/ttyUSB1",
    baudrate=38400,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
)


def setMode(mode):
    print mode
    if mode == 0:
        ser.write("TEC:MODE:T" + "\r\n")  # Constant temperature mode
        sleep(0.25)
    elif mode == 1:
        ser.write("TEC:MODE:ITE" + "\r\n")  # Constant current mode
        sleep(0.25)

    # Query the mode value on the Temp controller and write value to EPICS monitor channel
    ser.write("TEC:MODE?" + "\r\n")

    # let's wait 0.1 seconds before reading output (let's give device time to answer)
    sleep(0.1)
    modeVal = ""

    while ser.inWaiting() > 0:
        modeVal += ser.read(1)
    if modeVal.strip() == "T":
        print modeVal.strip()
        ModeMon.put("constT")
    elif modeVal.strip == "ITE":
        print modeVal.strip()
        ModeMon.put("constI")


def localMode():
    # Go to local mode: User can manually operate TEC controller until another RS232 command is sent
    # An RS232 command will trigger REMOTE mode, at which point the buttons on the TEC controller won't do anything.
    # Toggle local mode switch again to return to local operation.
    ser.write("LOCAL 1" + "\r\n")
    sleep(0.25)


def setOutput(onoff):
    print onoff
    if onoff == 1:
        # Enable the temperature controller output
        ser.write("TEC:OUT 1" + "\r\n")
        sleep(0.25)
    elif onoff == 0:
        # Disable the temperature controller output
        ser.write("TEC:OUT 0" + "\r\n")
        sleep(0.25)


def setMonitorValue(chan, RS232cmd, inputType):
    # Read the temp controller value and write value to appropriate EPICS channel
    ser.write(RS232cmd + "\r\n")
    # let's wait 0.2 seconds before reading output (let's give device time to answer)
    sleep(0.1)
    MonVal = ""
    # let's wait one second before reading output (let's give device time to answer)
    while ser.inWaiting() > 0:
        MonVal += ser.read(1)
    # convert from string if necessary
    if inputType == 1:
        if (
            re.findall("-" + "\d+.\d\d\d\d", MonVal)
            + re.findall("\d+.\d\d\d\d", MonVal)
            == []
        ):
            MonVal = ""
            # Do Nothing...Read Error don't update EPICS Channel
        else:
            chan.put(
                float(
                    (
                        re.findall("-" + "\d+.\d\d\d\d", MonVal)
                        + re.findall("\d+.\d\d\d\d", MonVal)
                    )[0]
                )
            )
    # String output: Strip, but don't convert to float
    elif inputType == 2:
        print MonVal.strip()
        if re.findall("\d", MonVal) == []:
            MonVal = ""
            # Do Nothing...Read Error don't update EPICS Channel
        else:
            chan.put(re.findall("\d", MonVal)[0])


if __name__ == "__main__":
    # Initialize all of the values by reading each once
    TsetValOld = Tset.get()
    print TsetValOld
    GainValOld = Gain.get()
    print GainValOld
    ILimValOld = ILim.get()
    print ILimValOld
    ModeValOld = Mode.get()
    print ModeValOld
    OutEnValOld = OutEn.get()
    print OutEnValOld
    TMaxValOld = TMax.get()
    print TMaxValOld
    TMinValOld = TMin.get()
    print TMinValOld
    ISetValOld = ISet.get()
    LocalValOld = Local.get()
    while True:
        if Local.get() == 0:
            TsetVal = Tset.get()
            # Set the temperature value on the temperature controller if EPICS value changes
            if TsetVal != TsetValOld:
                print TsetVal
                ser.write("TEC:T " + str(TsetVal) + "\r\n")
                sleep(0.25)
                TsetValOld = TsetVal
                # Read the set temp and write value to appropriate EPICS channel
                setMonitorValue(TsetMon, "TEC:SET:T?", 1)
            #        GainVal = Gain.get()
            # Set Gain on temp controller if EPICS value changes
            #        if GainVal != GainValOld:
            #            ser.write('TEC:GAIN ' + str(GainVal) + '\r\n')
            #            sleep(0.25)
            #            GainValOld = GainVal
            # Read the gain and write value to appropriate EPICS channel
            #            setMonitorValue(GainMon,'TEC:GAIN?',2)
            ILimVal = ILim.get()
            # Set the current limit value on the temperature controller if EPICS value changes
            if ILimVal != ILimValOld:
                ser.write("TEC:LIMit:ITE " + str(ILimVal) + "\r\n")
                sleep(0.25)
                ILimValOld = ILimVal
                # Read the current limit and write value to appropriate EPICS channel
                setMonitorValue(ILimMon, "TEC:LIMit:ITE?", 1)
            ISetVal = ISet.get()
            if ISetVal != ISetValOld:
                ser.write("TEC:ITE " + str(ISetVal) + "\r\n")
                sleep(0.25)
                ISetValOld = ISetVal
                # Read the current limit and write value to appropriate EPICS channel
                setMonitorValue(ISetMon, "TEC:ITE?", 1)
            ModeVal = Mode.get()
            # Set the Mode of the temperature controller if EPICS value Changes
            if ModeVal != ModeValOld:
                setMode(ModeVal)
                ModeValOld = ModeVal
            OutEnVal = OutEn.get()
            # set the Output to on or off if EPICS value changes
            if OutEnVal != OutEnValOld:
                setOutput(OutEnVal)
                OutEnValOld = OutEnVal
                # Read the output enable status and write value to appropriate EPICS channel
                setMonitorValue(OutEnMon, "TEC:OUT?", 2)
            #       TMaxVal = TMax.get()
            # Set TMax on temp controller if EPICS value changes
            #        if TMaxVal != TMaxValOld:
            #            ser.write('TEC:LIM:THI ' + str(TMaxVal) + '\r\n')
            #            sleep(0.25)
            #            TMaxValOld = TMaxVal
            # Read the temperature maximum setting and write value to appropriate EPICS channel
            #            setMonitorValue(TMaxMon,'TEC:LIM:THI?',1)
            #        TMinVal = TMax.get()
            #        #Set TMin on temp controller if EPICS value changes
            #        if TMinVal != TMinValOld:
            #            ser.write('TEC:LIM:TLO ' + str(TMinVal) + '\r\n')
            #            sleep(0.25)
            #            TMinValOld = TMinVal
            #            Read the temperature minimum setting and write value to appropriate EPICS channel
            #            setMonitorValue(TMinMon,'TEC:LIM:TLO?',1)

            # Read measured Temp and write value to appropriate EPICS channel
            setMonitorValue(Tmeas, "TEC:T?", 1)

            # Read the output current and write value to appropriate EPICS channel
            setMonitorValue(IOut, "TEC:ITE?", 1)

            # Enable manual operation of TEC if Local switch is "TRUE"
        LocalVal = Local.get()
        if LocalVal != LocalValOld:
            if Local.get() == 1:
                localMode()
            LocalValOld = LocalVal
