#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


import time
import datetime

from .. import cascore


class CASDateTime(cascore.CASUser):
    @cascore.dproperty
    def rv_str(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "STR",
            unit="datetime",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_float(self, default=0):
        rv = cascore.RelayValueFloat(default)
        self.cas_host(
            rv,
            "ORD",
            unit=self.root.settings.time_convention,
            interaction="report",
        )
        return rv

    def update_unix_time(self, unix_time):
        if self.root.settings.time_convention == "UNIX":
            self.rv_float.value = unix_time
        elif self.root.settings.time_convention == "GPS":
            # LIGO library
            import gpstime

            self.rv_float.value = gpstime.unix2gps(unix_time)
        dt = datetime.datetime.fromtimestamp(unix_time)
        self.rv_str.value = dt.strftime("%X %x")

    def update_now(self):
        self.update_unix_time(time.time())
