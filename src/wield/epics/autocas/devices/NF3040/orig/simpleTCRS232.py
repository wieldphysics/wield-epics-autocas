#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
Simple script for talking to temperature controller by typing in RS232 Commands directly.
See Newport 3040 Programming manual for commands
"""


import time
import serial
import re

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port="/dev/ttyUSB1",
    baudrate=38400,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
)

ser.isOpen()

print 'Enter your commands below.\r\nInsert "exit" to leave the application.'

input = 1
while 1:
    # get keyboard input
    input = raw_input(">> ")
    # Python 3 users
    # input = input(">> ")
    if input == "exit":
        ser.close()
        exit()
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
        ser.write(input + "\r\n")
        out = ""
        # let's wait one second before reading output (let's give device time to answer)
        time.sleep(0.1)
        while ser.inWaiting() > 0:
            out += ser.read(1)

        if out != "":
            print ">>" + out.strip()
