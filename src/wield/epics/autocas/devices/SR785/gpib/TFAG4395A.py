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
import AG4395A
import termstatus


# Parse options
usage = """usage: %prog [options]

This program executes a network measurement using AG4395A.
Various measurement conditions can be set using options.
The measurement result will be saved in FILENAME.dat and the measurement parameters in FILENAME.par.
Optionally, it can plot the retrieved data using the gpibplot.py script.
"""

parser = optparse.OptionParser(usage=usage)
# Specify name of data file
parser.add_option(
    "-f",
    "--file",
    dest="filename",
    help="Output file name without an extension",
    default="test",
)
# Specify IP address of netGPIB device
parser.add_option(
    "-i", "--ip", dest="ipAddress", default="18.120.0.102", help="IP address/Host name"
)
# Set GPIB address
parser.add_option(
    "-a",
    "--address",
    dest="gpibAddress",
    type="int",
    default=10,
    help="GPIB device address",
)
# Select number of averages
parser.add_option(
    "-v",
    "--averaging",
    dest="numAvg",
    type="str",
    default="2",
    help="Number of averages",
)
# Switch to B/R Network meas
parser.add_option(
    "-B",
    "--networkBR",
    dest="netBR",
    default=False,
    action="store_true",
    help="What network are you looking at (A/R, B/R)? Specify with '-B'",
)
# Set sweep start freq
parser.add_option(
    "--st", "--start", dest="startF", type="str", default="1kHz", help="Start frequency"
)
# Set sweep end freq
parser.add_option(
    "--fin", "--end", dest="endF", type="str", default="2MHz", help="End frequency"
)
# Set Scan BW
parser.add_option(
    "--bw",
    "--Bandwidth",
    dest="BW",
    type="str",
    default="300Hz",
    help="Bandwidth. Changes number of points - max number of points is 801",
)
# Optional Auto BW
parser.add_option(
    "--autobw",
    dest="autoBW",
    default=False,
    action="store_true",
    help="autoBW. automatically chooses number of points",
)
# Set Source Power
parser.add_option(
    "-p", dest="pwr", type="str", default="0dBm", help="Source Power.  Specify in dBm"
)
# Optional linear sweep
parser.add_option(
    "--swlin",
    dest="sweeplin",
    default=False,
    action="store_true",
    help="Change to Linear Sweep",
)
# Enable Plotting
parser.add_option(
    "--plot",
    dest="plotData",
    default=False,
    action="store_true",
    help="Plot the downloaded data.",
)
# Set Plot title
parser.add_option(
    "--title",
    dest="title",
    type="string",
    default="",
    help="Title of the measurement. The given string will be written into the parameter file.",
)


(options, args) = parser.parse_args()

# create output directory if it doesn't exist yet
DirName = "/ligo/svncommon/Squeezer/Data/" + time.strftime("%Y-%m-%d", time.gmtime())

if not os.path.isdir(DirName):
    print >>sys.stderr, "Creating the output directory '%s'..." % DirName
    os.makedirs(DirName)


# Create a netGPIB class object
print("Connecting to " + str(options.ipAddress) + " ..."),
gpibObj = netgpib.netGPIB(options.ipAddress, options.gpibAddress, "\004", 0)
print("done.")

# File names
dataFileName = DirName + "/" + options.filename + ".dat"
paramFileName = DirName + "/" + options.filename + ".par"

print("Data will be written into " + dataFileName)
print("Parameters will be written into " + paramFileName)
print("Setting up parameters for the measurement")

from time import gmtime

gpibObj.command("PRES")  # Restore Default Settings
time.sleep(0.1)
gpibObj.command("NA")  # Sets to Network Analyzer measurement
time.sleep(0.1)
gpibObj.command("DUAC ON")  # Dual Displays
time.sleep(0.1)
gpibObj.command("POWE " + str(options.pwr))

# set the measurement parameters
gpibObj.command("CHAN1")
time.sleep(0.1)

if options.netBR:
    gpibObj.command("MEAS BR")  # B/R Network
    time.sleep(0.1)
else:
    gpibObj.command("MEAS AR")  # A/R Network
    time.sleep(0.1)

gpibObj.command("AVERFACT " + str(options.numAvg))  # Set up Averaging
time.sleep(0.1)
gpibObj.command("AVER OFF")
time.sleep(0.1)
gpibObj.command("FMT LOGM")  # Log Magnitude
time.sleep(0.1)
gpibObj.command("STAR " + str(options.startF))  # Start Frequency
time.sleep(0.1)
gpibObj.command("STOP " + str(options.endF))  # Stop Frequency
time.sleep(0.1)
gpibObj.command("BW " + str(options.BW))  # Resolution Bandwidth
time.sleep(0.1)
if options.autoBW:
    gpibObj.command("BWAUTO ON")
    time.sleep(0.1)

gpibObj.command("CHAN2")  # Set Up Channel 2
time.sleep(0.1)

if options.netBR:
    gpibObj.command("MEAS BR")  # B/R Network
    time.sleep(0.1)
else:
    gpibObj.command("MEAS AR")  # A/R Network

gpibObj.command("AVERFACT " + str(options.numAvg))
time.sleep(0.1)
gpibObj.command("AVER OFF")
time.sleep(0.1)
gpibObj.command("FMT PHAS")  # Phase Units
time.sleep(0.1)
gpibObj.command("PHAU DEG")  # Measure Phase in degrees
time.sleep(0.1)
gpibObj.command("STAR " + str(options.startF))  # Start Frequency
time.sleep(0.1)
gpibObj.command("STOP " + str(options.endF))  # End Frequency
time.sleep(0.1)
gpibObj.command("BW " + str(options.BW))  # Resolution Bandwidth
time.sleep(0.1)
if options.autoBW:
    gpibObj.command("BWAUTO ON")
    time.sleep(0.1)

if options.sweeplin:
    gpibObj.command("SWPT LINF")  # Linear Frequency Sweep
    time.sleep(0.1)
else:
    gpibObj.command("SWPT LOGF")  # Log Frequency Sweep
    time.sleep(0.1)

time.sleep(2)
print("Parameters set")
dataFile = open(dataFileName, "w")
paramFile = open(paramFileName, "w")
gpibObj.command("CHAN1")
time.sleep(0.1)
gpibObj.command("AVER ON")
time.sleep(0.1)
gpibObj.command("CHAN2")
time.sleep(0.1)
gpibObj.command("AVER ON")
time.sleep(0.1)
tim = gpibObj.query(
    "SWET?"
)  # Get time per sweep.  measurement time~ time_per_sweep*num_of_averages
tot_time = float(tim) * int(options.numAvg) + 0.4 * int(
    options.numAvg
)  # add some padding to account for time between sweeps
print("Run time is " + str(tot_time) + "s")
gpibObj.command("AVERREST")  # Start measurement
time.sleep(0.1)
gpibObj.command("CHAN1")
time.sleep(0.1)
gpibObj.command("AVERREST")
print("Running...")
time.sleep((tot_time))
a = gmtime()
date_time = "%02d/%02d, %02d:%02d:%02d" % (a[1], a[2], a[3], a[4], a[5])
print("Done")


print("Getting data (if this takes more than ~15s it probably crashed, try again)")
AG4395A.getdata(gpibObj, dataFile, paramFile)
time.sleep(0.1)
# Deal with an empty title
if options.title == "":
    options.title = options.filename
time.sleep(0.1)
print("Print parameters")
# Parameters
paramFile.write("Title: " + options.title + "\n")
paramFile.write(
    "############## Spectra measurement parameters #########################\n"
)
fSpan = gpibObj.query("SPAN?")
# fSpan=fSpan[:-1]
paramFile.write("Frequency Span: " + fSpan + "\n")

fStart = gpibObj.query("STAR?")
paramFile.write("Start Frequency: " + fStart + "\n")

fStop = gpibObj.query("STOP?")
paramFile.write("Stop Frequency: " + fStop + "\n")

fRes = int(gpibObj.query("POIN?"))
paramFile.write("Number of Points: " + str(fRes) + "\n")

nAvg = int(gpibObj.query("AVERFACT?"))
paramFile.write("Number of Averages: " + str(nAvg) + "\n")


paramFile.write(
    "####################################################################\n"
)

AG4395A.getparam(gpibObj, options.filename, dataFile, paramFile)

dataFile.close()
paramFile.close()
gpibObj.close()
print("Done!")

if options.plotData:
    import gpibplot

    gpibplot.plotTFAG4395A(DirName + "/" + options.filename, options.title)
    raw_input("Press enter to quit:")
