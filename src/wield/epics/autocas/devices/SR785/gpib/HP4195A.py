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
import time
import netgpibOLD as netgpib
import pdb

# analyzer mode = 1 for Network Analyzer, 2 for Spectrum Analyzer
def getdata(gpibObj, dataFile, analyzerMode):

    # Set the output format to ASCII
    gpibObj.command("FMT1")

    if analyzerMode == 1:
        # It is the network analyzer mode
        # Get the magnitude data from chan 1 and phase data from chan 2

        # Get the frequency points
        print("Reading frequency points.")
        receivedData = gpibObj.query("X?")
        time.sleep(0.1)

        # Parse data
        # Matching to the second column of dumpedData
        freqList = re.findall(r"\d+\.\d+", receivedData, re.M)

        # Get the data
        print("Reading magnitude data")
        receivedData = gpibObj.query("A?")
        time.sleep(0.1)

        # Break the data into lists
        dataList1 = re.findall(r".\d+\.\d+E+.\d+|0", receivedData, re.M)

        # Get the Phase Data
        print("Reading Phase Data.")
        phaseData = gpibObj.query("B?")
        time.sleep(0.1)

        # Break the data into lists
        dataList2 = re.findall(r".\d+\.\d+E+.\d+|0", phaseData, re.M)

        # Output data
        print("Writing the data into a file.")

        for i in range(len(freqList)):
            dataFile.write(freqList[i] + " " + dataList1[i] + " " + dataList2[i] + "\n")
    else:
        # It is spectrum analyzer mode
        # Get the frequency points
        print("Reading frequency points.")
        receivedData = gpibObj.query("X?")
        time.sleep(0.1)

        # Parse data
        # Matching to the second column of dumpedData
        freqList = re.findall(r"\d+\.\d+", receivedData, re.M)

        # Get the data
        print("Reading magnitude data")
        receivedData = gpibObj.query("A?")
        time.sleep(0.1)

        # Break the data into lists
        dataList1 = re.findall(r".\d+\.\d+E+.\d+|0", receivedData, re.M)

        # Output data
        print("Writing the data into a file.")

        for i in range(len(freqList)):
            dataFile.write(freqList[i] + " " + dataList1[i] + "\n")
