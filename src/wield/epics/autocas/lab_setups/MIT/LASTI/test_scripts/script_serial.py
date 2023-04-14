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
    "/dev/ttyUSB1",
    baudrate=9600,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=2,
    xonxoff=0,
    rtscts=0,
)
print(ser)
# Needed to put the device in "Remote Mode" which disables the front panel unless the "local/menu" is pressed.

# can put the device into "local lockout" mode to prevent all front panel action
# ser.write('\x12\n')
# disables local lockout (otherwise requires power reset)
# ser.write('\x10\n')

# get ID String
ser.write(chr(01) + "\n")
# time.sleep(1)
for i in range(100):
    print(i)
    ser.timeout = 0.01
    ser.write("*TST?\n")
    resp = ser.readline()
    print("RESP: ", resp)
    if resp:
        break

ser.timeout = 1.0
ser.write("*IDN?\n")
print(ser.readline())

float_re = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"

re_SOURCE = re.compile("^:SOURCE (.)$")
re_FREQVALUE = re.compile("^:CFRQ:VALUE ({0});INC {0}$".format(float_re))
re_LEVELVALUE = re.compile(
    "^:RFLV:UNITS DBM;TYPE PD;VALUE ({0});INC {0};(ON|OFF)$".format(float_re)
)

ser.write(":SOURCE A;:SOURCE?\n")
line = ser.readline().strip()
print(line)

print("CHN: ", re_SOURCE.match(line).group(1))

ser.write("CFRQ:VALUE 201000022.1; CFRQ?\n")
line = ser.readline().strip()
print(line)
print("FREQ: ", re_FREQVALUE.match(line).group(1))


ser.write(":RFLV:UNITS DBM;:RFLV:VALUE -100DBM; RFLV?\n")
line = ser.readline().strip()
print(line)
print("LEVEL: ", re_LEVELVALUE.match(line).group(1))
# ser.write('STO:FULL 0\n')
# print(ser.readline())
