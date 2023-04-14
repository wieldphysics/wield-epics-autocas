#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""

from wield import declarative
import numbers

import YALL.controls.epics as epics
import YALL.controls.core.contexts as contexts


class EpicsIndirectEBridge(
    epics.EpicsRelayUser,
):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @RELAY_EPICS.string_value_add("IN", length=60)
    @declarative.dproperty
    def rv_chn_in(self, rv=declarative.NOARG):
        """
        rv may be None
        """
        if rv is declarative.NOARG:
            rv = declarative.RelayValue("")
        return rv

    @RELAY_EPICS.string_value_add("OUT", length=60)
    @declarative.dproperty
    def rv_chn_out(self, rv=declarative.NOARG):
        """
        rv may be None
        """
        if rv is declarative.NOARG:
            rv = declarative.RelayValue("")
        return rv

    @RELAY_EPICS.float_value_add("VAL", precision=4, value=0)
    @declarative.dproperty
    def rv_relay(self, rv=declarative.NOARG):
        if rv is declarative.NOARG:
            rv = declarative.RelayValue(0)
        elif isinstance(rv, numbers.Number):
            rv = declarative.RelayValue(rv)
        elif isinstance(rv, str):
            rv = declarative.RelayValue(rv)
        return rv


class EpicsIndirectController(
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject,
):
    @declarative.dproperty
    def ebridge(self, val):
        val.rv_connect_mode.value = "master"
        val.state_connect.bool_register(self.state_connect_epics)
        return val

    # TODO: refactor these into a class
    @declarative.dproperty
    def rv_relay(self):
        return self.ebridge.rv_relay

    @declarative.dproperty
    def relay_setup(self):
        if self.ebridge.rv_chn_in is not None:
            print("SETUP:", self.ebridge.rv_chn_in)
            self.ebridge.rv_chn_in.register(
                callback=self.chn_cb_in,
                call_immediate=True,
            )
        if self.ebridge.rv_chn_out is not None:
            self.ebridge.rv_chn_out.register(
                callback=self.chn_cb_out,
                call_immediate=True,
            )

    _chn_link_in = None

    def chn_cb_in(self, value):
        print("HEY: ", value)
        if self._chn_link_in is not None:
            self._chn_link_in.state_connect.bool_register(
                self.state_connect_epics, remove=True
            )
            self._chn_link_in = None
        if not isinstance(value, (str, unicode)):
            return
        if value == "":
            return
        # self.rv_relay.value = 0
        # TODO make type-safe
        print("GOT ONE: ", value)
        link = epics.RelayPVLink(
            name=value,
            relay_val=self.rv_relay,
            binding_type="pull",
            timeout=1,
        )
        print(self.state_connect_epics)
        link.state_connect.bool_register(self.state_connect_epics)
        self._chn_link_in = link

    _chn_link_out = None

    def chn_cb_out(self, value):
        if self._chn_link_out is not None:
            self._chn_link_out.state_connect.bool_register(
                self.state_connect_epics, remove=True
            )
            self._chn_link_out = None
        if not isinstance(value, (str, unicode)):
            return
        if value == "":
            return
        # TODO make type-safe
        print("GOT ONE: ", value)
        link = epics.RelayPVLink(
            name=value,
            relay_val=self.rv_relay,
            binding_type="push",
            timeout=1,
        )
        link.state_connect.bool_register(self.state_connect_epics)
        self._chn_link_out = link
