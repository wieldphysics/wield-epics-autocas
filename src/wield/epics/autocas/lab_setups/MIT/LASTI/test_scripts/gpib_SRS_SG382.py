#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import serial
import re
import time

ser = serial.Serial(
    "/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PXFA9IBH-if00-port0",
    baudrate=9600,
    timeout=0.5,
)
print(ser)

ser.write("++mode 1\n")
print("MODE 1:", ser.readline())
ser.write("++mode\n")
print("MODE:", ser.readline())
ser.write("++auto 0\n")

ser.write("++addr 3\n")
ser.write("*IDN?\n")
ser.write("++read eoi\n")
print("IDN", ser.readline())

# see page 68 of manual
ser.write("TYPE?\n")
ser.write("++read eoi\n")
print("MOD Type", ser.readline())

ser.write("MODL?\n")
ser.write("++read eoi\n")
print("MOD ENABLE:", ser.readline())

ser.write("MFNC?\n")
ser.write("++read eoi\n")
print("MOD Func:", ser.readline())


ser.write("MFNC?\n")
ser.write("++read eoi\n")
print("MOD Func:", ser.readline())


ser.write("COUP?\n")
ser.write("++read eoi\n")
print("MOD Coupling:", ser.readline())

ser.write("FDEV?\n")
ser.write("++read eoi\n")
print("MOD DEVN:", ser.readline())

ser.write("FNDV?\n")
ser.write("++read eoi\n")
print("MOD Noise DEVN:", ser.readline())


# CARRIER COMMANDS

ser.write("FREQ 200000000.0\n")
ser.write("FREQ?\n")
ser.write("++read eoi\n")
print("C FREQ:", ser.readline())

ser.write("ENBR?\n")
ser.write("++read eoi\n")
print("Type-N Out Enable:", ser.readline())

ser.write("AMPR?\n")
ser.write("++read eoi\n")
print("Type-N Out Ampl (dbm):", ser.readline())

ser.write("PHAS?\n")
ser.write("++read eoi\n")
print("Phase:", ser.readline())
