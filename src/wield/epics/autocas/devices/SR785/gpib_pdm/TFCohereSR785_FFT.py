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

This program executes a transfer function measurement using the FFT measurement group of an SR785.
Various measurement conditions can be set using options, including trigger properties.
The measurement result will be saved in FILENAME.dat and the measurement parameters in FILENAME.par.
"""


filetime = time.strftime(
    "%Y-%m-%d.%H%M%S", time.gmtime()
)  # Date string for data file (default)


# Start from FFT measurment setup

# Options below set for SUS noise measurements
parser = optparse.OptionParser(usage=usage)
parser.add_option(
    "-f",
    "--file",
    dest="filename",
    help="Output file name without an extension",
    default=filetime,
)
parser.add_option(
    "-i",
    "--ip",
    dest="ipAddress",
    default="gpib5.mit.edu",
    # dest="ipAddress", default="gpib4.mit.edu",
    # dest="ipAddress", default="18.120.0.103",
    # dest="ipAddress", default="18.120.0.112",
    help="IP address/Host name",
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
    "--coherence",
    dest="Coherence",
    action="store_true",
    default=True,
    help="If given, the code stores Coherence as column 4. Cannot turn off now.",
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
    default="800",
    help="Number of frequency points",
)
parser.add_option(
    "-v",
    "--averaging",
    dest="numAvg",
    type="int",
    default="50",
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
    "--tsource",
    dest="triggerSource",
    type="string",
    default="Continuous",
    help="Trigger Source. Choose Continuous, Ch1, Ch2, Manual, External, or TTL",
)
parser.add_option(
    "--level",
    dest="trig_level",
    type="string",
    default="5",
    help="Trigger level in percent.",
)
parser.add_option(
    "--del1",
    dest="delayA",
    default="1ms",
    help="Delay for Channel 1. Units can be us, ms, or s. Must be between -8000 and +10000 times underlying FFT sample rate.",
)
parser.add_option(
    "--del2",
    dest="delayB",
    default="1ms",
    help="Delay for Channel 2. Units can be us, ms, or s. Must be between -8000 and +10000 times underlying FFT sample rate.",
)
parser.add_option(
    "--timerecordincr",
    dest="timeRecordIncr",
    default="",
    help="Time record increment, up to 300 percentage.",
)
# parser.add_option("-d", "--dualchannel",action="store_true",
#                   dest="dual",
#                   help="Set to the dual channel mode.")
parser.add_option(
    "--ic1",
    dest="inputCoupling1",
    type="string",
    default="AC",
    help="CH1 input coupling. DC or AC",
)
parser.add_option(
    "--ic2",
    dest="inputCoupling2",
    type="string",
    default="AC",
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
    "--id1",
    dest="inputDiff1",
    type="string",
    default="SE",
    help="CH1 input Differential A-B, or single ended A",
)
parser.add_option(
    "--id2",
    dest="inputDiff2",
    type="string",
    default="SE",
    help="CH1 input Differential A-B, or single ended A",
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

# Should also have command here that makes sure delay is between -8000 and +10000 times the underlying FFT sample rate


# Convert number of points into available resolution
if options.numOfPoints <= 100:
    fRes = 0  # Resolution is 100 points
elif options.numOfPoints <= 200:
    fRes = 1  # Resolution is 200 points
elif options.numOfPoints <= 400:
    fRes = 2  # Resolution is 400 points
else:
    fRes = 3  # Resolution is 800 points

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

print ("Measurement data will be written into " + dataFileName)
print ("Setting up parameters for the measurement...")


# Prepare for the FFT measurement

# Set measurement parameters
numDisp = 2
gpibObj.command("DFMT1")  # Dual display
# if options.dual:
#    gpibObj.command('DFMT1') # Dual display
#    numDisp=2
# else:
#    gpibObj.command('DFMT0') # Single display
#    numDisp=1

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

if options.inputDiff1 == "SE":
    idf1 = "0"
else:
    idf1 = "1"
gpibObj.command("I1MD" + idf1)  # CH1 Input A-B = 1; A = 0

if options.inputDiff2 == "SE":
    idf1 = "0"
else:
    idf1 = "1"
gpibObj.command("I2MD" + idf1)  # CH2 Input A-B = 1; A = 0

gpibObj.command("A1RG0")  # AutoRange Off
gpibObj.command("A2RG0")  # AutoRange Off
if options.inputRange1 != "":
    gpibObj.command("I1RG" + options.inputRange1)
else:
    gpibObj.command("I1AR0")  # Auto Range Mode
    gpibObj.command("A1RG1")  # AutoRange On
if options.inputRange2 != "":
    gpibObj.command("I2RG" + options.inputRange2)
else:
    gpibObj.command("I2AR0")  # Auto Range Mode
    gpibObj.command("A2RG1")  # AutoRange On
if options.inputRange1 == "" or options.inputRange2 == "":
    print "Auto-ranging..."
    time.sleep(10)  # Gives it sufficient time to autorange completely -AWB
#  time.sleep(5)

gpibObj.command("I1AF1")  # Anti-Aliasing filter On
gpibObj.command("I2AF1")  # Anti-Aliasing filter On

# Common setup for both displays
gpibObj.command("MGRP2,0")  # Measurement Group = FFT
gpibObj.command("FBAS2,1")  # Base Frequency = 102.4kHz
gpibObj.command("ISRC0")  # Input = Analog

# Set up each display
# Display 0
gpibObj.command("MEAS0,11")  # Frequency Resp
gpibObj.command("VIEW0,0")  # Disp 0 = LogMag
gpibObj.command("UNDB0,1")  # dB ON
gpibObj.command("UNPK0,0")  # PK Unit Off
gpibObj.command("DISP0,1")  # Live display on

# Display 1

gpibObj.command("MEAS1,11")  # Frequency Resp
gpibObj.command("VIEW1,5")  # Dsip 1 = Phase
gpibObj.command("UNDB1,0")  # dB OFF
gpibObj.command("UNPK1,0")  # PK Unit Off
gpibObj.command("UNPH1,0")  # Phase Unit deg.
gpibObj.command("DISP1,1")  # Live display on

# Common setup
gpibObj.command("FSPN2," + options.bandWidth)  # Frequency span
gpibObj.command("FLIN2," + str(fRes))  # Frequency resolution
gpibObj.command("FAVG2,1")  # Averaging On
if options.timeRecordIncr != "":
    gpibObj.command("FOVL2,%s" % options.timeRecordIncr)

avgModDict = {"None": 0, "Vector": 1, "RMS": 2, "PeakHold": 3}
if options.avgMode in avgModDict:
    avgModID = avgModDict[options.avgMode]
else:
    avgModID = 2
gpibObj.command("FAVM2," + str(avgModID))  # Averaging mode

gpibObj.command("FAVT2,0")  # Averaging Type = Linear
gpibObj.command("FREJ2,1")  # Overload Reject On
gpibObj.command("FAVN2," + str(options.numAvg))  # Number of Averaging

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

# Set up trigger settings
gpibObj.command("TMOD0")  # Auto trigger arming
if options.triggerSource == "Continuous":  # Continuous
    trigSource = "0"
elif options.triggerSource == "Ch1":  # Channel 1
    trigSource = "1"
elif options.triggerSource == "Ch2":  # Channel 2
    trigSource = "2"
elif options.triggerSource == "External":  # External
    trigSource = "3"
elif options.triggerSource == "TTL":  # External TLL
    trigSource = "4"
elif options.triggerSource == "Source":  # Source
    trigSource = "5"
elif options.triggerSource == "Manual":  # Manual
    trigSource = "6"
else:  # Continuous
    trigSource = "0"
gpibObj.command("TSRC" + trigSource)  # Trigger Source
# Only set trigger level if correct trigger source is selected
if trigSource == 1 or trigSource == 2 or trigSource == 3:
    gpibObj.command("TLVL" + options.trig_level)  # Sets trigger level in percent
gpibObj.command("TDLA" + options.delayA)  # Delay for channel 1 in s
gpibObj.command("TDLB" + options.delayB)  # Delay for channel 2 in s


# Start measurement
# print 'Measurement started'
print "Trigger armed"
sys.stdout.flush()
gpibObj.command("STRT")  # Start measurement
# Wait for the measurement to end
measuring = True
avg = 0
print "Averaging completed:",
print "0",
sys.stdout.flush()
txtlen = 1
while measuring:
    # Get status
    measuring = not int(gpibObj.query("DSPS?1"))
    avg = int(gpibObj.query("NAVG?0"))
    print "\010" + "\010" * txtlen + str(avg),
    sys.stdout.flush()
    txtlen = len(str(avg))
    time.sleep(0.3)

a = int(gpibObj.query("NAVG?0"))
print "\010" + "\010" * txtlen + str(avg)
sys.stdout.flush()
print ("done")

gpibObj.command("ASCL0")  # Auto scale
gpibObj.command("ASCL1")  # Auto scale

# collect data
bData = []
units = []
measGrp = []
measurement = []
view = []

for disp in range(numDisp):
    # Get the number of points on the Display
    numPoint = int(gpibObj.query("DSPN?" + str(disp)))
    print "Transferring data of display %d..." % (disp + 1)
    # 801 points x 4 bytes/point = 3204 is the maximum buffer needed
    bData.append(gpibObj.query("DSPB?" + str(disp), buf=4096, IFCCheck=False))
    gpibObj.waitIFC()
    units.append(gpibObj.query("UNIT?%d" % disp)[:-1])
    # query params / sanity check
    if int(gpibObj.query("MGRP?" + str(disp))) == 0:
        measGrp.append("FFT")
    else:
        print >> sys.stderr, "Error: Measurement group is not set to FFT."
        sys.exit(1)
    i = int(gpibObj.query("MEAS?" + str(disp)))
    if i == 11:
        measurement.append("Frequency Response (FFT)")
    else:
        print >> sys.stderr, "Error: Measurement is not Frequency Response"
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

# Get coherence data (if option supplied)
if options.Coherence:
    numDisp = numDisp + 1  # We have another measurement to save
    print ("Changing Display 1 to Coherence")
    ##Get Coherence data :
    ## CHange display 0
    gpibObj.command("MEAS0,9")  # Coherence measurement
    gpibObj.command("VIEW0,1")  # Disp 0 = LinMag
    gpibObj.command("UNDB0,0")  # dB OFF
    gpibObj.command("UNPK0,0")  # PK Unit Off
    gpibObj.command("DISP0,1")  # Live display on

    print ("Downloading coherence data")
    ##Save data :
    disp = 0
    print ("Downloading data from display #" + str(disp))
    numPoint = int(gpibObj.query("DSPN?" + str(disp)))
    # startF=float(gpibObj.query("SSTR?%d"%disp))
    #  endF=float(gpibObj.query("SSTP?%d"%disp))
    # 2048 points x 4 bytes/point = 8192 is the maximum buffer needed
    bData.append(gpibObj.query("DSPB?" + str(disp), buf=8192, IFCCheck=False))
    gpibObj.waitIFC()
    units.append(gpibObj.query("UNIT?%d" % disp)[:-1])
    # query params / sanity check
    if int(gpibObj.query("MGRP?" + str(disp))) == 0:
        measGrp.append("FFT")
    else:
        print >> sys.stderr, "Error: Measurement group is not set to FFT."
        sys.exit(1)
    i = int(gpibObj.query("MEAS?" + str(disp)))
    if i == 9:
        measurement.append("Coherence (FFT)")
    else:
        print >> sys.stderr, "Error: Measurement is not Coherence"
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
else:
    print ("Not taking Coherence data")


## get other parameters
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
CH2AutoRangeMode = {0: "Up Only", 1: "Tracking"}[i]

# Anti-Aliasing Filter
i = int(gpibObj.query("I1AF?"))
CH1AAFilter = {0: "Off", 1: "On"}[i]

i = int(gpibObj.query("I1AF?"))
CH2AAFilter = {0: "Off", 1: "On"}[i]

# Trigger parameters
i = int(gpibObj.query("TSRC?"))  # Trigger Source
trig_source = {
    0: "Continuous",
    1: "Ch1",
    2: "Ch2",
    3: "External",
    4: "Ext. TLL",
    5: "Source",
    6: "Manual",
}[i]
trig_level = (
    gpibObj.query("TLVL?")[:-3] + "%"
)  # Trigger level in percent-->May have problems if not returned as percent
delay1 = gpibObj.query("TDLA?")[:-1] + " s"  # Delay for channel 1 in s
delay2 = gpibObj.query("TDLB?")[:-1] + " s"  # Delay for channel 2 in s

# frequency span
fSpan = gpibObj.query("FSPN?0")[:-1]

# frequency resolution
fRes = int(gpibObj.query("FLIN?0"))
fRes = {0: 100, 1: 200, 2: 400, 3: 800}[fRes]

# number of averages
nAvg = int(gpibObj.query("NAVG?0"))

avgMode = int(gpibObj.query("FAVM?0"))
avgMode = {0: "None", 1: "Vector", 2: "RMS", 3: "PeakHold"}[avgMode]

winFunc = int(gpibObj.query("FWIN?0"))
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
}[winFunc]


# Open file
dataFile = open(dataFileName, "w")

# Write data to file
dataFile.write("# SR785 Transfer Function Measurement Measurement\n")
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
dataFile.write("#Trigger Source: %s\n" % trig_source)
dataFile.write("#Trigger Level: %s\n" % trig_level)
dataFile.write("#Channel 1 Delay: %s\n" % delay1)
dataFile.write("#Channel 2 Delay: %s\n" % delay2)
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

dataFile.write("#---------- Measurement Setup ----------\n")
dataFile.write("#Frequency Span: %s\n" % fSpan)
dataFile.write("#Frequency Resolution: %s\n" % str(fRes))
dataFile.write("#Number of Averages: %s\n" % str(nAvg))
dataFile.write("#Averaging Mode: %s\n" % avgMode)
dataFile.write("#Window function: %s\n#\n" % winFunc)


# write the data
dataFile.write("#---------- Instrument Data -----------\n")
if options.Coherence:
    dataFile.write(
        "## Freqency(Hz) Magnitude(%s) Phase(%s) Coherence\n" % (units[0], units[1])
    )
else:
    dataFile.write("## Freqency(Hz) Magnitude(%s) Phase(%s) \n" % (units[0], units[1]))

# Move through each frequency bin
df = float(fSpan) / (numPoint - 1)
f = 0
for b in range(numPoint):  # Loop for frequency bins
    dataFile.write("%.7e " % f)
    for disp in range(numDisp):
        d = struct.unpack("f", bData[disp][4 * b : 4 * (b + 1)])[0]
        dataFile.write("%.7e " % d)
    dataFile.write("\n")
    f = f + df

dataFile.close()
print "done."


gpibObj.close()


# END OF FFT TF MEASUREMENT
