#!/usr/bin/python2
"""
"""
import epics
from collections import deque
import time
import numpy as np

import declarative

import threading
from ..connectable import Connectable

from YALL.controls.core.coroutine.main_reactor import reactor
import collections

epics_pending_connections_lock = threading.Lock()
epics_pending_connections = set()
epics_pending_connections_event = threading.Event()
epics_pending_connections_event.set()

ca_element_count = epics.ca.element_count


def pending_epics_wait(max_wait_s = 10):
    if epics_pending_connections_event.wait(max_wait_s):
        return
    else:
        raise RuntimeError(
            ("Timed out waiting for Epics Variables to Connect, still left are: {0}"
             ).format(epics_pending_connections)
        )


class ValuePV(epics.PV):

    def __init__(self, name, *args, **kwargs):
        with epics_pending_connections_lock:
            epics_pending_connections.add(self)
            epics_pending_connections_event.clear()
            def first_CB_event_deferred(*value, **kwargs):
                def first_CB_event():
                    with epics_pending_connections_lock:
                        try:
                            epics_pending_connections.remove(self)
                            if not epics_pending_connections:
                                epics_pending_connections_event.set()
                            self.connection_callbacks.remove(first_CB_event_deferred)
                        except ValueError:
                            pass
                reactor.send_task(first_CB_event)
            super(ValuePV, self).__init__(name, *args, connection_callback = first_CB_event_deferred, **kwargs)
            #print "init:", self, self.chid
            #self.add_callback(callback = first_CB_event_deferred, index = epics_pending_connections_lock)
        return

    def disconnect(self):
        """
        Must override the py-epics function as it misses this monref reset
        """
        super(ValuePV, self).disconnect()
        self._monref = None

    def __del__(self):
        """
        pyepics is very aggressive about reinitializing. I have to prevent deletes if it accidentally
        reinits during shutdown or a crash occurs.
        """
        if epics and epics.ca.libca:
            super(ValuePV, self).__del__()
        #print "del:", self
        return

    def register(
        self,
        key            = None,
        callback       = None,
        remove         = False,
        call_immediate = False,
        full           = False
    ):
        if key is None:
            key = callback
        if key is None:
            raise RuntimeError("Must specify key (or at least callback)")
        #num_callbacks = len(self.callbacks)
        #if num_callbacks > 5:
            #print "{0} has {1} callbacks registered".format(self, num_callbacks)
        if not remove:
            if not isinstance(callback, collections.Callable):
                raise RuntimeError("appropriate callback not given")
            if full:
                def deferred(value, **kwargs):
                    reactor.send_task_partial(callback, value, **kwargs)
            else:
                def deferred(value, **kwargs):
                    #print("CB: ", self, value)
                    reactor.send_task_partial(callback, value)
            self.add_callback(callback = deferred, index = key)
            if call_immediate:
                if self.connected:
                    deferred(self.value)
        else:
            self.remove_callback(index = key)

    def callback_register(self, *args, **kwargs):
        return self.register(*args, **kwargs)


class RelayPVLinkBase(Connectable, declarative.OverridableObject):
    _pv = None

    BINDING_COMPLEMENTS = {
        'push' : 'pull',
        'pull' : 'push',
        'int'  : 'ext',
        'ign'  : 'ext',
        'ext'  : 'ext',
        'RO'   : 'pull',
    }

    def __init__(
        self,
        name,
        relay_val,
        binding_type    = None,
        start_connected = False,
        **kwargs
    ):
        #print "init:", self
        super(RelayPVLinkBase, self).__init__(**kwargs)
        #print("LINKING: ", name, binding_type)
        self.relay_val = relay_val
        self.name = name
        if binding_type is None:
            binding_type = 'ext'
        self.binding_type = binding_type
        self._update_num = 0
        #throw error early if not accepted
        self._init_map_ext_react()
        if start_connected:
            self.connect()
        return

    def check_PV_type(self):
        if self._pv.type in ['string', 'time_string', 'ctrl_string']:
            self._relay_value_convert_toPV = self._relay_value_convert_str_toPV
            self._relay_value_convert_fromPV = self._relay_value_convert_str_fromPV
        elif self._pv.type in ['char', 'time_char', 'ctrl_char']:
            self._relay_value_convert_toPV = self._relay_value_convert_char_toPV
            self._relay_value_convert_fromPV = self._relay_value_convert_char_fromPV
            self._value_external_react_RO = self._value_external_react_char_RO

    def _init_map_ext_react(self):
        return {
            'push' : self._value_external_init_push,
            'pull' : self._value_external_init_pull,
            'int'  : self._value_external_init_int,
            'ign'  : self._value_external_init_ign,
            'ext'  : self._value_external_init_ext,
            'RO'   : self._value_external_init_RO,
        }[self.binding_type]

    def _init_map_int_react(self):
        return {
            'push' : None,
            'pull' : None,
            'int'  : None,
            'ign'  : None,
            'ext'  : None,
            'RO'   : None,
        }[self.binding_type]

    def _state_connect_do(self, bstate):
        if bstate:
            super(RelayPVLinkBase, self)._state_connect_do(bstate)
            #print("CONNECT PV: ", self.name)
            self._pv = ValuePV(self.name, auto_monitor = True)
            self._value_external_react = self._init_map_ext_react()
            #print("ADD CB, ", self._pv, self._value_external_react)
            if self._value_external_react is not None:
                self._pv.add_callback(callback = self._deferred, index = self)
                if self._pv.connected:
                    self._deferred(self._pv.value)
            int_react = self._init_map_int_react()
            if int_react is not None:
                self.relay_val.register(
                    callback = int_react,
                )
        else:
            self._pv.remove_callback(index = self)
            try:
                self.relay_val.register(
                    callback = self._value_internal_react,
                    remove = True,
                )
            except KeyError:
                pass

            try:
                del self._value_external_react
            except AttributeError:
                pass
            try:
                del self._value_external_react_RO
            except AttributeError:
                pass

            self._pv.disconnect()
            del self._pv
            super(RelayPVLinkBase, self)._state_connect_do(bstate)

    def __del__(self):
        if epics.ca.libca:
            super(RelayPVLink, self).__del__()
        #print "DEL:", self
        return

    def _pv_put(self, val):
        try:
            self._pv.put(val)
            epics.ca.flush_io()
        except TypeError as e:
            print("{0} on {1}".format(e, self._pv))
        except AttributeError:
            print("pv call", self)

    def _deferred(self, value, **kwargs):
        self._update_num += 1
        #send with the current update number, so that if this registration occurs again before the current
        #react update has occured, it will be skipped to arrive at the more current value faster
        reactor.send_task_partial(self._value_external_react, value, unum = self._update_num)

    def _value_external_init_ext(self, val, unum = 999999999):
        self.check_PV_type()
        #print("VALUE REACT INIT EXT", val)
        try:
            del self._value_external_react
        except AttributeError:
            self._value_external_react(val, unum = unum)
        else:
            self._value_external_react(val, unum = unum)
            self.relay_val.register(
                callback = self._value_internal_react,
            )
        return

    def _value_external_init_int(self, val, unum = 999999999):
        self.check_PV_type()
        try:
            del self._value_external_react
        except AttributeError:
            self._value_external_react(val, unum = unum)
        else:
            self.relay_val.register(
                callback = self._value_internal_react,
            )
            self._pv_put(self._relay_value_convert_toPV(self.relay_val.value))
        return

    def _value_external_init_ign(self, val, unum = 999999999):
        self.check_PV_type()
        try:
            del self._value_external_react
        except AttributeError:
            self._value_external_react(val, unum = unum)
        else:
            self.relay_val.register(
                callback = self._value_internal_react,
            )
        return

    def _value_external_init_push(self, val, unum = 999999999):
        self.check_PV_type()
        try:
            del self._value_external_react
            #we don't actually want to react, so remove the callback
            self._pv.remove_callback(index = self)
        except AttributeError:
            self._value_external_react(val, unum = unum)
        else:
            self._value_external_react = self._value_internal_react_push
            self.relay_val.register(
                callback = self._value_internal_react,
                call_immediate = True,
            )
        return

    def _value_internal_react_push(self, val):
        raise RuntimeError("Shouldn't Hit This")

    def _value_external_init_pull(self, val, unum = 999999999):
        self.check_PV_type()
        try:
            del self._value_external_react
        except AttributeError:
            self._value_external_react(val, unum = unum)
        return

    def _value_external_init_RO(self, val, unum = 999999999):
        self.check_PV_type()
        self._value_external_react_RO(val, unum = unum)
        self._value_external_react = self._value_external_react_RO
        self.relay_val.register(
            callback = self._value_internal_react,
        )
        return

    def _value_external_react_RO(self, val, unum = 999999999):
        #check if there is already a new value waiting in the reactor and ignore the update if so
        if self._update_num > unum:
            return
        #TODO this may screw up for character arrays due to the custom _relay_value_convert_toPV
        rvalue = self._relay_value_convert_toPV(self.relay_val.value)
        if val != rvalue:
            #this callback can occassionally get called after the PV has disconnected, due to the async nature
            #of the PV callback mechanism, so protect against that case
            pv = self._pv
            if pv is not None:
                self._pv_put(rvalue)
        return

    def _value_external_react_char_RO(self, val, unum = 999999999):
        #check if there is already a new value waiting in the reactor and ignore the update if so
        if self._update_num > unum:
            return
        val = self._relay_value_convert_fromPV(val)
        #TODO this may screw up for character arrays due to the custom _relay_value_convert_toPV
        rvalue_PV = self._relay_value_convert_toPV(self.relay_val.value)
        rvalue = self._relay_value_convert_fromPV(rvalue_PV)
        if val != rvalue:
            #this callback can occassionally get called after the PV has disconnected, due to the async nature
            #of the PV callback mechanism, so protect against that case
            pv = self._pv
            if pv is not None:
                self._pv_put(rvalue_PV)
        return

    def _value_external_react(self, val, unum = 999999999):
        #check if there is already a new value waiting in the reactor and ignore the update if so
        if self._update_num > unum:
            return
        val = self._relay_value_convert_fromPV(val)
        try:
            self.relay_val.put(val)
        except declarative.RelayValueCoerced as e:
            newval = e.args[0]
            self.relay_val.put_valid(newval)
            #this callback can occassionally get called after the PV has disconnected, due to the async nature
            #of the PV callback mechanism, so protect against that case
            pv = self._pv
            if pv is not None:
                self._pv_put(newval)
        except declarative.RelayValueRejected:
            #this callback can occassionally get called after the PV has disconnected, due to the async nature
            #of the PV callback mechanism, so protect against that case
            pv = self._pv
            if pv is not None:
                self._pv_put(self._relay_value_convert_toPV(self.relay_val.value))
        return

    def _value_internal_react(self, val):
        #print("PUT: ", self._pv, val)
        self._pv_put(self._relay_value_convert_toPV(val))
        return

    def _relay_value_convert_fromPV(self, val):
        if hasattr(val, '__len__'):
            return val
        if not np.isfinite(val):
            return float('NaN')
        return val

    def _relay_value_convert_toPV(self, val):
        if hasattr(val, '__len__'):
            return val
        if val is None or not np.isfinite(val):
            return float('inf')
        return val

    def _relay_value_convert_str_fromPV(self, val):
        return val

    def _relay_value_convert_str_toPV(self, val):
        return val[:39]

    def _relay_value_convert_char_fromPV(self, val):
        try:
            try:
                firstnull  = list(val).index(0)
                cval = ''.join([chr(i) for i in val[:firstnull]])
            except ValueError:
                cval = ''.join([chr(i) for i in val])
            return cval
        except TypeError:
            #this error occures with pyepics returns a non-array single character
            return chr(val)

    def _relay_value_convert_char_toPV(self, val):
        if val == '':
            return []
        if self._pv:
            #the nelm property of pyepics.PV cannot be trusted since it overrides the count parameter
            nelm = ca_element_count(self._pv.chid)
            return [ord(c) for c in val[:nelm]]
        return []


class RelayPVLink(RelayPVLinkBase):
    _pv = None

    no_put = False
    def __init__(
        self,
        name,
        relay_val,
        binding_type    = None,
        start_connected = False,
        timeout         = 1.,
    ):
        self.timeout = timeout
        self._osc_stop = deque()
        super(RelayPVLink, self).__init__(
            name            = name,
            relay_val       = relay_val,
            binding_type    = binding_type,
            start_connected = start_connected,
        )
        return

    def _clean_osc_stop(self, time_now):
        #clear
        while self._osc_stop:
            _, top_time = self._osc_stop[0]
            if (time_now - top_time) > self.timeout:
                self._osc_stop.popleft()
            else:
                break
        return

    def _pv_put(self, val):
        time_now = time.time()
        self._clean_osc_stop(time_now)
        self._osc_stop.append((val, time_now))
        try:
            if self._pv.connected:
                self._pv.put(val)
        except AttributeError:
            print("pv call", self)
        return

    def _value_external_react(self, val, unum = 999999999):
        #check if there is already a new value waiting in the reactor and ignore the update if so
        if self._update_num > unum:
            return

        time_now = time.time()
        self._clean_osc_stop(time_now)
        val = self._relay_value_convert_fromPV(val)
        for prev_rvf, prev_time in self._osc_stop:
            if np.all(val == prev_rvf):
                #remove it if seen for lower-latency
                self._osc_stop.remove((prev_rvf, prev_time))
                #if this was a previous rvf, then ignore it
                #but make sure the current value is always reflected
                prev_value = self._relay_value_convert_toPV(self.relay_val.value)
                if np.any(val != prev_value):
                    self._osc_stop.append((prev_value, time_now))
                    #this callback can occassionally get called after the PV has disconnected, due to the async nature
                    #of the PV callback mechanism, so protect against that case
                    pv = self._pv
                    if pv is not None and not self.no_put:
                        pv.put(prev_value)
                return
        try:
            self.relay_val.put(val)
        except declarative.RelayValueCoerced as e:
            newval = e.args[0]
            self.relay_val.put_valid(newval)
            self._pv_put(newval)
        except declarative.RelayValueRejected:
            self._pv_put(self._relay_value_convert_toPV(self.relay_val.value))
        return


class RelayPVLinkRO(RelayPVLink):
    def __init__(
        self,
        name,
        relay_val,
        start_connected = False,
        timeout         = 1.,
    ):
        super(RelayPVLinkRO, self).__init__(
            name,
            relay_val,
            binding_type    = 'RO',
            start_connected = False,
            timeout         = 1.,
        )

