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


gpibObj=netgpib.netGPIB("gpib5.mit.edu", 10, eot='\004')
gpibObj.connect()

gpibObj.command("*RST")

gpibObj.command('MGRP2,0') # Measurement Group = FFT
gpibObj.command('FBAS2,1') # Base Frequency = 102.4kHz
gpibObj.command('ISRC0') # Input = Analog

#Set up each display
# Display 0
gpibObj.command('MEAS0,11') # Frequency Resp 
gpibObj.command('VIEW0,0') # Disp 0 = LogMag
gpibObj.command('UNDB0,1') # dB ON
gpibObj.command('UNPK0,0') # PK Unit Off
gpibObj.command('DISP0,1') # Live display on

# Display 1

gpibObj.command('MEAS1,11') # Frequency Resp 
gpibObj.command('VIEW1,5') # Dsip 1 = Phase
gpibObj.command('UNDB1,0') # dB OFF
gpibObj.command('UNPK1,0') # PK Unit Off
gpibObj.command('UNPH1,0') # Phase Unit deg.
gpibObj.command('DISP1,1') # Live display on


gpibObj.command('TMOD1') # Auto trigger arming

gpibObj.command('TSRC3') # Trigger Source
gpibObj.command('TLVL10') # Sets trigger level in percent


gpibObj.command('TDLA1ms')


NO GOOD
gpibObj.command('TDLA,1')
gpibObj.command('TDLA1.0')
gpibObj.command('TDLA,1.0')
gpibObj.command('TDLA1s')

gpibObj.command('TDLA,'+options.delayA) # Delay for channel 1 in s
gpibObj.command('TDLB,'+options.delayB) # Delay for channel 2 in s


SSAM100mV
gpibObj.query('TDLA?')