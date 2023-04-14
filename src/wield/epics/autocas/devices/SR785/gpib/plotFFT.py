#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
If input file is specified (--inputFile/-f option), the plotFFT.py plots the data in the file. The file is assumed to be an output file from FFTSR785.py. All the options below --inputFile/-f will be ignored.

If --inputFile/-f option is not given, then plotFFT.py runs FFTSR785.py by itself to get data for plot, using the options given.

Syntax:
python plotFFT.py [options]

Type in
python plotFFT.py -h
for help.

Tomoki Isogai (isogait@mit.edu)
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
        "-o",
        "--outputDir",
        default="../../../Data/" + time.strftime("%Y-%m-%d", time.gmtime()),
        help="Output directory name.",
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
        help="If --inputFile is specified, the program just plots the data in the file. The file is assumed to be an output file from FFTSR785.py. If this option is not given, then the program runs the FFTSR785.py to get data, using the options given below.",
    )

    # options for FFTSR785.py
    parser.add_option(
        "-p", "--FFTSR785", default="./FFTSR785.py", help="Path to the FFTSR785.py."
    )
    parser.add_option(
        "--nocombine",
        action="store_true",
        help="By default, the code takes two FFT measurement, one for low frequency region (<1.6kHz) and one for high frequency region, and combine the two results. If this options is given, the code takes only one measurement instead.",
    )
    parser.add_option(
        "-i",
        "--ip",
        dest="ipAddress",
        default="18.120.0.112",
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
        "-b",
        "--bandwidth",
        dest="bandWidth",
        default="100kHz",
        help="Bandwidth. You can use mHz,Hz or kHz units.",
    )
    parser.add_option(
        "--base",
        dest="base",
        action="store_true",
        default="False",
        help="Set frequency base to 100kHz.",
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
        "--timerecordincr",
        dest="timeRecordIncr",
        default='""',
        help="Time record increment, up to 300 percentage.",
    )
    parser.add_option(
        "-d",
        "--dualchannel",
        action="store_true",
        dest="dual",
        help="Set to the dual channel mode.",
    )
    parser.add_option(
        "--dB",
        action="store_true",
        default="False",
        dest="decible",
        help="Use dB units instead of V/rt(Hz).",
    )
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
        help="CH2 input Differential A-B, or single ended A",
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
        "--memo",
        dest="memo",
        type="string",
        default="",
        help="Use this option to note miscellaneous things.",
    )

    opts, args = parser.parse_args()

    if opts.verbose:
        print >> sys.stderr, "Running plotFFT.py..."
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
if opts.inputFile == None and not os.path.isfile(opts.FFTSR785):
    print >> sys.stderr, "Error: FFTSR785.py is not found at %s." % opts.inputFile
    sys.exit(1)

# create output directory if it doesn't exist yet
if not os.path.isdir(opts.outputDir):
    if opts.verbose:
        print >> sys.stderr, "Creating the output directory '%s'..." % opts.outputDir
    os.makedirs(opts.outputDir)

if opts.inputFile != None:
    dataFile = opts.inputFile
else:
    # run FFTSR785.py to get data
    if opts.title == "":
        opts.title = time.strftime("%Y-%m-%d.%H%M%S", time.gmtime())
    fileName = os.path.join(opts.outputDir, opts.title)

    # high freq range
    fileNameHigh = fileName + "_HighFreq"
    if opts.dual:
        dual = "-d"
        numOfDisp = 2
    else:
        dual = ""
        numOfDisp = 1
    if opts.skipReset:
        reset = "-r"
    else:
        reset = ""
    cmd = (
        'python %s -i %s -a %s -f %s %s -b %s -n %s -v %s --avgmode %s --timerecordincr %s %s --ic1 %s --ic2 %s --ig1 %s --ig2 %s --inputrange1 %s --inputrange2 %s --id1 %s --id2 %s -w %s --title "%s" --memo "%s"'
        % (
            opts.FFTSR785,
            opts.ipAddress,
            opts.gpibAddress,
            fileNameHigh,
            reset,
            opts.bandWidth,
            opts.numOfPoints,
            opts.numAvg,
            opts.avgMode,
            opts.timeRecordIncr,
            dual,
            opts.inputCoupling1,
            opts.inputCoupling2,
            opts.inputGND1,
            opts.inputGND2,
            opts.inputRange1,
            opts.inputRange2,
            opts.inputDiff1,
            opts.inputDiff2,
            opts.windowFunc,
            opts.title,
            opts.memo,
        )
    )
    if opts.verbose:
        print >> sys.stderr, "Getting data for high frequency range...:"
        print >> sys.stderr, cmd
    exit = os.system(cmd)
    if exit > 0:
        print >> sys.stderr, "Error: '%s' failed" % cmd
        sys.exit(1)

    if not opts.nocombine:
        # low freq range (below 1.6kHz)
        fileNameLow = fileName + "_LowFreq"
        cmd = (
            'python %s -i %s -a %s -f %s -r -b %s -n %s -v %s --avgmode %s --timerecordincr %s %s --ic1 %s --ic2 %s --ig1 %s --ig2 %s --inputrange1 %s --inputrange2 %s --id1 %s --id2 %s -w %s --title "%s" --memo "%s"'
            % (
                opts.FFTSR785,
                opts.ipAddress,
                opts.gpibAddress,
                fileNameLow,
                "1.6kHz",
                opts.numOfPoints,
                opts.numAvg,
                opts.avgMode,
                opts.timeRecordIncr,
                dual,
                opts.inputCoupling1,
                opts.inputCoupling2,
                opts.inputGND1,
                opts.inputGND2,
                opts.inputRange1,
                opts.inputRange2,
                opts.inputDiff1,
                opts.inputDiff2,
                opts.windowFunc,
                opts.title,
                opts.memo,
            )
        )
        if opts.verbose:
            print >> sys.stderr, "Getting data for low frequency range...:"
            print >> sys.stderr, cmd
        exit = os.system(cmd)
        if exit > 0:
            print >> sys.stderr, "Error: '%s' failed" % cmd

        # combine low freq and all freq data and save it to a file
        if opts.verbose:
            print >> sys.stderr, "Combining high and low frequency data and saving it in a file..."

        # get metadata
        fp = open(fileNameHigh + ".dat")
        metaData = []
        headerN = 0
        # enumerate(x) uses x.next, so it doesn't store the entire file info in memory
        for i, line in enumerate(fp):
            metaData.append(line)
            if line[:2] == "##":
                metaData.append(line)
                headerN = i + 1
                break
        fp.close()
        data = np.genfromtxt(fileNameHigh + ".dat", skip_header=headerN, delimiter=" ")
        freqHigh = data[:, 0]
        magHigh = data[:, 1 : numOfDisp + 1]

        data = np.genfromtxt(fileNameLow + ".dat", skip_header=headerN, delimiter=" ")
        freqLow = data[:, 0]
        magLow = data[:, 1 : numOfDisp + 1]

        validIdx = freqHigh > freqLow[-1]
        freq = np.concatenate([freqLow, freqHigh[validIdx]])
        mag = np.concatenate([magLow, magHigh[validIdx]])

        # saving:
        dataFile = fileName + "_combined.dat"
        fp = open(dataFile, "w")
        fp.write("".join(metaData))
        np.savetxt(fp, np.column_stack([freq, mag]), fmt="%.7e")
        fp.close()

        del freqHigh, magHigh, freqLow, magLow
    else:  # no combine case
        dataFile = fileNameHigh + ".dat"

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
        units = line.split()[1 : numOfDisp + 2]
        headerN = i + 1
        break
data = np.genfromtxt(dataFile, skip_header=headerN, delimiter=" ")
numOfDisp = len(data[0]) - 1
freq = data[:, 0]
mag = data[:, 1 : numOfDisp + 1]


# Convert sqrt character
for i in range(len(units)):
    units[i] = re.sub(r"\xFB(.*)", r"$\mathsf{\sqrt{\1}}$", units[i][:-1]) + ")"

# ==============================================================================
# Spectrum Plot

if opts.verbose:
    print >> sys.stderr, "Plotting..."

if numOfDisp == 1:
    plt.loglog(freq, mag, "b")
    plt.title(title)
    plt.xlabel(units[0])
    plt.ylabel(units[1])
    plt.grid()
    plt.savefig(os.path.join(opts.outputDir, "%s.jpg" % title))
    if opts.showPlot:
        print "Close the plot window to continue..."
        plt.show()
    plt.close("all")

if numOfDisp == 2:
    # plot disp 1
    plt.loglog(freq, mag[:, 0], "b")
    plt.title("%s Disp1" % title)
    plt.xlabel(units[0])
    plt.ylabel(units[1])
    plt.grid()
    plt.savefig(os.path.join(opts.outputDir, "%s_disp1.jpg" % title))
    if opts.showPlot:
        print "Close the plot window to continue..."
        plt.show()
    plt.close("all")
    # plot disp 2
    plt.loglog(freq, mag[:, 1], "b")
    plt.title("%s Disp2" % title)
    plt.xlabel(units[0])
    plt.ylabel(units[2])
    plt.grid()
    plt.savefig(os.path.join(opts.outputDir, "%s_disp2.jpg" % title))
    if opts.showPlot:
        print "Close the plot window to continue..."
        plt.show()
    plt.close("all")

    # plot both in one plot
    plt.loglog(freq, mag[:, 0], "b", label="disp1")
    plt.loglog(freq, mag[:, 1], "g", label="disp2")
    plt.title(title)
    plt.xlabel(units[0])
    plt.ylabel(units[1])
    plt.grid()
    plt.legend(loc="best")
    plt.savefig(os.path.join(opts.outputDir, "%s_both.jpg" % title))
    if opts.showPlot:
        print "Close the plot window to continue..."
        plt.show()
    plt.close("all")

    # plot both using subplot
    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.set_title("%s disp 1" % title)
    ax.set_ylabel(units[1])
    ax.loglog(freq, mag[:, 0], "b")
    plt.grid()

    ax = fig.add_subplot(212)
    ax.set_title("%s disp 2" % title)
    ax.set_xlabel(units[0])
    ax.set_ylabel(units[2])
    ax.loglog(freq, mag[:, 1], "b")
    plt.grid()
    plt.savefig(os.path.join(opts.outputDir, "%s_subplot.jpg" % title))
    if opts.showPlot:
        print "Close the plot window to continue..."
        plt.show()
    plt.close("all")

if opts.verbose:
    print >> sys.stderr, "Done!"
