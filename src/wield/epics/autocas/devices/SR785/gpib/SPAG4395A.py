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

This program executes a spectral measurement using AG4395A.
Various measurement conditions can be set using options.
The measurement result will be saved in FILENAME.dat and the measurement parameters in FILENAME.par.
Optionally, it can plot the retrieved data using the plotgpibdata.py script.
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
    "-d",
    "--dualchannel",
    dest="dual",
    default=False,
    action="store_true",
    help="Set to dual channel mode.",
)

# parser.add_option("--ch", "--channel",
#                  dest="chan", type="str", default="R",
#                  help="What channel are you looking at (R, A, B)")

parser.add_option(
    "-R",
    "--channelR",
    dest="chanR",
    default=True,
    action="store_true",
    help="What channel are you looking at (R, A, B)? Specify with '-R'",
)

parser.add_option(
    "-A",
    "--channelA",
    dest="chanA",
    default=False,
    action="store_true",
    help="What channel are you looking at (R, A, B)? Specify with '-A'",
)

parser.add_option(
    "-B",
    "--channelB",
    dest="chanB",
    default=False,
    action="store_true",
    help="What channel are you looking at (R, A, B)? Specify with '-B'",
)

parser.add_option(
    "-v",
    "--averaging",
    dest="numAvg",
    type="str",
    default="20",
    help="Number of averages",
)

parser.add_option(
    "--st", "--start", dest="startF", type="str", default="1kHz", help="Start frequency"
)

parser.add_option(
    "--fin", "--end", dest="endF", type="str", default="2MHz", help="End frequency"
)

parser.add_option(
    "--bw",
    "--Bandwidth",
    dest="BW",
    type="str",
    default="300Hz",
    help="Bandwidth. Changes number of points - max number of points is 801",
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

# create output directory if it doesn't exist yet
DirName = "/ligo/h1sqz/data/" + time.strftime("%Y-%m-%d", time.gmtime())

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

gpibObj.command("PRES")
time.sleep(0.1)
gpibObj.command("SA")
time.sleep(0.1)


if options.dual:
    duac = "ON"
    if options.chanR:
        MS = "R"
        gpibObj.command("CHAN1")
        gpibObj.command("MEAS " + str(MS))
        if options.chanA:
            MS = "A"
            gpibObj.command("CHAN2")
            gpibObj.command("MEAS " + str(MS))
            if options.chanB:
                MS = "B"
                gpibObj.command("CHAN2")
                gpibObj.command("MEAS " + str(MS))
    elif options.chanB:
        MS = "B"
        gpibObj.command("CHAN1")
        gpibObj.command("MEAS " + str(MS))
        if options.chanA:
            MS = "A"
            gpibObj.command("CHAN2")
            gpibObj.command("MEAS " + str(MS))
    gpibObj.command("DUAC " + str(duac))
    time.sleep(0.1)
    gpibObj.command("CHAN1")
    time.sleep(0.1)
    gpibObj.command("AVERFACT " + str(options.numAvg))
    time.sleep(0.1)
    gpibObj.command("AVER OFF")
    gpibObj.command("STAR " + str(options.startF))
    time.sleep(0.1)
    gpibObj.command("STOP " + str(options.endF))
    time.sleep(0.1)
    gpibObj.command("BW " + str(options.BW))
    time.sleep(0.1)
    if options.units:
        gpibObj.command("FMT NOISE")
        time.sleep(0.1)
        gpibObj.command("SAUNIT V")
        time.sleep(0.1)
    gpibObj.command("CHAN2")
    time.sleep(0.1)
    gpibObj.command("AVERFACT " + str(options.numAvg))
    time.sleep(0.1)
    gpibObj.command("AVER OFF")
    gpibObj.command("STAR " + str(options.startF))
    time.sleep(0.1)
    gpibObj.command("STOP " + str(options.endF))
    time.sleep(0.1)
    gpibObj.command("BW " + str(options.BW))
    time.sleep(0.1)
    if options.units:
        gpibObj.command("FMT NOISE")
        time.sleep(0.1)
        gpibObj.command("SAUNIT V")
        time.sleep(0.1)
    time.sleep(5)
    print("Parameters set")
    dataFile = open(dataFileName, "w")
    paramFile = open(paramFileName, "w")
    gpibObj.command("AVER ON")
    time.sleep(0.1)
    gpibObj.command("CHAN2")
    time.sleep(0.1)
    gpibObj.command("AVER ON")
    tim = gpibObj.query("SWET?")
    tot_time = float(tim) * int(options.numAvg) + int(options.numAvg)
    print("Run time is " + str(tot_time) + "s")
    gpibObj.command("AVERREST")  # Start measurement
    gpibObj.command("CHAN1")
    gpibObj.command("AVERREST")
    print("Running...")
    time.sleep((tot_time))
    a = gmtime()
    date_time = "%02d/%02d, %02d:%02d:%02d" % (a[1], a[2], a[3], a[4], a[5])
    print("Done")
else:
    if options.chanA == 1:
        MS = "A"
    elif options.chanB == 1:
        MS = "B"
    else:
        MS = "R"
    gpibObj.command("MEAS " + str(MS))
    time.sleep(0.1)
    gpibObj.command("AVERFACT " + str(options.numAvg))
    time.sleep(0.1)
    gpibObj.command("AVER OFF")
    gpibObj.command("STAR " + str(options.startF))
    time.sleep(0.1)
    gpibObj.command("STOP " + str(options.endF))
    time.sleep(0.1)
    gpibObj.command("BW " + str(options.BW))
    time.sleep(0.1)
    if options.units:
        gpibObj.command("FMT NOISE")
        time.sleep(0.1)
        gpibObj.command("SAUNIT V")
        time.sleep(0.1)
    time.sleep(5)
    print("Parameters set")
    gpibObj.command("AVER ON")
    dataFile = open(dataFileName, "w")
    paramFile = open(paramFileName, "w")
    tim = gpibObj.query("SWET?")
    tot_time = float(tim) * int(options.numAvg) + int(options.numAvg)
    print("Run time is " + str(tot_time) + "s")
    gpibObj.command("AVERREST")  # Start measurement
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

    gpibplot.plotSPAG4395A(
        DirName + "/" + options.filename,
        options.title,
        xlog=options.xlog,
        ylog=options.ylog,
        psdunits=options.units,
    )
    raw_input("Press enter to quit:")
