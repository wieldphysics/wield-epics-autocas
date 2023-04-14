#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
from labjack import ljm

# Driver Class for T7 Labjack with MUX80 multiplexer add-on.  Used for VPO-AUX channels.
class ljT7MUX80Driver(Driver):
    ljIPNumber = '18.120.0.66'

    @autocas.dproperty
    def AIN_PN_pairs(self):
        pChan = range(48,56)+range(64,72)+range(80,88)+range(96,104)+range(112,120) #Positive AIN LabJack Address
        nChan = range(56,64)+range(72,80)+range(88,96)+range(104,112)+range(120,128) #Negative AIN LabJack Address
        return zip(pChan, nChan)

    def  __init__(self, LJIPNumber, subsys):
        Driver.__init__(self)

        #Various Book keeping values for Multiplexed AIN channels...see self.setupLabJack() 
        #Also See MUX80 multiplexer Data sheet for info about channel number mappings
        #For differential readings
        self.numChannels = 40  #Total of 40 Differential Channels to be read
        self.numFrames = self.numChannels*3
        self.names = []
        self.aValues = []
        self.chanNames = [] # LabJack Channel Names for calls to ljm.eReadName...see setupLabJack()
        self.ljOK = False   # Keeps track of LabJack State

        self.subsys = subsys
        self.LJIP = LJIPNumber
        self.AINNames = ['_AIN%i'%n for n in range(40)] #EPICS AIN channel names

        # Setup binary channel lists for calls to ljm.eWriteName and ljm.eReadName
        # Also create parallel lists for their corresponding EPICS channel names
        self.bChanNames = ['FIO%i'%bout for bout in range(8)]+['MIO%i'%bout for bout in range(3)]+['CIO%i'%bout for bout in range(4)]+['EIO%i'%bout for bout in range(8)]#LabJack Convension
        self.BOUTNames = ['_BOUT%i'%n for n in range(len(self.bChanNames))] #EPICS convension

        self.setupLabJack()

    def setupLabJack(self):
            # Connect to T7
            print 'Connecting To LabJack: ' + self.subsys
            # Open first found T7 LabJack
            self.LJ = ljm.openS("T7", "ETHERNET", self.LJIP)    
            info = ljm.getHandleInfo(self.LJ)
            print("Opened a LabJack with Device type: %i, Connection type: %i,\n" \
                  "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" % \
                  (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

        # Set up the channels
        # Setup and call eWriteNames to configure AINs on the LabJack.
        for p in self.pChan:
        self.names = self.names+["AIN%d_NEGATIVE_CH"%p, "AIN%d_RANGE"%p, "AIN%d_RESOLUTION_INDEX"%p]
        self.chanNames = self.chanNames+["AIN%d"%p]
        for n in self.nChan:
                self.aValues = self.aValues+[n, 10, 0]  #+/-10V range with default resolution
                ljm.eWriteNames(self.LJ, self.numFrames, self.names, self.aValues)
                self.ljOK = True


    def restartLabJack(self):
        try:
                print("Connection error occurred.  Restarting the LabJack...")
                print("Actually, decided to die instead")
                #dying automatically
                sys.exit(-1)
                # Close the LabJack connection
                ljm.close(self.LJ)
                sleep(10)
                # reconnect to labjack
                self.LJ = ljm.openS("T7", "ETHERNET", self.LJIP)    

            info = ljm.getHandleInfo(self.LJ)
            print("Opened a LabJack with Device type: %i, Connection type: %i,\n" \
                  "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" % \
                  (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

            ljm.eWriteNames(self.LJ, self.numFrames, self.names, self.aValues)
            sleep(1)
            self.ljOK = True
        except Exception:
                print("LabJack is not fine yet")

    @catch_labjack_booboos_read
    def read(self, reason):
            #Strategy:  Read the AIN values from the LabJack directly when appropriate
            #       Otherwise just read old EPICS value if LabJack read command fails
            
        #If Necessary, read the appropriate AIN channel
        if reason in self.AINNames:
                #Have to convert from reason="_AINx" (EPICS convention) to name="AINy" (LabJack convention)
                #to read correct channel from multiplexed LabJack   
            if self.ljOK:
                try:
                        AINChanName = self.chanNames[self.AINNames.index(reason)]                     
                        value = ljm.eReadName(self.LJ, AINChanName)
                except:
                        value = self.getParam(reason)  #Default behavior when LabJack connection fails
                        self.ljOK = False              #LabJack needs to be restarted
            else:
                    value = self.getParam(reason) #Just reads old EPICS value when LabJack connection fails
        else:
                value = self.getParam(reason)  #Default for all other channels  
        return value

    @catch_labjack_booboos_write
    def write(self, reason, value):
            #Strategy:  Only write new EPICS values after LabJack write is successful
            #       Otherwise, just keep the old value
            
        status = True
        #Write LabJack Binary Outputs, if necessary
        if reason in self.BOUTNames:
                #Have to convert from reason="_BOUTx" (EPICS convention) to name="FI0y" (LabJack convention)
                #to read correct channel LabJack    
                BOUTChanName = self.bChanNames[self.BOUTNames.index(reason)]
            if self.ljOK:           
                try:            
                        ljm.eWriteName(self.LJ, BOUTChanName, value)
                        self.setParam(reason, value)
                except:
                        self.ljOK = False #LabJack Needs to be restarted
                        #Write LabJack Analog Outputs, if necessary
        elif reason == '_AOUT0':
            if self.ljOK:
                try:
                        ljm.eWriteName(self.LJ, 'DAC0', value)
                        self.setParam(reason, value)
                except:
                        self.ljOK = False #LabJack Needs to be restarted
        elif reason == '_AOUT1':
            if self.ljOK:
                try:
                        ljm.eWriteName(self.LJ, 'DAC1', value)
                        self.setParam(reason, value)
                except:
                        self.ljOK = False #LabJack needs to be restarted
        else:
                self.setParam(reason, value) #Default for all other channels
        return status





def casAUX():
        server = SimpleServer()
        prefix = 'M1:VPO-AUX'
    for n in range(40):
            server.createPV(prefix,db.genAuxdb('_AIN',n))
    for n in range(23):
            server.createPV(prefix,db.genAuxdb('_BOUT',n))
    for n in range(2):
        server.createPV(prefix,db.genAuxdb('_AOUT',n))
        server.createPV(prefix,db.WaveplatedB)
        #   driver = myDriver()
        #   while True:
        #       server.process(0.1) #Sample rate = 10 Hz

    driver = ljT7MUX80Driver(ljIPNumber, 'AUX')
    sleep(0.1)

    # process CA transactions
    while True:
        if driver.ljOK:#Check to make sure that LabJack connection is OK.  Restart if it isn't
                server.process(0.1) #Sample rate = 10Hz
        else:
                sleep(1)
                print('Aux LabJack Error!')
                driver.restartLabJack()
