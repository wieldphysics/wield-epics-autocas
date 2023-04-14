#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
save2mat.py reads the .dat file created from the SR785 and saves the data as a .mat file.

Syntax:
python save2mat.py -f inputfile

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
import scipy.io as sio
from cmath import exp
from math import pi

__author__ = (
    "Tim Bodiya <bodtim@mit.edu>, modified from plotTF written by Tomoki Isogai"
)
__date__ = "08/07/2012"
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
        "-f",
        "--inputFile",
        help="If input file is specified, the program just plots the data in the file. The file is assumed to be an output file from TFSR785.py. If this option is not given, then the program runs the TFSR785.py to get data, using the options given below.",
    )

    opts, args = parser.parse_args()

    if opts.verbose:
        print >>sys.stderr, "Converting data with save2mat.py ..."
        print >>sys.stderr, "Version: %s" % __version__
        print >>sys.stderr, ""
        print >>sys.stderr, "***************** PARAMETERS ********************"
        for o in opts.__dict__.items():
            print >>sys.stderr, o[0] + ":"
            print >>sys.stderr, o[1]
        print >>sys.stderr, ""

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
    print >>sys.stderr, "Error: --inputFile %s not found." % opts.inputFile
    sys.exit(1)

if opts.inputFile != None:
    dataFile = opts.inputFile


# read the spectrum data
if opts.verbose:
    print >>sys.stderr, "Reading data from %s..." % dataFile

# find where data begins, and find title and unit
headerN = 0
# enumerate(x) uses x.next, so it doesn't store the entire file info in memory
for i, line in enumerate(open(dataFile)):
    if line[:7] == "#Title:":
        title = os.path.split(line.split()[1])[-1]
    elif line[:2] == "##":
        units = line.split()[1:5]
        headerN = i + 1
        break
print >>sys.stderr, dataFile
data = np.genfromtxt(dataFile, skip_header=headerN, delimiter=" ")
freq = data[:, 0]
mag = data[:, 1]
phase = data[:, 2]
phase = phase * pi / 180
phase = [exp(pp * 1j) for pp in phase]

if len(data[1, :]) == 4:
    coh = data[:, 3]

tf = 10 ** (mag / 20.0)
tf = tf * phase

dataFileMat = dataFile[0:-4] + ".mat"
matdata = {}
matdata["freq"] = freq
matdata["tf"] = tf
matdata["coh"] = coh

sio.savemat(dataFileMat, matdata)
