#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import serial, time

    #initialization and open the port

    #possible timeout values:

    #    1. None: wait forever, block call

    #    2. 0: non-blocking mode, return immediately

    #    3. x, x is bigger than 0, float allowed, timeout block call

ser = serial.Serial()

    #ser.port = "/dev/ttyUSB0"

ser.port = "/dev/ttyUSB0"

    #ser.port = "/dev/ttyS2"

ser.baudrate = 9600

ser.bytesize = serial.EIGHTBITS #number of bits per bytes

ser.parity = serial.PARITY_NONE #set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE #number of stop bits

    #ser.timeout = None          #block read

ser.timeout = 1            #non-block read

    #ser.timeout = 2              #timeout block read

ser.xonxoff = False     #disable software flow control

ser.rtscts = False     #disable hardware (RTS/CTS) flow control

ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control

ser.writeTimeout = 2     #timeout for write

try: 

    ser.open()

except Exception, e:

    print "error open serial port: " + str(e)

    exit()

if ser.isOpen():

    try:

	ser.flushInput() #flush input buffer, discarding all its contents

	ser.flushOutput()#flush output buffer, aborting current output 

                 #and discard all that is in buffer

    #write data

    ser.write("AT+CSQ")

    print("write data: AT+CSQ")

    time.sleep(0.5)  #give the serial port sometime to receive the data

    numOfLines = 0

    while True:

        response = ser.readline()

        print("read data: " + response)

        numOfLines = numOfLines + 1

        if (numOfLines >= 5):

            break

    ser.close()
