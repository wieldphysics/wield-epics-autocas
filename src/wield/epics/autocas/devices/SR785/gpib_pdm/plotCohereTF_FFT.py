#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
plotCohereTF_FFT.py creates a plot from output file of TFCohereSR785_FFT.py.

If input file is specified (--inputFile/-f option), the plotCohereTF_FFT.py plots the data in the file. The file is assumed to be an output file from TFCohereSR785_FFT.py. All the options below --inputFile/-f will be ignored.

If --inputFile/-f option is not given, then plotTF.py runs TFCohereSR785_FFT.py by itself to get data for plot, using the options given.

Syntax:
python plotCohereTF_FFT.py [options]

Type in
python plotCohereTF_FFT.py -h
for help.

Tomoki Isogai (isogait@mit.edu)
Aaron Buikema (abuikema@mit.edu)
"""

# =============================================================================
#
#                                  PREAMBLE
#
# =============================================================================


import os
import sys
import re
import optparse
import time
import numpy as np
import matplotlib.pyplot as plt

__author__ = "Tomoki Isogai <isogait@mit.edu>"
__date__ = "06/25/2012"
__version__ = "1.0"


def parse_commandline():
    """
    Parse the options given on the command-line.
    """
    parser = optparse.OptionParser(usage=__doc__, version=__version__)

    parser.add_option(
        "-V",
        "--verbose",
        action="store_true",
        default=False,
        help="Run verbosely. (Default: False)",
    )
    parser.add_option(
        "-o", "--outputDir", default="outputs", help="Output directory name."
    )
    parser.add_option(
        "--title",
        dest="title",
        type="string",
        default="",
        help="Title of the measurement.",
    )
    parser.add_option(
        "--showplot",
        dest="showPlot",
        action="store_true",
        default=False,
        help="If given, plot will show up on screen. (Default: False)",
    )
    parser.add_option(
        "-f",
        "--inputFile",
        help="If input file is specified, the program just plots the data in the file. The file is assumed to be an output file from TFSR785.py. If this option is not given, then the program runs the TFSR785.py to get data, using the options given below.",
    )

    # options for TFCohereSR785_FFT.py
    #   parser.add_option("-p", "--TFSR785",default="./TFSR785.py",help="Path to the TFSR785.py.")
    parser.add_option(
        "-p",
        "--TFSR785",
        default="./TFCohereSR785_FFT.py",
        help="Path to the TFCohereSR785_FFT.py.",
    )
    parser.add_option(
        "-i",
        "--ip",
        dest="ipAddress",
        default="gpib7.mit.edu",
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
        default='""',
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
        default='""',
        help="CH1 input range (default unit is dBVpk). If not given, auto-range will be used.",
    )
    parser.add_option(
        "--inputrange2",
        dest="inputRange2",
        default='""',
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
    #   parser.add_option("--title",
    #                   dest="title", type="string",default="",
    #                   help="Title of the measurement. The given string will be written into the parameter file.")
    parser.add_option(
        "--memo",
        dest="memo",
        type="string",
        default="",
        help="Use this option to note miscellaneous things.",
    )

    opts, args = parser.parse_args()

    if opts.verbose:
        print >> sys.stderr, "Running plotCohereTF_FFT.py..."
        print >> sys.stderr, "Version: %s" % __version__
        print >> sys.stderr, ""
        print >> sys.stderr, "***************** PARAMETERS ********************"
        for o in opts.__dict__.items():
            print >> sys.stderr, o[0] + ":"
            print >> sys.stderr, o[1]
        print >> sys.stderr, ""

    return opts


# =============================================================================
#
#                                    MAIN
#
# =============================================================================

# parse the command line
opts = parse_commandline()

# sanity check
if opts.inputFile != None and not os.path.isfile(opts.inputFile):
    print >> sys.stderr, "Error: --inputFile %s not found." % opts.inputFile
    sys.exit(1)
if opts.inputFile == None and not os.path.isfile(opts.TFSR785):
    print >> sys.stderr, "Error: TFCohereSR785_FFT.py is not found at %s." % opts.inputFile
    sys.exit(1)

# create output directory if it doesn't exist yet
if not os.path.isdir(opts.outputDir):
    if opts.verbose:
        print >> sys.stderr, "Creating the output directory '%s'..." % opts.outputDir
    os.makedirs(opts.outputDir)

if opts.inputFile != None:
    dataFile = opts.inputFile
else:
    # run TFCohereSR785_FFT.py to get data
    if opts.title == "":
        opts.title = time.strftime("%Y-%m-%d.%H%M%S", time.gmtime())
    fileName = os.path.join(opts.outputDir, opts.title)
    if opts.skipReset:
        reset = "-r"
    else:
        reset = ""
    cmd = (
        'python %s -i %s -a %s %s -v %s --coherence -b %s -f %s --tsource %s --level %s -n %s --del1 %s --del2 %s --timerecordincr %s -w %s --ic1 %s --ic2 %s --ig1 %s --ig2 %s --inputrange1 %s --inputrange2 %s --title "%s" --memo "%s"'
        % (
            opts.TFSR785,
            opts.ipAddress,
            opts.gpibAddress,
            reset,
            opts.numAvg,
            opts.bandWidth,
            fileName,
            opts.triggerSource,
            opts.trig_level,
            opts.numOfPoints,
            opts.delayA,
            opts.delayB,
            opts.timeRecordIncr,
            opts.windowFunc,
            opts.inputCoupling1,
            opts.inputCoupling2,
            opts.inputGND1,
            opts.inputGND2,
            opts.inputRange1,
            opts.inputRange2,
            opts.title,
            opts.memo,
        )
    )  # Right now, coherence measurement hard coded in
    #  cmd = 'python %s -i %s -a %s %s --coherence -f %s -s %s -e %s -n %s --sweep %s -x %s -c %s -t %s --ic1 %s --ic2 %s --ig1 %s --ig2 %s --inputrange1 %s --inputrange2 %s --armode %s --title "%s" --memo "%s"'%(opts.TFSR785,opts.ipAddress,opts.gpibAddress,reset,fileName,opts.startFreq,opts.stopFreq,opts.numOfPoints,opts.sweepType,opts.excAmp,opts.settleCycles,opts.intCycles,opts.inputCoupling1,opts.inputCoupling2,opts.inputGND1,opts.inputGND2,opts.inputRange1,opts.inputRange2,opts.arMode,opts.title,opts.memo) #Right now, coherence measurement hard coded in

    if opts.verbose:
        print >> sys.stderr, "Getting data...:"
        print >> sys.stderr, cmd
    exit = os.system(cmd)
    if exit > 0:
        print >> sys.stderr, "Error: '%s' failed" % cmd
        sys.exit(1)

    dataFile = fileName + ".dat"

# read the spectrum data
if opts.verbose:
    print >> sys.stderr, "Reading data from %s..." % dataFile

# find where data begins, and find title and unit
headerN = 0
# enumerate(x) uses x.next, so it doesn't store the entire file info in memory
for i, line in enumerate(open(dataFile)):
    if line[:7] == "#Title:":
        title = os.path.split(line.split()[1])[-1]
    elif line[:2] == "##":
        units = line.split()[1:4]
        headerN = i + 1
        break
data = np.genfromtxt(dataFile, skip_header=headerN, delimiter=" ")
freq = data[:, 0]
mag = data[:, 1]
phase = data[:, 2]
cohere = data[:, 3]

# Convert sqrt character
for i in range(len(units)):
    units[i] = re.sub(r"\xFB(.*)", r"$\mathsf{\sqrt{\1}}$", units[i])
xUnit, magUnit, phaseUnit = units

# ==============================================================================
# Transfer Function Plot

if opts.verbose:
    print >> sys.stderr, "Plotting..."

fig = plt.figure()
ax = fig.add_subplot(211)
ax.set_title(title + " Transfer Function")
# ax.set_xlabel(xUnit)
ax.set_ylabel(magUnit)
ax.semilogx(freq, mag, "b")
# plt.xlim(xRange)
plt.grid()

ax = fig.add_subplot(212)
ax.set_xlabel(xUnit)
ax.set_ylabel(phaseUnit)
ax.semilogx(freq, phase, "b")
# plt.xlim(xRange)
plt.grid()

plt.savefig(os.path.join(opts.outputDir, "%s.png" % title))
if opts.showPlot:
    print "Close the plot window to continue..."
    plt.show()
plt.close("all")


# Now plot coherence
plt.semilogx(freq, cohere, "b")
plt.title("%s Coherence" % title)
plt.xlabel(units[0])
plt.ylabel("Coherence")
plt.grid()
plt.savefig(os.path.join(opts.outputDir, "%s_cohere.png" % title))
if opts.showPlot:
    print "Close the plot window to continue..."
    plt.show()
plt.close("all")
