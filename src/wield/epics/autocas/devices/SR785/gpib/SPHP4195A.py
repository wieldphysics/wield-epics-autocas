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
import HP4195A
import termstatus


# Parse options
usage = """usage: %prog [options]

This program executes a spectral measurement using HP4195A.
Various measurement conditions can be set using options.
The measurement result will be saved in FILENAME.dat.
Optionally, it can also plot the retrieved data using the plotgpibdata.py script.
Currently, Only single channel spectrum measurements are supported.
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
    "-i", "--ip", dest="ipAddress", default="18.120.0.103", help="IP address/Host name"
)
parser.add_option(
    "-a",
    "--address",
    dest="gpibAddress",
    type="int",
    default=17,
    help="GPIB device address",
)

parser.add_option(
    "--R1", dest="r1", default=False, action="store_true", help="Measure Input R1"
)

parser.add_option(
    "--T1", dest="t1", default=False, action="store_true", help="Measure input T1"
)

parser.add_option(
    "--R2", dest="r2", default=False, action="store_true", help="Measure input R2"
)

parser.add_option(
    "--T2", dest="t2", default=False, action="store_true", help="Measure input T2"
)
parser.add_option(
    "--AR1", dest="ar1", type="str", default="10DBM", help="Attenuation for input R1"
)

parser.add_option(
    "--AT1", dest="at1", type="str", default="10DBM", help="Attenuation for input T1"
)

parser.add_option(
    "--AR2", dest="ar2", type="str", default="10DBM", help="Attenuation for input R2"
)

parser.add_option(
    "--AT2", dest="at2", type="str", default="10DBM", help="Attenuation for input T2"
)

parser.add_option(
    "-L",
    dest="log",
    default="False",
    action="store_true",
    help="Chooses Log frequency scale",
)

parser.add_option(
    "--st", "--start", dest="startF", type="str", default="1KHZ", help="Start frequency"
)

parser.add_option(
    "--fin", "--end", dest="endF", type="str", default="2MHZ", help="End frequency"
)

parser.add_option(
    "--bw",
    "--Bandwidth",
    dest="BW",
    type="str",
    default="1KHZ",
    help="Bandwidth. Changes number of points - max number of points is 401",
)

parser.add_option(
    "--psd",
    dest="units",
    default=False,
    action="store_true",
    help="Change to PSD units (v/rt(Hz)).",
)

parser.add_option(
    "--plot",
    dest="plotData",
    default=False,
    action="store_true",
    help="Plot the downloaded data.",
)
parser.add_option(
    "--xlog",
    dest="xlog",
    default=False,
    action="store_true",
    help="Plot with logarithmic x axis",
)
parser.add_option(
    "--ylog",
    dest="ylog",
    default=False,
    action="store_true",
    help="Plot with logarithmic y axis",
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

gpibObj.command("FNC2")  # Enable Spectrum analyzer mode
time.sleep(0.1)
gpibObj.command("RST")  # Restore default settings
time.sleep(0.1)

# Set up the appropriate input.  The default input is R1.
# All inputs have a default input attenuation of 10dB

if options.t1:  # Sets input to T1
    gpibObj.command("PORT2")
    time.sleep(0.1)
    gpibObj.command("ATT1=" + str(options.at1))
    time.sleep(0.1)
elif options.r2:  # Sets input to R2
    gpibObj.command("PORT3")
    time.sleep(0.1)
    gpibObj.command("ATR2=" + str(options.ar2))
    time.sleep(0.1)
elif options.t2:  # Sets input to T2
    gpibObj.command("PORT4")
    time.sleep(0.1)
    gpibObj.command("ATT2=" + str(options.at2))
else:  # Sets input to R1.  Default case.
    gpibObj.command("PORT1")
    time.sleep(0.1)
    gpibObj.command("ATR1=" + str(options.ar1))
    time.sleep(0.1)

# Set measurement paramaters
gpibObj.command("START=" + str(options.startF))  # Sets Start Frequency
time.sleep(0.1)
gpibObj.command("STOP=" + str(options.endF))  # Sets stop frequency
time.sleep(0.1)
gpibObj.command("RBW=" + str(options.BW))  # sets resolution bandwidth
time.sleep(0.1)
if options.units:  # Optional uV/rt(Hz) units
    gpibObj.command("SAP6")
    time.sleep(0.1)
gpibObj.command("SCT2")  # Uses Log magnitude Scale
time.sleep(0.1)
if options.log:
    gpibObj.command("SWT2")  # Optional Log Frequency Scale
    time.sleep(0.1)

time.sleep(2)
print("Parameters Set")
dataFile = open(dataFileName, "w")

# Take the measurement

print("Taking Spectrum")
meas_time = float(gpibObj.query("ST?"))  # Determine the measurement time
time.sleep(0.1)
gpibObj.command("SWM2")  # Single Sweep Mode
time.sleep(0.1)
gpibObj.command("SWTRG")  # Trigger the Sweep
time.sleep(meas_time)  # Pause for the measurement
time.sleep(1)  # Add a little extra time to avoid pulling the plug too early
gpibObj.command("AUTO")  # Auto-Scale the display
time.sleep(0.1)

print("Getting Measurement Data")
HP4195A.getdata(
    gpibObj, dataFile, 2
)  # Downloads data. Last parameter=2 indicates spectrum analyzer mode
time.sleep(0.1)

dataFile.close()
gpibObj.close()
print("Done!")

if options.plotData:
    import gpibplot

    gpibplot.plotSPHP4195A(
        options.filename,
        options.title,
        xlog=options.xlog,
        ylog=options.ylog,
        psdunits=options.units,
    )
    raw_input("Press enter to quit:")
