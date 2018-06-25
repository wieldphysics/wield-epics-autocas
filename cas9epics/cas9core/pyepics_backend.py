#!/usr/bin/python2
"""
"""
import epics
from collections import deque
import time
import numpy as np

import declarative

import threading
import warnings
import collections

from . import relay_values

ca_element_count = epics.ca.element_count

class CAEpicsClient(declarative.OverridableObject):
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
        List of RVs needing to commit values to PVs
        """
        return set()

    @declarative.dproperty
    def pending_reads(self):
        """
        List of PVs needing to commit values to RVs
        """
        return set()

    @declarative.dproperty
    def PV_RV_map(self):
        """
        Stores the mapping of PVs to RVs
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
            saver = None,
            deferred_write_period = 1/4.
    ):
        self.db      = db
        self.reactor = reactor
        self.saver   = saver

        db_cas_raw = {}

        for channel, db_entry in self.db.items():
            #use only the remote entries
            if not db_entry.get('remote', False):
                continue

            rv = db_entry['rv']
            entry_use = {
                'rv' : rv
            }

            #provide a callback key so that we can avoid the callback during the write method
            if db_entry.get('immediate', True):
                rv.register(
                    callback = self._put_cb_generator_immediate(rv),
                    key = self,
                )
            else:
                if deferred_write_period is not None and deferred_write_period > 0:
                    rv.register(
                        callback = self._put_cb_generator_deferred(rv),
                        key = self,
                    )
                else:
                    rv.register(
                        callback = self._put_cb_generator_immediate(rv),
                        key = self,
                    )

            #setup relays for any of the channel values to be inserted
            for elem in [
                    #"type" 	,  # 'float' PV data type. enum, string, char, float or int
                    "count" 	,  # 1 	Number of elements
                    "enums" 	,  # [] 	String representations of the enumerate states
                    "states" 	,  # [] 	Severity values of the enumerate states.
                    "prec",     # 0 	Data precision
                    "unit",     # '' 	Physical meaning of data
                    "lolim" 	,  # 0 	Data low limit for graphics display
                    "hilim" 	,  # 0 	Data high limit for graphics display
                    "low",     # 0 	Data low limit for alarm
                    "high",     # 0 	Data high limit for alarm
                    "lolo",     # 0 	Data low low limit for alarm
                    "hihi",     # 0 	Data high high limit for alarm
                    "adel",     # 0 	Archive deadband
                    "mdel",     # 0 	Monitor,                    value change deadband
                    #"scan", #  0 	Scan period in second. 0 means passive
                    #"asyn", #  False 	Process finishes asynchronously if True
                    #"asg",     #  '' 	Access security group name
                    #"value",  # 0 or '' 	Data initial value
            ]:
                if elem in db_entry:
                    elem_val = db_entry[elem]
                    if isinstance(elem_val, relay_values.RelayValueDecl):
                        #TODO add this functionality
                        raise NotImplementedError()
                        entry_use[elem] = elem_val.value
                        elem_val.register(
                            callback = self._put_elem_cb_generator(channel, elem)
                        )

            if 'value' not in entry_use:
                entry_use['value'] = rv.value
            db_cas_raw[channel] = entry_use

            #writable = db_entry['writable']
        self.db_cas_raw = db_cas_raw
        #have to setup createPV before starting the driver

        #the deferred writes will happen this often
        if deferred_write_period is not None and deferred_write_period > 0:
            self.reactor.enqueue_looping(
                self.write_pending,
                period_s = deferred_write_period,
            )

        #print("CAS RAW", self.db, self.db_cas_raw)

        return  # ~__init__

    def _put_cb_generator_immediate(self, rv):
        def put_cb(value):
            #a python2 safety as unicode objects crash the CAS
            self.write_RV_to_PV(rv)
        return put_cb

    def _put_cb_generator_deferred(self, rv):
        def put_cb(value):
            self.pending_writes.add(rv)
            pass
        return put_cb

    def _conn_cb_generator_deferred(self, rv):
        """
        This gets called from the epics thread
        """
        def first_CB_event_deferred(*value, **kwargs):
            conn = kwargs.get('conn', None)
            pv = self.RV_PV_map[rv]
            print(pv, "connect: ", conn)
            if conn is None:
                return
            elif conn:
                def conn_task():
                    print("CONN: ", pv)
                    self._setup_callbacks(rv, pv)
            else:
                def conn_task():
                    print("DISCONN: ", pv)
                    self._remove_callbacks(rv, pv)
            self.reactor.send_task(conn_task)
            return
        return first_CB_event_deferred

    def start(self):
        for chn, db in self.db_cas_raw.items():
            rv = db['rv']
            pv = epics.PV(
                chn,
                connection_callback = self._conn_cb_generator_deferred(rv),
                auto_monitor = True,
            )

            def _test_cb(value, *args, **kwargs):
                print("IMMED:", rv, value)
            pv.add_callback(callback = _test_cb)
            #register the PV as wanting a connection
            self.epics_pending_connections.add(pv)
            self.PV_RV_map[pv] = rv
            self.RV_PV_map[rv] = pv
        return

    def stop(self):
        return

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _setup_callbacks(self, rv, pv):
        """
        Checks the PV types
        """
        if pv not in self.epics_pending_connections:
            warnings.warn("WARNING SHOULDNT GET CALLED")
            return

        print(pv.type)

        def _test_cb(value, *args, **kwargs):
            print("SETUP CB", rv, value)
        print("SETUP: ", rv, pv)
        pv.add_callback(callback = _test_cb)

        self.epics_pending_connections.remove(pv)
        return

    def _remove_callbacks(self, rv, pv):
        if pv in self.epics_pending_connections:
            #this is OK, since it means that it was unregistered by a method noticing that "conn" was unset
            #warnings.warn("WARNING SHOULDNT GET CALLED")
            return

        #pv.remove_callback(index = self)

        rv.register(key = self, remove = True)
        self.epics_pending_connections.add(pv)
        return

    def write_pending(self):
        for rv in self.pending_writes:
            self.write_RV_to_PV(rv)
        self.pending_writes.clear()

    def read_pending(self):
        for pv in self.pending_reads:
            self.PV_to_RV(pv)
        self.pending_reads.clear()

    def PV_to_RV(self, rv):
        return

    def RV_to_PV(self, rv):
        return

    def check_pending_connections(self):
        #TODO, make something to check that the pending connections list is up-to-date
        raise NotImplementedError()

