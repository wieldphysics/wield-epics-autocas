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
import optparse
import struct
import time
from math import log10
import netgpib

# Parse options
usage = """usage: %prog [options]

This program executes a transfer function measurement using SR785.
Various measurement conditions can be set using options.
The measurement result will be saved in FILENAME.dat and the measurement parameters in FILENAME.par.
Optionally, it can plot the retrieved data. You need matplotlib and numpy modules to plot the data.
"""

filetime = time.strftime(
    "%Y-%m-%d.%H%M%S", time.gmtime()
)  # Date string for data file (default

parser = optparse.OptionParser(usage=usage)
parser.add_option(
    "-f",
    "--file",
    dest="filename",
    help="Output file name without an extension",
    default=filetime,
)
parser.add_option(
    "-i", "--ip", dest="ipAddress", default="18.120.0.112", help="IP address/Host name"
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
    "-r",
    "--skipreset",
    dest="skipReset",
    action="store_true",
    default=False,
    help="If given, the code does not reset the instrument at the beginning.",
)
parser.add_option(
    "-s",
    "--startfreq",
    dest="startFreq",
    default="100kHz",
    help="Start frequency. Units can be mHz, Hz or kHz.",
)
parser.add_option(
    "-e",
    "--stopfreq",
    dest="stopFreq",
    default="100Hz",
    help="Stop frequency. Units can be mHz, Hz or kHz.",
)
parser.add_option(
    "-n",
    "--numpoints",
    dest="numOfPoints",
    type="int",
    default="200",
    help="Number of frequency points",
)
parser.add_option(
    "--sweep",
    dest="sweepType",
    type="string",
    default="Log",
    help="Sweep type: Log or Linear (default: Log)",
)
parser.add_option(
    "-x", "--excamp", dest="excAmp", default="100mV", help="Excitation amplitude"
)
parser.add_option(
    "-c",
    "--settlecycle",
    dest="settleCycles",
    type="int",
    default="10",
    help="Settle cycles",
)
parser.add_option(
    "-t",
    "--intcycle",
    dest="intCycles",
    type="int",
    default="20",
    help="Integration cycles",
)
parser.add_option(
    "--ic1",
    dest="inputCoupling1",
    type="string",
    default="DC",
    help="CH1 input coupling. DC or AC (default:DC)",
)
parser.add_option(
    "--ic2",
    dest="inputCoupling2",
    type="string",
    default="DC",
    help="CH2 input coupling. DC or AC (default:DC)",
)
parser.add_option(
    "--ig1",
    dest="inputGND1",
    type="string",
    default="Float",
    help="CH1 input grounding. Float or Ground (default:Float)",
)
parser.add_option(
    "--ig2",
    dest="inputGND2",
    type="string",
    default="Float",
    help="CH2 input grounding. Float or Ground (default:Float)",
)
parser.add_option(
    "--inputrange1",
    dest="inputRange1",
    default="",
    help="CH1 input range (default unit is dBVpk). If not given, auto-range will be used.",
)
parser.add_option(
    "--inputrange2",
    dest="inputRange2",
    default="",
    help="CH2 input range (default unit is dBVpk). If not given, auto-range will be used.",
)
parser.add_option(
    "--armode",
    dest="arMode",
    type="string",
    default="UpOnly",
    help="Auto range mode: UpOnly or Tracking (default: UpOnly). This option will be ignored if input range is set.",
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

## input sanity check
sf = (
    options.startFreq.replace("Hz", "")
    .replace("k", "E3")
    .replace("m", "E-3")
    .replace("u", "E-6")
)
try:
    float(sf)
except ValueError:
    print >> sys.stderr, "Error: --startfreq must be a number (optionally) associated with unit kHz, Hz, mHz or uHz."
    sys.exit(1)
if float(sf) < 0.001 or float(sf) > 102400:
    print >> sys.stderr, "Error: --startfreq must be between 0.0001Hz and 102400Hz."
    sys.exit(1)

ef = (
    options.stopFreq.replace("Hz", "")
    .replace("k", "E3")
    .replace("m", "E-3")
    .replace("u", "E-6")
)
try:
    float(ef)
except ValueError:
    print >> sys.stderr, "Error: --stopfreq must be a number (optionally) associated with unit kHz, Hz, mHz or uHz."
    sys.exit(1)
if float(ef) < 0.001 or float(ef) > 102400:
    print >> sys.stderr, "Error: --stopfreq must be between 0.0001Hz and 102400Hz."
    sys.exit(1)

if options.numOfPoints > 2047 or options.numOfPoints < 10:
    print >> sys.stderr, "Error: --numofpoints must be between 10 and 2047."
    sys.exit(1)

if options.sweepType not in ("Log", "Linear"):
    print >> sys.stderr, "Error: --sweep must be either 'Log' or 'Linear'."
    sys.exit(1)

# Deal with an empty title
if options.title == "":
    options.title = options.filename

# Create a netGPIB class object
print ("Connecting to " + str(options.ipAddress) + " ..."),
gpibObj = netgpib.netGPIB(options.ipAddress, options.gpibAddress, eot="\004")
gpibObj.connect()
print ("done.")

# clear all status word
gpibObj.command("*CLS")
# Set output to GPIB
gpibObj.command("OUTX0")
# set the Standard Event enable register to catch EXE and CME
# Command errors will set the ESB bit in the Serial Poll status word
gpibObj.command("*ESE 48")  # set bits 4 and 5

# force reset
if not options.skipReset:
    print ("Resetting SR785...")
    gpibObj.command("*RST")

# Print IDN
print "Instrument ID: ",
idnString = gpibObj.query("*IDN?")
print idnString[:-1]
# sanity check for query sync
if idnString[:31] != "Stanford_Research_Systems,SR785":
    print >> sys.stderr, "Error: query/return mismatch or the device is not SR785."
    print >> sys.stderr, "Please reset the device (i.e. do not use --skipreset option) and see if the problem goes away."
    sys.exit(1)


# File names
dataFileName = options.filename + ".dat"

print ("Data will be written into " + dataFileName)
print ("Setting up parameters for the measurement")

# Prepare for the TF measurement

# Input setup
if options.inputCoupling1 == "AC":
    icp1 = "1"
else:
    icp1 = "0"
gpibObj.command("I1CP" + icp1)  # CH1 Input Coupling

if options.inputCoupling2 == "AC":
    icp2 = "1"
else:
    icp2 = "0"
gpibObj.command("I2CP" + icp2)  # CH2 Input Coupling

if options.inputGND1 == "Float":
    igd1 = "0"
else:
    igd1 = "1"
gpibObj.command("I1GD" + igd1)  # CH1 Input GND

if options.inputGND2 == "Float":
    igd2 = "0"
else:
    igd2 = "1"
gpibObj.command("I2GD" + igd2)  # CH2 Input GND

gpibObj.command("A1RG0")  # AutoRange Off
gpibObj.command("A2RG0")  # AutoRange Off
if options.arMode == "Tracking":
    arModeID = "1"
else:
    arModeID = "0"
if options.inputRange1 != "":
    gpibObj.command("I1RG" + options.inputRange1)
else:
    gpibObj.command("I1AR" + arModeID)  # Auto Range Mode
    gpibObj.command("A1RG1")  # AutoRange On
if options.inputRange2 != "":
    gpibObj.command("I2RG" + options.inputRange2)
else:
    gpibObj.command("I2AR" + arModeID)  # Auto Range Mode
    gpibObj.command("A2RG1")  # AutoRange On
if options.inputRange1 == "" or options.inputRange2 == "":
    print "Auto-ranging..."
    time.sleep(5)

gpibObj.command("I1AF1")  # Anti-Aliasing filter On
gpibObj.command("I2AF1")  # Anti-Aliasing filter On

# Set measurement parameters
gpibObj.command("DFMT1")  # Dual display
gpibObj.command("ACTD0")  # Active display 0

gpibObj.command("MGRP2,3")  # Measurement Group = Swept Sine
gpibObj.command("MEAS2,47")  # Frequency Resp
gpibObj.command("VIEW0,0")  # Disp 0 = LogMag
gpibObj.command("VIEW1,5")  # Dsip 1 = Phase
gpibObj.command("UNDB0,1")  # dB ON
gpibObj.command("UNPK0,0")  # PK Unit Off
gpibObj.command("UNDB1,0")  # dB OFF
gpibObj.command("UNPK1,0")  # PK Unit Off
gpibObj.command("UNPH1,0")  # Phase Unit deg.
gpibObj.command("DISP0,1")  # Live display on
gpibObj.command("DISP1,1")  # Live display on
gpibObj.command("SSCY2," + str(options.settleCycles))  # Settle cycles
gpibObj.command("SICY2," + str(options.intCycles))  # Integration cycles
gpibObj.command("SSTR2," + options.startFreq)  # Start frequency
gpibObj.command("SSTP2," + options.stopFreq)  # Stop frequency
gpibObj.command("SNPS2," + str(options.numOfPoints))  # Number of points
gpibObj.command("SRPT2,0")  # Single shot moede
if options.sweepType == "Linear":
    sweepTypeID = "0"
else:
    sweepTypeID = "1"
gpibObj.command("SSTY2," + sweepTypeID)  # Sweep Type
gpibObj.command("SSAM" + options.excAmp)  # Source Amplitude

# Start measurement
print "Transfer function measurement started:",
sys.stdout.flush()
numPoints = int(gpibObj.query("SNPS?0"))  # Number of points
gpibObj.command("STRT")  # Source Amplitude

# Wait for the measurement to end
measuring = True
percentage = 0
accomplished = 0
print "0%",
sys.stdout.flush()
txtlen = 2
while measuring:
    # Get status
    measuring = not int(gpibObj.query("DSPS?4"))
    a = int(gpibObj.query("SSFR?"))
    percentage = int(100 * a / numPoints)
    print "\010" + "\010" * txtlen + "%d%%" % percentage,
    sys.stdout.flush()
    txtlen = len(str(percentage)) + 1
    accomplished = percentage
    time.sleep(0.3)

print "\010" + "\010" * txtlen + "100%"
sys.stdout.flush()

# Collect Data
bData = []
units = []
measGrp = []
measurement = []
view = []

for disp in range(2):
    print ("Downloading data from display #" + str(disp))
    numPoint = int(gpibObj.query("DSPN?" + str(disp)))
    startF = float(gpibObj.query("SSTR?%d" % disp))
    endF = float(gpibObj.query("SSTP?%d" % disp))
    # 2048 points x 4 bytes/point = 8192 is the maximum buffer needed
    bData.append(gpibObj.query("DSPB?" + str(disp), buf=8192, IFCCheck=False))
    gpibObj.waitIFC()
    units.append(gpibObj.query("UNIT?%d" % disp)[:-1])
    # query params / sanity check
    if int(gpibObj.query("MGRP?" + str(disp))) == 03:
        measGrp.append("Swept Sine")
    else:
        print >> sys.stderr, "Error: Measurement group is not set to Swept Sine."
        sys.exit(1)
    i = int(gpibObj.query("MEAS?" + str(disp)))
    if i == 47:
        measurement.append("Frequency Response")
    else:
        print >> sys.stderr, "Error: Measurement is not Frequency Response."
        sys.exit(1)
    i = int(gpibObj.query("VIEW?" + str(disp)))
    view.append(
        {
            0: "Log Magnitude",
            1: "Linear Magnitude",
            2: "Magnitude Squared",
            3: "Real Part",
            4: "Imaginary Part",
            5: "Phase",
            6: "Unwrapped Phase",
            7: "Nyquist",
            8: "Nichols",
        }[i]
    )


## get other parameters
print "Collecting parameters..."
# Input Source
i = int(gpibObj.query("ISRC?"))
inputSource = {0: "Analog", 1: "Capture"}[i]

# Input Mode
i = int(gpibObj.query("I1MD?"))
CH1inputMode = {0: "Single ended", 1: "Differential"}[i]

i = int(gpibObj.query("I2MD?"))
CH2inputMode = {0: "Single ended", 1: "Differential"}[i]

# Grounding
i = int(gpibObj.query("I1GD?"))
CH1Grounding = {0: "Float", 1: "Grounded"}[i]

i = int(gpibObj.query("I2GD?"))
CH2Grounding = {0: "Float", 1: "Grounded"}[i]

# Coupling
i = int(gpibObj.query("I1CP?"))
CH1Coupling = {0: "DC", 1: "AC", 2: "ICP"}[i]

i = int(gpibObj.query("I2CP?"))
CH2Coupling = {0: "DC", 1: "AC", 2: "ICP"}[i]

# Input Range
result = gpibObj.query("I1RG?")
match = re.search(r"^\s*([-+\d]*),.*", result)
CH1Range = str(float(match.group(1)))
match = re.search(r"\d,(\d)", result)
i = int(match.group(1))
CH1Range = (
    CH1Range
    + {
        0: "dBVpk",
        1: "dBVpp",
        2: "dBVrms",
        3: "Vpk",
        4: "Vpp",
        5: "Vrms",
        6: "dBEUpk",
        7: "dBEUpp",
        8: "dBEUrms",
        9: "EUpk",
        10: "EUpp",
        11: "EUrms",
    }[i]
)

result = gpibObj.query("I2RG?")
match = re.search(r"^\s*([-+\d]*),.*", result)
CH2Range = str(float(match.group(1)))
match = re.search(r"\d,(\d)", result)
i = int(match.group(1))
CH2Range = (
    CH2Range
    + {
        0: "dBVpk",
        1: "dBVpp",
        2: "dBVrms",
        3: "Vpk",
        4: "Vpp",
        5: "Vrms",
        6: "dBEUpk",
        7: "dBEUpp",
        8: "dBEUrms",
        9: "EUpk",
        10: "EUpp",
        11: "EUrms",
    }[i]
)

# Auto Range
i = int(gpibObj.query("A1RG?"))
CH1AutoRange = {0: "Off", 1: "On"}[i]
i = int(gpibObj.query("I1AR?"))
CH1AutoRangeMode = {0: "Up Only", 1: "Tracking"}[i]

i = int(gpibObj.query("A2RG?"))
CH2AutoRange = {0: "Off", 1: "On"}[i]
i = int(gpibObj.query("I2AR?"))
CH2AutoRangeMode = {0: "Normal", 1: "Tracking"}[i]

# Anti-Aliasing Filter
i = int(gpibObj.query("I1AF?"))
CH1AAFilter = {0: "Off", 1: "On"}[i]

i = int(gpibObj.query("I1AF?"))
CH2AAFilter = {0: "Off", 1: "On"}[i]

# Source amplitude
result = gpibObj.query("SSAM?")
match = re.search(r"^\s*([-+.\d]*),.*", result)
SrcAmp = str(float(match.group(1)))
match = re.search(r"\d,(\d)", result)
i = int(match.group(1))
SrcAmp = (
    SrcAmp
    + {
        0: "mVpk",
        1: "mVpp",
        2: "mVrms",
        3: "Vpk",
        4: "Vrms",
        5: "dBVpk",
        6: "dBVpp",
        7: "dBVrms",
    }[i]
)

# settle cycles
settleCycle = gpibObj.query("SSCY?1")[:-1]

# integration cycle
integrationCycle = gpibObj.query("SICY?1")[:-1]

# construct frequency
if options.sweepType == "Log":
    if startF < endF:
        freq = [
            10 ** ((log10(endF) - log10(startF)) * i / (numPoint - 2) + log10(startF))
            for i in range(numPoint)
        ]
    else:
        freq = [
            10 ** ((log10(startF) - log10(endF)) * i / (numPoint - 2) + log10(endF))
            for i in range(numPoint)
        ]
else:  # linear
    if startF > endF:
        freq = [endF + (startF - endF) * i / (numPoint - 2) for i in range(numPoint)]
    else:
        freq = [startF + (endF - startF) * i / (numPoint - 2) for i in range(numPoint)]

# Open file
dataFile = open(dataFileName, "w")

# Write to the data file
print ("Writing data into the data file %s..." % dataFileName)

dataFile.write("# SR785 Transfer Function Measurement\n")
dataFile.write("#Title: " + options.title + "\n")
dataFile.write("#Memo: " + options.memo + "\n")
dataFile.write("#Instrument ID: " + idnString + "#\n")

dataFile.write("#---------- Given Arguments ----------\n")
for o in sorted(options.__dict__.items()):
    dataFile.write("#" + o[0] + ": ")
    dataFile.write(str(o[1]) + "\n")
dataFile.write("#\n")

dataFile.write("#---------- Measurement Parameters ----------\n")
dataFile.write("#Measurement Group: %s\n" % ", ".join(measGrp))
dataFile.write("#Measurements: %s\n" % ", ".join(measurement))
dataFile.write("#View: %s\n" % ", ".join(view))
dataFile.write("#Unit: %s\n#\n" % ", ".join(units))

dataFile.write("#---------- Input Parameters ----------\n")
dataFile.write("#Input Source: %s\n" % inputSource)
dataFile.write("#Input Mode: %s, %s\n" % (CH1inputMode, CH2inputMode))
dataFile.write("#Input Grounding: %s, %s\n" % (CH1Grounding, CH2Grounding))
dataFile.write("#Input Coupling: %s, %s\n" % (CH1Coupling, CH2Coupling))
dataFile.write("#Input Range: %s, %s\n" % (CH1Range, CH2Range))
dataFile.write("#Auto Range: %s, %s\n" % (CH1AutoRange, CH2AutoRange))
dataFile.write("#Auto Range Mode: %s, %s\n" % (CH1AutoRangeMode, CH2AutoRangeMode))
dataFile.write("#Anti-Aliasing Filter: %s, %s\n#\n" % (CH1AAFilter, CH2AAFilter))

dataFile.write("#---------- Measurement Setup ------------\n")
dataFile.write("#Start frequency = %s\n" % str(startF))
dataFile.write("#Stop frequency = %s\n" % str(endF))
dataFile.write("#Number of frequency points = %d\n" % numPoint)
dataFile.write("#Excitation amplitude = %s\n" % SrcAmp)
dataFile.write("#Settling cycles = %s\n" % settleCycle)
dataFile.write("#Integration cycles = %s\n#\n" % integrationCycle)

dataFile.write("#---------- Instrument Data -----------\n")
dataFile.write("## Freqency(Hz) Magnitude(%s) Phase(%s)\n" % (units[0], units[1]))

for i in range(len(freq)):
    dataFile.write("%.7e " % freq[i])
    for disp in range(2):
        d = struct.unpack("f", bData[disp][4 * i : 4 * (i + 1)])[0]
        dataFile.write("%.7e " % d)
    dataFile.write("\n")


dataFile.close()
gpibObj.close()
