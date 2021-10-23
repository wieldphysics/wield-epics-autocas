from numpy import *
import fileinput
import matplotlib.pyplot as mpl
import re


def plotSR785(filename, xlog=True, ylog=None):
    """Plot downloaded data from SR785"""
    dataFile = filename + ".dat"
    paramFile = filename + ".par"

    # If it is a file generated by TFSR785.py, call plotTFSR785()
    tfFilePat = re.compile(r"^#SR785 Transfer function measurement")
    firstLine = fileinput.input(paramFile)[0]
    if tfFilePat.match(firstLine):
        fileinput.close()
        ax = plotTFSR785(filename)
        return ax
    tsFilePat = re.compile(r"#Time series measurement parameters")
    if tsFilePat.match(firstLine):
        fileinput.close()
        ax = plotTSSR785(filename)
        return ax

    fileinput.close()

    # Scan parameter file to get units
    unitLinePat = re.compile(r"^Unit:")
    measLinePat = re.compile(r"^Measurements:")
    mgLinePat = re.compile(r"^Measurement Group:")
    quotePat = re.compile(r'"([^"]*)"')
    for line in fileinput.input(paramFile):
        if unitLinePat.match(line):
            units = quotePat.findall(line)
            for i in range(len(units)):
                # Convert sqrt character
                units[i] = re.sub(r"\xFB(.*)", r"$\mathsf{\sqrt{\1}}$", units[i])

        if measLinePat.match(line):
            titles = quotePat.findall(line)

        if mgLinePat.match(line):  # Check measurement group
            mgs = quotePat.findall(line)
            if mgs[0] == "FFT":
                type = "spectrum"
            else:
                type = "other"

    # Read data
    firstLine = True
    dispLinePat = re.compile(r"^#Display")
    dispID = -1
    data = []
    if type == "spectrum":
        for line in fileinput.input(dataFile):
            if dispLinePat.match(line):  # Start of new display
                firstLine = True
                dispID = dispID + 1
                continue
            if line.strip()[0] == "#":
                continue  # Skip lines starting from #

            if firstLine:
                data.append(transpose(array([map(float, line.split())])))
                firstLine = False
            else:
                data[dispID] = hstack(
                    (data[dispID], transpose(array([map(float, line.split())])))
                )

        # Plot spectra
        numPlot = len(data)
        fig = mpl.figure()
        fig.subplots_adjust(hspace=0.4)
        axList = []
        for i in range(numPlot):
            axList.append(fig.add_subplot(numPlot, 1, i + 1))
            axList[i].plot(data[i][0], data[i][1])
            if (data[i][1].min() > 0) and ((ylog == None) or (ylog == True)):
                axList[i].set_yscale("log")
            if xlog:
                axList[i].set_xscale("log")
            axList[i].grid(True)
            axList[i].set_xlabel("Frequency [Hz]")
            axList[i].set_ylabel(units[i])
            axList[i].set_title(titles[i])
            axList[i].autoscale_view(True, True, False)

    else:  # Not spectrum data
        for line in fileinput.input(dataFile):
            if line.strip()[0] == "#":
                continue  # Skip lines starting from #
            if firstLine:
                data = transpose(array([map(float, line.split())]))
                firstLine = False
            else:
                data = hstack((data, transpose(array([map(float, line.split())]))))

        # Plot non spectrum data
        numPlot = len(data) - 1
        fig = mpl.figure()
        fig.subplots_adjust(hspace=0.4)
        axList = []
        for i in range(numPlot):
            axList.append(fig.add_subplot(numPlot, 1, i + 1))
            axList[i].plot(data[0], data[i + 1])

            if (data[i + 1].min() > 0) and (ylog == True):
                axList[i].set_yscale("log")
            if xlog:
                axList[i].set_xscale("log")
            axList[i].grid(True)

            axList[i].set_xlabel("Frequency [Hz]")
            axList[i].set_ylabel(units[i])
            axList[i].set_title(titles[i])
            axList[i].autoscale_view(True, True, False)

    fig.show()
    return axList


def plotTFSR785(filename):
    """Plot TF data from SR785"""
    dataFile = filename + ".dat"
    paramFile = filename + ".par"

    # Read data
    firstLine = True
    for line in fileinput.input(dataFile):
        if line.strip()[0] == "#":
            continue  # Skip lines starting from #
        if firstLine:
            data = transpose(array([map(float, line.split())]))
            firstLine = False
        else:
            data = hstack((data, transpose(array([map(float, line.split())]))))

    fig = mpl.figure()
    #    fig.subplots_adjust(hspace=0.4)
    axList = []
    mag = fig.add_subplot(3, 1, 1)
    mag.plot(data[0], data[1])
    #    mag.set_yscale('log')
    mag.set_xscale("log")
    mag.grid(True)
    mag.set_ylabel("Mag [dB]")
    mag.set_title("Transfer function")
    mag.autoscale_view(True, True, False)

    phase = fig.add_subplot(3, 1, 2)
    phase.plot(data[0], data[2])
    phase.grid(True)
    phase.set_ylabel("Phase [deg]")
    phase.set_xscale("log")
    phase.autoscale_view(True, True, False)

    coh = fig.add_subplot(3, 1, 3)
    coh.hold(True)
    coh.plot(data[0], data[3], label="Norm Var 1")
    coh.plot(data[0], data[4], label="Norm Var 2")
    coh.grid(True)
    coh.set_xscale("log")
    coh.set_ylabel("Normalized Variance")
    coh.set_xlabel("Frequency [Hz]")
    coh.set_ylim(0, 1.03)
    coh.legend(loc=0)
    coh.autoscale_view(True, True, False)

    fig.show()

    return [mag, phase, coh]


def plotTSSR785(filename):
    """Plot TS data from SR785"""
    dataFile = filename + ".dat"
    paramFile = filename + ".par"

    # Read data
    firstLine = True
    timeSeries = True
    timeLinePat = re.compile(r"^#Time series")
    histLinePat = re.compile(r"^#Histogram")
    tDispID = -1
    hDispID = -1
    tsData = []
    hsData = []
    for line in fileinput.input(dataFile):
        if timeLinePat.match(line):  # Start of new time series
            firstLine = True
            timeSeries = True
            tDispID = tDispID + 1
            continue
        if histLinePat.match(line):  # Start of new histogram
            firstLine = True
            timeSeries = False
            hDispID = hDispID + 1
            continue

        if line.strip()[0] == "#":
            continue  # Skip lines starting from #
        if firstLine:
            if timeSeries:
                tsData.append(transpose(array([map(float, line.split())])))
            else:
                hsData.append(transpose(array([map(float, line.split())])))
            firstLine = False
        else:
            if timeSeries:
                tsData[tDispID] = hstack(
                    (tsData[tDispID], transpose(array([map(float, line.split())])))
                )
            else:
                hsData[hDispID] = hstack(
                    (hsData[hDispID], transpose(array([map(float, line.split())])))
                )

    numFig = len(tsData) + len(hsData)
    fig = mpl.figure()
    fig.subplots_adjust(hspace=0.4)
    axList = []
    for i in range(numFig / 2):  # Plot time series
        axList.append(fig.add_subplot(numFig / 2, numFig / 2, i + 1))
        axList[i].plot(tsData[i][0], tsData[i][1])
        axList[i].grid(True)
        axList[i].set_title("Time Series " + str(i + 1))
        axList[i].set_ylabel("V")
        axList[i].set_xlabel("sec")

    for i in range(numFig / 2):  # Plot histogram
        j = i + numFig / 2
        axList.append(fig.add_subplot(numFig / 2, numFig / 2, j + 1))
        axList[j].plot(hsData[i][0], hsData[i][1])
        axList[j].grid(True)
        axList[j].set_title("Histogram " + str(i + 1))
        axList[j].set_ylabel("Counts")
        axList[j].set_xlabel("V")

    fig.suptitle("Time series and histograms")

    fig.show()

    return axList


def plotSPAG4395A(filename, title, xlog=True, ylog=True, psdunits=False):
    """Plot downloaded spectrum data from AG4395A"""
    dataFile = filename + ".dat"
    paramFile = filename + ".par"

    # Read data
    firstLine = True
    for line in fileinput.input(dataFile):
        if line.strip()[0] == "#":
            continue  # Skip lines starting from #
        if firstLine:
            data = transpose(array([map(float, line.split())]))
            firstLine = False
        else:
            data = hstack((data, transpose(array([map(float, line.split())]))))

    fig = mpl.figure()
    #    fig.subplots_adjust(hspace=0.4)
    axList = []
    mag = fig.add_subplot(1, 1, 1)
    mag.plot(data[0], data[1])
    if ylog:
        mag.set_yscale("log")
    else:
        mag.set_yscale("linear")
    if xlog:
        mag.set_xscale("log")
    else:
        mag.set_xscale("linear")
    mag.grid(True)
    if psdunits:
        mag.set_ylabel("Vrms/rt(Hz)")
    else:
        mag.set_ylabel("Mag [dB]")
    mag.set_xlabel("Frequency [Hz]")
    mag.set_title(title)
    mag.autoscale_view(True)

    fig.show()

    return mag


def plotTFAG4395A(filename, title):
    """Plot TF data from AG4395A"""
    dataFile = filename + ".dat"
    paramFile = filename + ".par"

    # Read data
    firstLine = True
    for line in fileinput.input(dataFile):
        if line.strip()[0] == "#":
            continue  # Skip lines starting from #
        if firstLine:
            data = transpose(array([map(float, line.split())]))
            firstLine = False
        else:
            data = hstack((data, transpose(array([map(float, line.split())]))))

    fig = mpl.figure()
    #    fig.subplots_adjust(hspace=0.4)
    axList = []
    mag = fig.add_subplot(2, 1, 1)
    mag.plot(data[0], data[1])
    mag.set_xscale("log")
    mag.grid(True)
    mag.set_ylabel("Mag [dB]")
    mag.set_title(title)
    mag.autoscale_view(True, True)

    phase = fig.add_subplot(2, 1, 2)
    phase.plot(data[0], data[2])
    phase.grid(True)
    phase.set_ylabel("Phase [deg]")
    phase.set_xscale("log")
    phase.autoscale_view(True, True)

    fig.show()

    return [mag, phase]


def plotTFHP4195A(filename, title):
    """Plot TF data from HP4195A"""
    dataFile = filename + ".dat"

    # Read data
    firstLine = True
    for line in fileinput.input(dataFile):
        if line.strip()[0] == "#":
            continue  # Skip lines starting from #
        if firstLine:
            data = transpose(array([map(float, line.split())]))
            firstLine = False
        else:
            data = hstack((data, transpose(array([map(float, line.split())]))))

    fig = mpl.figure()
    #    fig.subplots_adjust(hspace=0.4)
    axList = []
    mag = fig.add_subplot(2, 1, 1)
    mag.plot(data[0], data[1])
    mag.set_xscale("log")
    mag.grid(True)
    mag.set_ylabel("Mag [dB]")
    mag.set_title(title)
    mag.autoscale_view(True, True)

    phase = fig.add_subplot(2, 1, 2)
    phase.plot(data[0], data[2])
    phase.grid(True)
    phase.set_ylabel("Phase [deg]")
    phase.set_xscale("log")
    phase.autoscale_view(True, True)

    fig.show()

    return [mag, phase]


def plotSPHP4195A(filename, title, xlog=True, ylog=True, psdunits=False):
    """Plot downloaded spectrum data from AG4395A"""
    dataFile = filename + ".dat"

    # Read data
    firstLine = True
    for line in fileinput.input(dataFile):
        if line.strip()[0] == "#":
            continue  # Skip lines starting from #
        if firstLine:
            data = transpose(array([map(float, line.split())]))
            firstLine = False
        else:
            data = hstack((data, transpose(array([map(float, line.split())]))))

    fig = mpl.figure()
    #    fig.subplots_adjust(hspace=0.4)
    axList = []
    mag = fig.add_subplot(1, 1, 1)
    mag.plot(data[0], data[1])
    if ylog:
        mag.set_yscale("log")
    else:
        mag.set_yscale("linear")
    if xlog:
        mag.set_xscale("log")
    else:
        mag.set_xscale("linear")
    mag.grid(True)
    if psdunits:
        mag.set_ylabel("uV/rt(Hz)")
    else:
        mag.set_ylabel("Mag [dBm]")
    mag.set_xlabel("Frequency [Hz]")
    mag.set_title(title)
    mag.autoscale_view(True)

    fig.show()

    return mag
