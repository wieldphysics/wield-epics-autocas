#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import os
import re
import sys
import math
import optparse
import time
import pdb
import netgpibOLD as netgpib
import termstatus
import HP4195A

# Parse options
usage = """usage: %prog [options]

This program executes a network measurement using HP4195A.
Various measurement conditions can be set using options.
The measurement result will be saved in FILENAME.dat.
Optionally, it can plot the retrieved data using the gpibplot.py script.
"""

parser = optparse.OptionParser(usage=usage)
parser.add_option(
    "-f",
    "--file",
    dest="filename",
    help="Output file name without an extension",
    default="/data/eoelker/test",
)
parser.add_option(
    "-i", "--ip", dest="ipAddress", default="18.120.0.102", help="IP address/Host name"
)

parser.add_option(
    "-a",
    "--address",
    dest="gpibAddress",
    type="int",
    default=10,
    help="GPIB device address",
)

parser.add_option(
    "-c", "--chan", dest="chan", type="str", default="1", help="Channel (1 or 2)"
)

parser.add_option(
    "--st",
    "--start",
    dest="startF",
    type="str",
    default="1KHZ",
    help="Start frequency (example 3KHZ)",
)

parser.add_option(
    "--fin",
    "--end",
    dest="endF",
    type="str",
    default="2MHZ",
    help="End frequency (example 2MHZ)",
)

parser.add_option(
    "--bw",
    "--Bandwidth",
    dest="BW",
    type="str",
    default="300HZ",
    help="Bandwidth. Changes number of points - max number of points is 401",
)

parser.add_option(
    "-r",
    dest="atr",
    type="str",
    default="10DB",
    help="Reference input Attenuation.  Specify in DB.",
)

parser.add_option(
    "-t",
    dest="att",
    type="str",
    default="10DB",
    help="Test input Attenuation. Specify in DB.",
)

parser.add_option(
    "-p", dest="pwr", type="str", default="0DBM", help="Source Power.  Specify in DBM"
)

parser.add_option(
    "--sweep",
    dest="sweep",
    type="str",
    default="2",
    help="set sweep type. 1=linear 2=log",
)

parser.add_option(
    "--plot",
    dest="plotData",
    default=False,
    action="store_true",
    help="Plot the downloaded data.",
)

parser.add_option(
    "--title",
    dest="title",
    type="string",
    default="",
    help="Title of the measurement. The given string will be written into the parameter file.",
)

(options, args) = parser.parse_args()
# Create a netGPIB class object
print("Connecting to " + str(options.ipAddress) + " ..."),
gpibObj = netgpib.netGPIB(options.ipAddress, options.gpibAddress, "\004", 0)
print("done.")

# File names
dataFileName = options.filename + ".dat"

print("Data will be written into " + dataFileName)
print("Setting up parameters for the measurement")

gpibObj.command("FNC1")  # Enable Network analyzer measurement
time.sleep(0.1)
gpibObj.command("RST")  # Restore default settings
time.sleep(0.1)

# setup measurement parameters
gpibObj.command(
    "OSC" + str(options.chan) + "=" + str(options.pwr)
)  # Set the source power
time.sleep(0.1)
gpibObj.command(
    "ATR" + str(options.chan) + "=" + str(options.atr)
)  # Set Reference Input Attenuation
time.sleep(0.1)
gpibObj.command(
    "ATT" + str(options.chan) + "=" + str(options.att)
)  # Set Test Input Attenuation
time.sleep(0.1)
gpibObj.command("START=" + str(options.startF))  # Set the start frequency
time.sleep(0.1)
gpibObj.command("STOP=" + str(options.endF))  # Set the end frequency
time.sleep(0.1)
gpibObj.command("RBW=" + str(options.BW))  # Set the Res BW
time.sleep(0.1)
gpibObj.command("SWT" + str(options.sweep))  # Sets sweep type (Log/Linear)
time.sleep(0.1)
gpibObj.command("GPP" + str(options.chan))  # T/R (dB)-theta units
time.sleep(0.1)
gpibObj.command("DSP" + str(options.chan))  # Rectangular X-A&B Display Format
time.sleep(0.1)
if str(options.chan) == "1":
    gpibObj.command("PORT1")  # T1/R1 Measurement
    time.sleep(0.1)
else:
    gpibObj.command("PORT5")  # T2/R2 Measurement
    time.sleep(0.1)

time.sleep(2)
print("Parameters Set")
dataFile = open(dataFileName, "w")

# Take the measurement


print("Taking Transfer Function")
meas_time = float(gpibObj.query("ST?"))  # Determine the measurement time
time.sleep(0.1)
gpibObj.command("SWM2")  # Single Sweep Mode
time.sleep(0.1)
gpibObj.command("SWTRG")  # Trigger the Sweep
time.sleep(meas_time)
time.sleep(1)


print("Getting Measurement Data")
HP4195A.getdata(gpibObj, dataFile, 1)
time.sleep(0.1)

dataFile.close()
gpibObj.close()
print("Done!")

if options.plotData:
    import gpibplot

    gpibplot.plotTFHP4195A(options.filename, options.title)
    raw_input("Press enter to quit:")
