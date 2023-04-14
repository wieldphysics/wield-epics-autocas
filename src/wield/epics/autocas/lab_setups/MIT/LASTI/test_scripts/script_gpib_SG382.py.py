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

ser.write("++addr\n")
print("ADDR:", ser.readline())
ser.write("++ver\n")
print("VER:", ser.readline())
ser.write("++addr 0\n")
print("addr 0", ser.readline())
ser.write("++addr\n")
print("ADDR:", ser.readline())
ser.write("++mode\n")
print("MODE:", ser.readline())
ser.write("++mode 1\n")
print("MODE 1:", ser.readline())
ser.write("++mode\n")
print("MODE:", ser.readline())

ser.write("++auto\n")
print("AUTO:", ser.readline())

ser.timeout = 0.25
print("addr 0", ser.readline())
ser.write("++addr\n")
ser.write("*IDN?\n")
print("IDN", ser.readline())
ser.write("++read eoi\n")
print("IDN2", ser.readline())

float_re = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"

re_FREQVALUE = re.compile(
    "^:CFRQ:VALUE ({0});INC {0};MODE (?:FIXED|SWEPT)$".format(float_re)
)
re_LEVELVALUE = re.compile(
    "^:RFLV:UNITS DBM;TYPE PD;VALUE ({0});INC {0};ON$".format(float_re)
)

ser.write("CFRQ:VALUE 200000000.0; CFRQ?\n")
ser.write("++read eoi\n")
line = ser.readline().strip()
print(line)
print("FREQ: ", re_FREQVALUE.match(line).group(1))


ser.write(":RFLV:UNITS DBM;:RFLV:VALUE -100DBM; RFLV?\n")
ser.write("++read eoi\n")
line = ser.readline().strip()
print(line)
print("LEVEL: ", re_LEVELVALUE.match(line).group(1))
# ser.write('STO:FULL 0\n')
# print(ser.readline())

ser.write("++addr 3\n")
ser.write("*IDN?\n")
print("IDN", ser.readline())
ser.write("++read eoi\n")
print("IDN2", ser.readline())

ser.write("++addr 2\n")
ser.write("*IDN?\n")
print("IDN", ser.readline())
ser.write("++read eoi\n")
print("IDN2", ser.readline())
