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
import contextlib

from .. import cascore


class RVError(cascore.CASUser):
    name_default = "ERR"

    @declarative.dproperty
    def rv_str(self):
        rv = cascore.RelayValueString("")
        self.cas_host(
            rv,
            "STR",
            unit="message",
            interaction="report",
        )
        return rv

    @declarative.dproperty
    def rv_level(self):
        rv = cascore.RelayValueInt(10000)
        self.cas_host(
            rv,
            "LEVEL",
            unit="level",
            interaction="report",
        )
        return rv

    @declarative.dproperty
    def rv_thresh(self):
        rv = cascore.RelayValueInt(10)
        self.cas_host(
            rv,
            "THR",
            unit="level",
            interaction="setting",
        )
        return rv

    @declarative.dproperty
    def rb_triggered(self):
        rb = cascore.RelayBool(False)
        self.cas_host(
            rb,
            "TRG",
            interaction="report",
        )
        return rb

    @declarative.dproperty
    def rb_clear(self):
        rb = cascore.RelayBool(False)
        self.cas_host(
            rb,
            "CLR",
            interaction="command",
        )

        def _clear_clear():
            rb.value = False

        def _clear_action(value):
            if value:
                self.rb_triggered.value = False
                self.reactor.send_task(_clear_clear)

        rb.register(callback=_clear_action)
        return rb

    _holding = False
    _level_temp = None
    _str_temp = None

    def __call__(self, level, msg):
        if self._holding:
            if self._level_temp is None or level < self._level_temp:
                self._level_temp = level
                self._str_temp = msg
            # do nothing if level is not superceded
        else:
            if level < self.rv_level.value:
                self.rv_level.value = level
                try:
                    self.rv_str.value = msg
                except cascore.RelayValueCoerced as E:
                    self.rv_str.put_valid(E.preferred)
                self.rb_triggered.value = True
            elif level == self.rv_level.value:
                try:
                    self.rv_str.value = msg
                except cascore.RelayValueCoerced as E:
                    self.rv_str.put_valid(E.preferred)

    def clear(self):
        self.rv_str.value = ""
        self.rv_level.value = self.rv_thresh.value
        self.rb_triggered.value = False
        return

    @contextlib.contextmanager
    def clear_pending(self):
        if self._holding:
            yield
        else:
            self._holding = True
            self._level_temp = None
            self._str_temp = None
            yield
            if self._level_temp is None or self._level_temp > self.rv_thresh.value:
                self.rv_str.value = ""
                self.rv_level.value = self.rv_thresh.value
                self.rb_triggered.value = False
            elif self._level_temp == self.rv_thresh.value:
                try:
                    self.rv_str.value = self._str_temp
                except cascore.RelayValueCoerced as E:
                    self.rv_str.put_valid(E.preferred)
            else:
                try:
                    self.rv_str.value = self._str_temp
                except cascore.RelayValueCoerced as E:
                    self.rv_str.put_valid(E.preferred)
                self.rv_level.value = self._level_temp
                self.rb_triggered.value = True
            del self._holding
