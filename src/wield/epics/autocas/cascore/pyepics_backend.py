#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import epics
import time
import numpy as np

from wield import declarative

import warnings

from . import relay_values

ca_element_count = epics.ca.element_count


class CAEpicsClient(declarative.OverridableObject):
    @declarative.callbackmethod
    def connections_changed(self):
        # print("ECONN: ", self.epics_pending_connections)
        return

    @declarative.dproperty
    def epics_pending_connections(self):
        """
        Stores the list of PVs known to not be connected
        """
        return set()

    @declarative.dproperty
    def epics_bad_connections(self):
        """
        List of PV's with bad connections or types
        """
        return dict()

    @declarative.dproperty
    def pending_writes(self):
        """
        set of (RV, PV) tuples needing to commit values to PVs
        """
        return set()

    @declarative.dproperty
    def pending_reads(self):
        """
        set of (RV, PV) tuples needing to commit values to RVs
        """
        return set()

    @declarative.dproperty
    def PV_RV_map(self):
        """
        Stores the mapping of PVs to RVs
        """
        return {}

    PV_update_rateconst_s = 10

    @declarative.dproperty
    def PV_update_rateFOM(self):
        """
        Stores a FOM consisting of (tintR, mtime) to represent how often on
        average the PV is changing. tintR is the inverse change rate,
        mtime is the last change time.
        """
        return {}

    @declarative.dproperty
    def PV_putfails(self):
        """
        Stores a FOM consisting of (tintR, mtime) to represent how often on
        average the PV is changing. tintR is the inverse change rate,
        mtime is the last change time.
        """
        return {}

    PV_put_rateconst_s = 10

    @declarative.dproperty
    def PV_put_rateFOM(self):
        """
        Stores a FOM consisting of (tintR, mtime) to represent how often on
        average the PV is changing. tintR is the inverse change rate,
        mtime is the last change time.
        """
        return {}

    @declarative.dproperty
    def RV_connection_attached(self):
        """
        Stores a mapping from pvs to bools indicating that the connection
        is live and attached. This helps with the transition to/from fully
        connected
        """
        return {}

    @declarative.dproperty
    def RV_PV_map(self):
        """
        Stores the inverse mapping
        """
        return {}

    def __init__(
        self,
        db,
        reactor,
        saver=None,
        deferred_write_period=1 / 4.0,  # TODO, make this a configurable
        **kwargs
    ):
        super(CAEpicsClient, self).__init__(**kwargs)
        self.db = db
        self.reactor = reactor
        self.saver = saver

        db_cas_raw = {}
        rvdb_cas_raw = {}

        for channel, db_entry in self.db.items():
            # use only the remote entries
            if not db_entry.get("remote", False):
                continue

            rv = db_entry["rv"]
            entry_use = {"rv": rv}

            self.RV_connection_attached[rv] = False
            # provide a callback key so that we can avoid the callback during the write method
            if not db_entry["deferred"]:
                rv.register(
                    callback=self._put_cb_generator_immediate(rv),
                    key=self,
                )
            else:
                if deferred_write_period is not None and deferred_write_period > 0:
                    rv.register(
                        callback=self._put_cb_generator_deferred(rv),
                        key=self,
                    )
                else:
                    rv.register(
                        callback=self._put_cb_generator_immediate(rv),
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
                "mdel",  # 0 	Monitor, value change deadband
            ]:
                if elem in db_entry:
                    elem_val = db_entry[elem]
                    if isinstance(elem_val, relay_values.RelayValueDecl):
                        # TODO add this functionality
                        raise NotImplementedError()
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
            rvdb_cas_raw[rv] = entry_use

            # writable = db_entry['writable']

        self.db_cas_raw = db_cas_raw
        self.rvdb_cas_raw = rvdb_cas_raw
        # have to setup createPV before starting the driver

        # the deferred writes will happen this often
        if deferred_write_period is not None and deferred_write_period > 0:
            self.reactor.enqueue_looping(
                self.write_pending,
                period_s=deferred_write_period,
            )

        return  # ~__init__

    def _put_cb_generator_immediate(self, rv):
        def put_cb(value):
            # a python2 safety as unicode objects crash the CAS
            self.xfer_RV_to_PV(rv)

        return put_cb

    def _put_cb_generator_deferred(self, rv):
        def put_cb(value):
            pv = self.RV_to_PV[rv]
            self.pending_writes.add((rv, pv))
            pass

        return put_cb

    def _conn_cb_generator_deferred(self, rv):
        """
        This gets called from the epics thread
        """

        def first_CB_event_deferred(*value, **kwargs):
            conn = kwargs.get("conn", None)
            pv = self.RV_PV_map[rv]
            if conn is None:
                return
            elif conn:

                def conn_task():
                    self._connection_start(rv, pv)

            else:

                def conn_task():
                    self._connection_end(rv, pv)

            self.reactor.send_task(conn_task)
            return

        return first_CB_event_deferred

    def start(self):
        for chn, db in self.db_cas_raw.items():
            rv = db["rv"]
            pv = epics.PV(
                chn,
                connection_callback=self._conn_cb_generator_deferred(rv),
                auto_monitor=True,
            )

            def cb_gen(rv, pv):
                def update_cb_reactor():
                    # TODO, deal with deferred type
                    self.xfer_PV_to_RV(rv, pv)
                    return

                # this callback runs in the epics thread, so enqueue
                # it in the reactor to be in the main thread
                def update_cb(value, *args, **kwargs):
                    return self.reactor.send_task(update_cb_reactor)

                return update_cb

            pv.add_callback(callback=cb_gen(rv, pv), index=self)

            # register the PV as wanting a connection
            self.epics_pending_connections.add(pv)
            self.PV_RV_map[pv] = rv
            self.RV_PV_map[rv] = pv
        self.connections_changed()
        return

    def stop(self):
        return
        for pv, rv in self.PV_RV_map.items():
            pv.disconnect()
            pv.connection_callbacks[:] = []
            pv.clear_callbacks()
            # rv.register(key = self, remove = True)

        self.PV_RV_map.clear()
        self.RV_PV_map.clear()
        self.pending_reads.clear()
        self.pending_writes.clear()
        self.epics_pending_connections.clear()
        self.epics_bad_connections.clear()
        return

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _connection_start(self, rv, pv):
        """
        Checks the PV types
        """
        if pv not in self.epics_pending_connections:
            warnings.warn("WARNING SHOULDNT GET CALLED")
            return

        # TODO Check type and update the bad connections
        # print(pv.type)

        channel = pv.pvname
        value = pv.value
        db = self.db[channel]

        interaction = db["interaction"]
        if interaction == "report":
            self.xfer_RV_to_PV(rv, pv)
        elif interaction == "command":
            self.xfer_RV_to_PV(rv, pv)
        elif interaction == "internal":
            self.xfer_RV_to_PV(rv, pv)
        elif interaction == "external":
            self.xfer_PV_to_RV(rv, pv)
        elif interaction == "setting":
            self.xfer_PV_to_RV(rv, pv)
        else:
            raise RuntimeError("Unknown interaction type")

        self.RV_connection_attached[rv] = True
        self.epics_pending_connections.remove(pv)
        self.connections_changed()
        return

    def _connection_end(self, rv, pv):
        if pv in self.epics_pending_connections:
            # this is OK, since it means that it was unregistered by a method
            # noticing that "conn" was unset
            # warnings.warn("WARNING SHOULDNT GET CALLED")
            return

        self.RV_connection_attached[rv] = False
        self.epics_pending_connections.add(pv)
        self.connections_changed()
        return

    def write_pending(self):
        for rv in self.pending_writes:
            self.xfer_RV_to_PV(rv)
        self.pending_writes.clear()

    def read_pending(self):
        for pv in self.pending_reads:
            self.xfer_PV_to_RV(pv)
        self.pending_reads.clear()

    def xfer_PV_to_RV(self, rv, pv):
        """ """
        if not self.RV_connection_attached[rv]:
            # the connection start code must apply the first PV_to_RV transfer
            # based on the interaction type set for the rv cas_host
            return
        channel = pv.pvname
        value = pv.value
        db = self.db[channel]

        tnow = time.time()
        tintR, tlast = self.PV_update_rateFOM.get(pv, (0, 0))
        tdiff = tnow - tlast
        weight = np.exp(-tdiff / self.PV_update_rateconst_s)
        tintR = (1 - weight) / tdiff + weight * tintR
        self.PV_update_rateFOM[pv] = (tintR, tnow)

        # reject writes to non-writable channels
        if db["interaction"] == "report":
            # should put the OLD value back into the PV
            # TODO, should this depend on interaction_type
            self.xfer_RV_to_PV(rv, pv)
            return

        if self.saver is not None:
            urgentsave_s = db.get("urgentsave_s", None)
            if urgentsave_s is not None and urgentsave_s >= 0:
                self.saver.urgentsave_notify(channel, urgentsave_s)

        try:
            rv.put_exclude_cb(value, key=self)
        except relay_values.RelayValueCoerced as E:
            pref_value = E.preferred
            # it should NOT exclude the callback, so that the changed
            # value gets updated into the PV
            # this is like calling put_exclude_cb, then xfer_RV_to_PV
            rv.put_valid(pref_value)
        except relay_values.RelayValueRejected:
            # should put the OLD value back into the PV
            # TODO, should this depend on interaction_type
            self.xfer_RV_to_PV(rv, pv)
        return

    def xfer_RV_to_PV(self, rv, pv):
        if not pv.connected or not self.RV_connection_attached[rv]:
            return

        channel = pv.pvname
        db = self.db[channel]
        # TODO, determine if interaction type should affect this method.

        if not pv.put_complete:
            Nlast = self.PV_putfails.get(pv, 0)
            self.PV_putfails[pv] = Nlast + 1

        tnow = time.time()
        tintR, tlast = self.PV_put_rateFOM.get(pv, (0, 0))
        tdiff = tnow - tlast
        weight = np.exp(-tdiff / self.PV_put_rateconst_s)
        tintR = (1 - weight) / tdiff + weight * tintR
        self.PV_put_rateFOM[pv] = (tintR, tnow)

        pv.put(rv.value, wait=False)
        return

    def check_pending_connections(self):
        # TODO, make something to check that the pending connections list is
        # up-to-date
        raise NotImplementedError()
