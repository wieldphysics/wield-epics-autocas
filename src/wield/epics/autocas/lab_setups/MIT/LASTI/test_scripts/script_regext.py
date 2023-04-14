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

float_re = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"

re_SOURCE = re.compile("^:SOURCE (.)$")
re_FREQVALUE = re.compile("^:CFRQ:VALUE ({0});INC {0}$".format(float_re))
re_LEVELVALUE = re.compile(
    "^:RFLV:UNITS DBM;TYPE (PD|EMF);VALUE ({0});INC {0};(ON|OFF)$".format(float_re)
)

print(re_LEVELVALUE.match(":RFLV:UNITS DBM;TYPE PD;VALUE -100.0;INC 1.0;ON").group(2))

re_FREQVALUE = re.compile(
    "^:CFRQ:VALUE ({0});INC ({0})(:?|;MODE FIXED)$".format(float_re)
)
print(re_FREQVALUE.match(":CFRQ:VALUE 200000000.0;INC 1000.0;MODE FIXED"))

re_DEVNVALUE = re.compile(
    "^:FM:DEVN ({0});(INT|EXTAC|EXTALC|EXTDC)\s*;(ON|OFF)\s*;INC ({0})$".format(
        float_re
    )
)
print(re_DEVNVALUE.match(":FM:DEVN 0.0;INT ;OFF ;INC 1000.0"))
