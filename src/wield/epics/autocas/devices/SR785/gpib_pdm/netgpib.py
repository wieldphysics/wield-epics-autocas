#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import sys
import socket
import time
import select
import struct


class netGPIB:
    def __init__(self, ip, gpibAddr, eot="\004", debug=0):

        # End of Transmission character
        self.eot = eot
        # EOT character number in the ASCII table
        self.eotNum = struct.unpack("B", eot)[0]

        # Debug flag
        self.debug = debug

        self.ip = ip
        self.gpibAddr = gpibAddr

    def connect(self):
        # Connect to the GPIB-Ethernet converter
        netAddr = (self.ip, 1234)
        self.netSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.netSock.connect(netAddr)

        # Initialize the GPIB-Ethernet converter
        # Set socket to non-blocking
        self.netSock.setblocking(0)
        # Set the gpib address
        self.netSock.send("++addr " + str(self.gpibAddr) + "\n")
        time.sleep(0.1)
        # Do not append anything to instrument commands
        self.netSock.send("++eos 3\n")
        time.sleep(0.1)
        # Set to controller mode
        self.netSock.send("++mode 1\n")
        time.sleep(0.1)
        # auto mode off
        self.netSock.send("++auto 0\n")
        time.sleep(0.1)
        # ifc asserts GPIB IFC signal for 150 microseconds making Prologix
        # GPIBETHERNET controller the Controller-In-Charge on the GPIB bus.
        self.netSock.send("++ifc\n")
        time.sleep(0.1)
        # Specifies the timeout value to be used in the read command and
        # spoll command to 3 seconds.
        self.netSock.send("++read_tmo_ms 3000\n")
        time.sleep(0.1)
        # Set the character to be appended to network output when
        # EOI is detected.
        self.netSock.send("++eot_enable 1\n")
        self.netSock.send("++eot_char " + str(self.eotNum) + "\n")

    def getData(self, buf, sleep=0.1):
        data = ""
        dlen = 0
        if self.debug == True:
            print "0 bytes received"
        while 1:  # Repeat reading data until eot is found
            while 1:  # Read some data
                readSock, writeSock, errSock = select.select([self.netSock], [], [], 3)
                if len(readSock) == 1:
                    data1 = readSock[0].recv(buf)
                    if self.debug == True:
                        dlen = dlen + len(data1)
                        print "%d bytes received." % dlen
                    break

            if data1[-1] == self.eot:  # if eot is found at the end
                data = data + data1[:-1]  # remove eot
                break
            else:
                data = data + data1
                time.sleep(1)

        return data

    def query(self, string, buf=128, IFCCheck=True, sleep=0):
        """Send a query to the device and return the result."""
        self.command(string, IFCCheck=IFCCheck)
        time.sleep(sleep)
        self.netSock.send("++read eoi\n")  # Change to listening mode
        return self.getData(buf)

    def command(self, string, IFCCheck=True, sleep=0):
        """Send a command to the device."""
        self.netSock.send(string + "\n")
        if IFCCheck:
            self.waitIFC()
        time.sleep(sleep)

    def waitIFC(self):
        """serial poll until IFC (bit7) is set (command done)"""
        while 1:
            stb = int(self.spoll())
            if stb & 0b10000000:
                break
            # time.sleep(0.1)
        if stb & 0b100000:
            # if ESB bit is set, there must be a command error in the Standard
            # Event Status word.
            raise RuntimeError("EXE error\n Status bit: %d" % stb)

    def spoll(self):
        """Perform a serial polling and return the result."""
        self.netSock.send("++spoll\n")
        time.sleep(0.1)
        while 1:  # Read some data
            readSock, writeSock, errSock = select.select([self.netSock], [], [], 3)
            if len(readSock) == 1:
                data = readSock[0].recv(128)
                break
        return data[:-2]

    def close(self):
        self.netSock.close()

    def setDebugMode(self, debugFlag):
        if debugFlag:
            self.debug = 1
        else:
            self.debug = 0
