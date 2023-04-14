#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


from .. import cascore
from . import cas_time


def time_validator(val):
    assert val in ["UNIX", "GPS"]
    return val


class ProgramSettings(cascore.CASUser):
    @cascore.dproperty_ctree(default="GPS", validator=time_validator)
    def time_convention(self, val):
        return val


class ProgramStatus(cascore.CASUser):
    """
    Service class which hosts variables related to the status of standard subcomponents of a CAS System. This includes

    reactor latency
    reactor queue depth
    last reactor fault

    last burt time

    number of missing remote PVs, with names for first 5 missing.
    number of hosted PVs
    hostname
    version
    software-hash
    config-hash
    cpu usage of program (maybe).

    global error status
    """

    @cascore.dproperty
    def rv_reactor_latency_ms(self):
        rv = cascore.RelayValueFloat(-1)
        self.cas_host(
            rv,
            "REACTOR_LAT_MS",
            unit="milliseconds",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_reactor_rate(self):
        rv = cascore.RelayValueInt(-1)
        self.cas_host(
            rv,
            "REACTOR_RATE",
            unit="number",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_reactor_fill(self):
        rv = cascore.RelayValueInt(-1)
        self.cas_host(
            rv,
            "REACTOR_FILL",
            unit="number",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_reactor_canary(self):
        dt = cas_time.CASDateTime(parent=self, name="REACTOR_FAULT")
        return dt

    @cascore.dproperty
    def rv_PVs_missing(self):
        rv = cascore.RelayValueInt(0)
        self.cas_host(
            rv,
            "PVS_MISSING",
            unit="number",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_PVs_bad(self):
        rv = cascore.RelayValueInt(0)
        self.cas_host(
            rv,
            "PVS_BAD",
            unit="number",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_PVs_hosted(self):
        rv = cascore.RelayValueInt(0)
        self.cas_host(
            rv,
            "PVS_HOSTED",
            unit="number",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_PVs_connected(self):
        rv = cascore.RelayValueInt(0)
        self.cas_host(
            rv,
            "PVS_REMOTE",
            unit="number",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_about_hostname(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "HOSTNAME",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_about_version(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "VERSION",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_about_cpu(self):
        rv = cascore.RelayValueFloat(-1)
        self.cas_host(
            rv,
            "CPU_USAGE",
            unit="percentage",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_about_softhash(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "ABOUT_SOFTHASH",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_about_confhash(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "ABOUT_CONFHASH",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def rv_about_softhash_user(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "ABOUT_SOFTHASH_USE",
            interaction="setting",
        )
        return rv

    @cascore.dproperty
    def rv_about_confhash_user(self):
        rv = cascore.RelayValueString("<TODO>")
        self.cas_host(
            rv,
            "ABOUT_CONFHASH_USE",
            interaction="setting",
        )
        return rv

    @cascore.dproperty
    def rv_burt_time(self):
        dt = cas_time.CASDateTime(parent=self, name="BURT_TIME")

        def notify(time_now, time_epoch):
            dt.update_unix_time(time_now)

        self.root.autosave.save_notify.register(
            callback=notify,
        )
        return dt
