#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import re
import sys
import math
import optparse
import time
import pdb
from libholo.gpib_controllers.remote_instrument_control.netgpibdata import netgpib
from libholo.gpib_controllers.remote_instrument_control.SR785 import SR785_get_data
from libholo.gpib_controllers.remote_instrument_control.netgpibdata import termstatus

# Parse options
usage = """usage: %prog [options]

This program remotely executes a spectrum measurement using SR785.
Various measurement conditions can be set using options.
The measurement result will be saved in FILENAME.dat and the measurement parameters in FILENAME.par.
Optionally, it can plot the retrieved data. You need matplotlib and numpy modules to plot the data.
"""
parser = optparse.OptionParser(usage=usage)
parser.add_option(
    "-f",
    "--file",
    dest="filename",
    help="Output file name without an extension",
    default="data",
)
parser.add_option(
    "-i", "--ip", dest="ipAddress", default="gpib01", help="IP address/Host name"
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
    "-b",
    "--bandwidth",
    dest="bandWidth",
    default="100kHz",
    help="Bandwidth. You can use mHz,Hz or kHz units.",
)
parser.add_option(
    "-n",
    "--numpoints",
    dest="numOfPoints",
    type="int",
    default="100",
    help="Number of frequency points",
)
parser.add_option(
    "-v",
    "--averaging",
    dest="numAvg",
    type="int",
    default="20",
    help="Number of averages",
)
parser.add_option(
    "--avgmode",
    dest="avgMode",
    type="string",
    default="RMS",
    help="Averaging mode: None, Vector, RMS or PeakHold",
)
parser.add_option(
    "-d",
    "--dualchannel",
    action="store_true",
    dest="dual",
    help="Set to the dual channel mode.",
)
parser.add_option(
    "--ic1",
    dest="inputCoupling1",
    type="string",
    default="DC",
    help="CH1 input coupling. DC or AC",
)
parser.add_option(
    "--ic2",
    dest="inputCoupling2",
    type="string",
    default="DC",
    help="CH2 input coupling. DC or AC",
)
parser.add_option(
    "--ig1",
    dest="inputGND1",
    type="string",
    default="Float",
    help="CH1 input grounding. Float or Ground",
)
parser.add_option(
    "--ig2",
    dest="inputGND2",
    type="string",
    default="Float",
    help="CH2 input grounding. Float or Ground",
)
parser.add_option(
    "-w",
    "--window",
    dest="windowFunc",
    type="string",
    default="Hanning",
    help="Window function: Uniform, Flattop, Hanning, BMH, Kaiser, Force/Exponential, User, [-T/2,T/2],[0,T/2] or [-T/4,T/4]",
)
parser.add_option(
    "--plot",
    dest="plotData",
    default=False,
    action="store_true",
    help="Plot the downloaded data.",
)
parser.add_option(
    "--xlin",
    dest="xlog",
    default=True,
    action="store_false",
    help="Plot with linear x axis",
)
parser.add_option(
    "--ylin",
    dest="ylog",
    default=None,
    action="store_false",
    help="Plot with linear y axis",
)
parser.add_option(
    "--xlog",
    dest="xlog",
    default=True,
    action="store_true",
    help="Plot with logarithmic x axis",
)
parser.add_option(
    "--ylog",
    dest="ylog",
    default=None,
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
parser.add_option(
    "--memo",
    dest="memo",
    type="string",
    default="",
    help="Use this option to note miscellaneous things.",
)


(options, args) = parser.parse_args()

# Convert number of points into available resolution
if options.numOfPoints <= 100:
    fRes = 0  # Resolution is 100 points
elif options.numOfPoints <= 200:
    fRes = 1  # Resolution is 200 points
elif options.numOfPoints <= 400:
    fRes = 2  # Resolution is 400 points
else:
    fRes = 3  # Resolution is 800 points


# Create a netGPIB class object
print ("Connecting to " + str(options.ipAddress) + " ..."),
gpibObj = netgpib.netGPIB(options.ipAddress, options.gpibAddress, "\004", 0)
print ("done.")

# File names
dataFileName = options.filename + ".dat"
paramFileName = options.filename + ".par"

print ("Data will be written into " + dataFileName)
print ("Parameters will be written into " + paramFileName)
print ("Setting up parameters for the measurement")

# pdb.set_trace()
#


# Prepare for the TF measurement

# Set output to GPIB
gpibObj.command("OUTX0")
time.sleep(0.1)

# Set measurement parameters
if options.dual:
    gpibObj.command("DFMT1")  # Dual display
    time.sleep(0.1)
    numDisp = 2
else:
    gpibObj.command("DFMT0")  # Dual display
    time.sleep(0.1)
    numDisp = 1

# Input setup
if options.inputCoupling1 == "AC":
    icp1 = "1"
else:
    icp1 = "0"
gpibObj.command("I1CP" + icp1)  # CH1 Input Coupling
time.sleep(0.1)

if options.inputCoupling2 == "AC":
    icp2 = "1"
else:
    icp2 = "0"
gpibObj.command("I2CP" + icp2)  # CH2 Input Coupling
time.sleep(0.1)

if options.inputGND1 == "Float":
    igd1 = "0"
else:
    igd1 = "1"
gpibObj.command("I1GD" + igd1)  # CH1 Input GND
time.sleep(0.1)

if options.inputGND2 == "Float":
    igd2 = "0"
else:
    igd2 = "1"
gpibObj.command("I2GD" + igd2)  # CH2 Input GND
time.sleep(0.1)

gpibObj.command("A1RG0")  # AutoRange Off
time.sleep(0.1)
gpibObj.command("A2RG0")  # AutoRange Off
time.sleep(0.1)
gpibObj.command("I1AR0")  # AutoRange Up Only
time.sleep(0.1)
gpibObj.command("I2AR0")  # AutoRange Up Only
time.sleep(0.1)
gpibObj.command("A1RG1")  # AutoRange On
time.sleep(0.1)
gpibObj.command("A2RG1")  # AutoRange On
time.sleep(0.1)

gpibObj.command("I1AF1")  # Anti-Aliasing filter On
time.sleep(0.1)
gpibObj.command("I2AF1")  # Anti-Aliasing filter On
time.sleep(0.1)

# Common setup for both displays
gpibObj.command("MGRP2,0")  # Measurement Group = FFT
gpibObj.command("ISRC1")  # Input = Analog
gpibObj.command("FBAS2,1")  # Base Frequency = 102.4kHz

# Set up each display
for disp in range(numDisp):

    gpibObj.command("ACTD" + str(disp))  # Change active display
    time.sleep(0.1)
    gpibObj.command("MEAS" + str(disp) + "," + str(disp))  # 0:FFT1, 1:FFT2
    time.sleep(0.1)
    gpibObj.command("VIEW" + str(disp) + ",0")  # Log Magnitude
    time.sleep(0.1)
    gpibObj.command("UNDB" + str(disp) + ",0")  # dB OFF
    time.sleep(0.1)
    gpibObj.command("UNPK" + str(disp) + ",2")  # Vrms
    time.sleep(0.1)
    gpibObj.command("PSDU" + str(disp) + ",1")  # PSD ON
    time.sleep(0.1)
    gpibObj.command("DISP" + str(disp) + ",1")  # Live display on

# Common setup
gpibObj.command("FSPN2," + options.bandWidth)  # Frequency span
time.sleep(0.1)
gpibObj.command("FLIN2," + str(fRes))  # Frequency resolution
time.sleep(0.1)
gpibObj.command("FAVG2,1")  # Averaging On
time.sleep(0.1)

avgModDict = {"None": 0, "Vector": 1, "RMS": 2, "PeakHold": 3}
if options.avgMode in avgModDict:
    avgModID = avgModDict[options.avgMode]
else:
    avgModID = 2
gpibObj.command("FAVM2," + str(avgModID))  # Averaging mode
time.sleep(0.1)

gpibObj.command("FAVT2,0")  # Averaging Type = Linear
time.sleep(0.1)
gpibObj.command("FREJ2,1")  # Overload Reject On
time.sleep(0.1)
gpibObj.command("FAVN2," + str(options.numAvg))  # Number of Averaging
time.sleep(0.1)

winFuncDict = {
    "Uniform": 0,
    "Flattop": 1,
    "Hanning": 2,
    "BMH": 3,
    "Kaiser": 4,
    "Force/Exponential": 5,
    "User": 6,
    "[-T/2,T/2]": 7,
    "[0,T/2]": 8,
    "[-T/4,T/4]": 9,
}
if options.windowFunc in winFuncDict:
    winFuncID = winFuncDict[options.windowFunc]
else:
    winFuncID = 2
gpibObj.command("FWIN2," + str(winFuncID))  # Window function

time.sleep(1)
# Start measurement
print "Measurement started"
sys.stdout.flush()
gpibObj.command("STRT")  # Start measurement
time.sleep(0.1)
# Wait for the measurement to end
measuring = True
avg = 0
print "Averaging completed:",
avgStatus = termstatus.statusTxt("0")
while measuring:
    # Get status
    measuring = not int(gpibObj.query("DSPS?1"))
    avg = int(gpibObj.query("NAVG?0"))
    avgStatus.update(str(avg))

    # if options.numAvg <= avg:
    #    measuring = False
    time.sleep(0.3)

a = int(gpibObj.query("NAVG?0"))
avgStatus.end(str(a))
print ("done")

gpibObj.command("ASCL0")  # Auto scale
gpibObj.command("ASCL1")  # Auto scale


# Download Data
# pdb.set_trace()
time.sleep(0.5)

dataFile = open(dataFileName, "w")
paramFile = open(paramFileName, "w")

SR785_get_data.getdata(gpibObj, dataFile, paramFile)

# Deal with an empty title
if options.title == "":
    options.title = options.filename

# Parameters
paramFile.write("Title: " + options.title + "\n")
paramFile.write("Memo: " + options.memo + "\n")
paramFile.write(
    "############## Spectra measurement parameters #########################\n"
)
fSpan = gpibObj.query("FSPN?0")
fSpan = fSpan[:-1]
paramFile.write("Frequency Span: " + fSpan + "\n")

fRes = int(gpibObj.query("FLIN?0"))
fRes = {0: 100, 1: 200, 2: 400, 3: 800}[fRes]
paramFile.write("Frequency Resolution: " + str(fRes) + "\n")

nAvg = int(gpibObj.query("NAVG?0"))
paramFile.write("Number of Averages: " + str(nAvg) + "\n")

avgMode = {0: "None", 1: "Vector", 2: "RMS", 3: "PeakHold"}[
    int(gpibObj.query("FAVM?0"))
]
paramFile.write("Averaging Mode: " + avgMode + "\n")

winFunc = {
    0: "Uniform",
    1: "Flattop",
    2: "Hanning",
    3: "BMH",
    4: "Kaiser",
    5: "Force/Exponential",
    6: "User",
    7: "[-T/2,T/2]",
    8: "[0,T/2]",
    9: "[-T/4,T/4]",
}[int(gpibObj.query("FWIN?0"))]
paramFile.write("Window function: " + winFunc + "\n")

paramFile.write(
    "####################################################################\n"
)

SR785_get_data.getparam(gpibObj, options.filename, dataFile, paramFile)

dataFile.close()
paramFile.close()
gpibObj.close()

if options.plotData:
    import gpibplot

    gpibplot.plotSR785(options.filename, xlog=options.xlog, ylog=options.ylog)
    raw_input("Press enter to quit:")
