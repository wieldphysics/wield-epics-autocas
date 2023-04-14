#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""

import numpy as np
import pcaspy
import pcaspy.tools

from . import relay_values
from ..utilities.pprint import pprint


class CADriverServer(pcaspy.Driver):
    def _put_cb_generator_immediate(self, channel):
        def put_cb(value):
            self.setParam(channel, value)
            self.updatePVs()

        return put_cb

    def _put_cb_generator_deferred(self, channel):
        def put_cb(value):
            self.setParam(channel, value)
            self.updatePVs()
            pass

        return put_cb

    def _put_elem_cb_generator(self, channel, elem):
        def put_cb(value):
            use_entry = self.db_cas_raw[channel]
            # TODO 'value' maybe shouldn't be in this..
            use_entry[elem] = value
            # I "type" is included in setParamInfo, it crashes pcaspy
            dtemp = dict(use_entry)
            dtemp.pop("type", None)
            self.setParamInfo(channel, dtemp)

        return put_cb

    def __init__(self, db, reactor, saver=None, deferred_write_period=1 / 4.0):
        self.db = db
        self.reactor = reactor
        self.saver = saver

        self.cas = pcaspy.SimpleServer()
        self.cas_thread = pcaspy.tools.ServerThread(self.cas)
        self.cas_thread.daemon = True

        db_cas_raw = {}

        for channel, db_entry in self.db.items():
            # ignore the remote entries
            if db_entry["remote"]:
                # print('REMOTE')
                # print(channel, db_entry)
                continue
            rv = db_entry["rv"]
            entry_use = {}

            # provide a callback key so that we can avoid the callback during the write method
            # print("ENTRY", db_entry)
            if not db_entry["deferred"]:
                rv.register(
                    callback=self._put_cb_generator_immediate(channel),
                    key=self,
                )
            else:
                if deferred_write_period is not None and deferred_write_period > 0:
                    rv.register(
                        callback=self._put_cb_generator_deferred(channel),
                        key=self,
                    )
                else:
                    rv.register(
                        callback=self._put_cb_generator_immediate(channel),
                        key=self,
                    )

            # setup relays for any of the channel values to be inserted
            for elem in [
                "count",  # 1 	Number of elements
                "enums",  # [] 	String representations of the enumerate states
                "states",  # [] 	Severity values of the enumerate states.
                "prec",  # 0 	Data precision
                "unit",  # '' 	Physical meaning of data
                "lolim",  # 0 	Data low limit for graphics display
                "hilim",  # 0 	Data high limit for graphics display
                "low",  # 0 	Data low limit for alarm
                "high",  # 0 	Data high limit for alarm
                "lolo",  # 0 	Data low low limit for alarm
                "hihi",  # 0 	Data high high limit for alarm
                "adel",  # 0 	Archive deadband
                "mdel",  # 0 	Monitor,                    value change deadband
            ]:
                if elem in db_entry:
                    elem_val = db_entry[elem]
                    if isinstance(elem_val, relay_values.RelayValueDecl):
                        entry_use[elem] = elem_val.value
                        elem_val.register(
                            callback=self._put_elem_cb_generator(channel, elem)
                        )
                    else:
                        entry_use[elem] = elem_val
            for elem in [
                "type",  # 'float' PV data type. enum, string, char, float or int
                "scan",  # 0 	Scan period in second. 0 means passive
                "asyn",  # False 	Process finishes asynchronously if True
                "asg",  # '' 	Access security group name
                "value",  # 0 or '' 	Data initial value
            ]:
                if elem in db_entry:
                    elem_val = db_entry[elem]
                    entry_use[elem] = elem_val

            if "value" not in entry_use:
                entry_use["value"] = rv.value
            db_cas_raw[channel] = entry_use

        self.db_cas_raw = db_cas_raw
        # print("INT:")
        # dprint(self.db_cas_raw)
        # have to setup createPV before starting the driver
        self.cas.createPV("", self.db_cas_raw)
        super(CADriverServer, self).__init__()

        # pre-set all values, since this is apparently not done for you
        for channel, db_entry in self.db_cas_raw.items():
            self.setParam(channel, db_entry["value"])
            # If "type" is included in setParamInfo, it crashes pcaspy
            dtemp = dict(db_entry)
            dtemp.pop("type", None)
            self.setParamInfo(channel, dtemp)
        self.updatePVs()

        # the deferred writes will happen this often
        if deferred_write_period is not None and deferred_write_period > 0:
            self.reactor.enqueue_looping(
                self.updatePVs,
                period_s=deferred_write_period,
            )

        if self.saver is not None:
            self.saver.set_db_driver(self.db, self)
            self.saver.folders_make_ready()
            self.saver.load_snap()
        return  # ~__init__

    def write(self, channel, value):
        # NOTE: for enum records the value here is the numeric value,
        # not the string.  setParam() expects the numeric value.

        # reject writes to non-writable channels
        if self.db[channel]["interaction"] == "report":
            return False

        ctype = self.db[channel]["type"]
        ctype_strlike = False

        if ctype in ["string", "char"]:
            ctype_strlike = True

        # reject values that don't correspond to an actual index of
        # the enum
        # FIXME: this is apparently a feature? of cas that allows for
        # setting numeric values higher than the enum?
        if ctype == "enum" and (value >= len(self.db[channel]["enums"]) or value < 0):
            return False

        db = self.db[channel]
        rv = db["rv"]
        mt_assign = db.get("mt_assign", False)

        if self.saver is not None:
            urgentsave_s = db.get("urgentsave_s", None)
            if urgentsave_s is not None and urgentsave_s >= 0:
                self.saver.urgentsave_notify(channel, urgentsave_s)

        try:
            if mt_assign:
                rv.put_exclude_cb(value, key=self)
            else:
                with self.reactor.task_lock:
                    rv.put_exclude_cb(value, key=self)
        except relay_values.RelayValueCoerced as E:
            # print(value, type(value))
            value = E.preferred
            # print(value, type(value))
            if mt_assign:
                rv.put_valid_exclude_cb(E.preferred, key=self)
            else:
                with self.reactor.task_lock:
                    rv.put_valid_exclude_cb(E.preferred, key=self)

            self.setParam(channel, value)

            self.updatePVs()
            return False
        except relay_values.RelayValueRejected:
            return False
        else:
            self.setParam(channel, value)
            # self.updatePVs()
            return True

    def write_sync_typecast(self, channel, value):
        """
        This is a special write function for burt/autosave and other users of the synchronous system. It does two things different:

        A: it writes without grabbing the lock, since it should be called only with the lock held
        B: It typecasts its input values, this allows them to be input as strings from a burt loader
        """
        # NOTE: for enum records the value here is the numeric value,
        # not the string.  setParam() expects the numeric value.

        # reject writes to non-writable channels
        if self.db[channel]["interaction"] == "report":
            return False

        ctype = self.db[channel]["type"]
        ctype_strlike = False
        if ctype == "float":
            ccount = self.db[channel].get("count", 1)
            if ccount == 1:
                value = float(value)
            else:
                value = np.asarray(value, dtype=float)
        elif ctype == "int":
            ccount = self.db[channel].get("count", 1)
            if ccount == 1:
                try:
                    value = int(value)
                except ValueError:
                    value = float(value)
            else:
                value = np.asarray(value, dtype=int)
        elif ctype == "enum":
            try:
                value = int(value)
            except ValueError:
                value = self.db[channel]["enums"].index(value)
        elif ctype == "string":
            # should be happy
            value = str(value)
            ctype_strlike = True
        elif ctype == "char":
            # also should be happy as a str
            value = str(value)
            ctype_strlike = True

        # reject values that don't correspond to an actual index of
        # the enum
        # FIXME: this is apparently a feature? of cas that allows for
        # setting numeric values higher than the enum?
        if ctype == "enum" and (value >= len(self.db[channel]["enums"]) or value < 0):
            return False

        db = self.db[channel]
        rv = db["rv"]
        if self.saver is not None:
            urgentsave_s = db.get("urgentsave_s", None)
            if urgentsave_s is not None and urgentsave_s >= 0:
                self.saver.urgentsave_notify(channel, urgentsave_s)

        try:
            rv.put_exclude_cb(value, key=self)
        except relay_values.RelayValueCoerced as E:
            # print("COERCED")
            value = E.preferred
            rv.put_valid_exclude_cb(
                E.preferred,
                key=self,
            )

            self.setParam(channel, value)

            self.updatePVs()
            return False
        except relay_values.RelayValueRejected:
            return False
        else:
            self.setParam(channel, value)
            # self.updatePVs()
            return True

    def start(self):
        self.cas_thread.start()

    def stop(self):
        self.cas_thread.stop()
        # join needed to prevent a sigabrt in python3
        self.cas_thread.join()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
