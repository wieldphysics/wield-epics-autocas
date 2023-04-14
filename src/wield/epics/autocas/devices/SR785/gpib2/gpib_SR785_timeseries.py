#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@mit.edu>
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

This program measures time series and histograms of signals coming to an SR785.
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
    "-t",
    "--time",
    dest="time",
    default=1.0,
    type="float",
    help="Measurement time in sec.",
)
parser.add_option(
    "-n",
    "--numbin",
    dest="nbin",
    type="int",
    default=256,
    help="Number of bins for histograms",
)
parser.add_option(
    "-l",
    "--hlen",
    dest="hlen",
    type="string",
    default="1",
    help="Measurement length for histograms in sec.",
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
parser.add_option(
    "--memo",
    dest="memo",
    type="string",
    default="",
    help="Use this option to note miscellaneous things.",
)

(options, args) = parser.parse_args()

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

##%%
# Prepare for the time series measurement

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
##%%
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
##%%
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
##%%
# Common setup for both displays
gpibObj.command("MGRP2,5")  # Measurement Group = Time/Histogram
gpibObj.command("ISRC1")  # Input = Analog
gpibObj.command("FBAS2,1")  # Base Frequency = 102.4kHz
##%%
fspan = 25.0 / (64.0 * options.time / 1000.0)
gpibObj.command("FSPN2," + str(fspan))  # Frequency Span
gpibObj.command("HLEN2," + options.hlen)  # Histogram length

i = int(math.floor(math.log(options.nbin, 2) - 2))
if i < 0:
    i = 0
gpibObj.command("HBIN2," + str(i))  # Number of histogram bins
gpibObj.command("HRPT2,0")  # Turn off repeat

##%%
# Set up each display
for disp in range(numDisp):
    gpibObj.command("ACTD" + str(disp))  # Change active display
    time.sleep(0.1)
    gpibObj.command("MEAS" + str(disp) + "," + str(78 + disp))  # 78:Time1, 79:Time2
    time.sleep(0.1)
    gpibObj.command("VIEW" + str(disp) + ",1")  # Linear Mag
    time.sleep(0.1)
    gpibObj.command("UNDB" + str(disp) + ",0")  # dB OFF
    time.sleep(0.1)
    gpibObj.command("UNPK" + str(disp) + ",1")  # Peak unit Pk
    time.sleep(0.1)
    gpibObj.command("PSDU" + str(disp) + ",0")  # PSD OFF
    time.sleep(0.1)
    gpibObj.command("DISP" + str(disp) + ",1")  # Live display on

##%%
# Common setup
gpibObj.command("FAVG2,0")  # Averaging Off
time.sleep(0.1)

gpibObj.command("FWIN2,0")  # Uniform window function
##%%
time.sleep(1)

# Start measurement
print "Measurement started"
sys.stdout.flush()
gpibObj.command("STRT")  # Start measurement
time.sleep(0.1)
# Wait for the measurement to end
measuring = True
while measuring:
    time.sleep(0.1)
    # Get status
    measuring = not int(gpibObj.query("DSPS?1"))
print ("done")

gpibObj.command("ASCL0")  # Auto scale
gpibObj.command("ASCL1")  # Auto scale


# Download Data
# pdb.set_trace()
time.sleep(0.5)

timeSeries = []
for disp in range(numDisp):
    print ("Downloading data from display #" + str(disp))
    (t, d) = SR785_get_data.downloadData(gpibObj, disp)
    timeSeries.append([t, d])

# Change the measurement to histograms
print ("Switching to Histgram display")
hist = []
for disp in range(numDisp):
    gpibObj.command("ACTD" + str(disp))  # Change active display
    time.sleep(0.1)
    gpibObj.command(
        "MEAS" + str(disp) + "," + str(72 + disp)
    )  # 72:Histogram 1, 73:Histogram 2
    time.sleep(0.1)
    print ("Downloading data from display #" + str(disp))
    (v, d) = SR785_get_data.downloadData(gpibObj, disp)
    hist.append([v, d])

# Open files
dataFile = open(dataFileName, "w")
paramFile = open(paramFileName, "w")

# Write data to file
print ("Writing data into the data file ...")
for i in range(len(timeSeries)):
    dataFile.write("#Time series " + str(i + 1) + "\n")
    for j in range(len(timeSeries[i][0])):
        dataFile.write(timeSeries[i][0][j] + " " + timeSeries[i][1][j] + "\n")

for i in range(len(hist)):
    dataFile.write("#Histogram " + str(i + 1) + "\n")
    for j in range(len(hist[i][0])):
        dataFile.write(hist[i][0][j] + " " + hist[i][1][j] + "\n")

# Deal with an empty title
if options.title == "":
    options.title = options.filename

# Parameters
paramFile.write("Title: " + options.title + "\n")
paramFile.write("Memo: " + options.memo + "\n")
paramFile.write("#========= Time series measurement parameters =========\n")

SR785_get_data.getparam(gpibObj, options.filename, dataFile, paramFile)

dataFile.close()
paramFile.close()
gpibObj.close()

if options.plotData:
    import gpibplot

    gpibplot.plotSR785(options.filename)
    raw_input("Press enter to quit:")
