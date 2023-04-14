#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""


from wield import declarative
from wield.bunch import Bunch

from . import relay_values
from . import instacas

# from . import utilities


class SerialError(Exception):
    pass


class SerialConnection(
    instacas.CASUser,
):
    @declarative.dproperty
    def rb_connected(self):
        rb = relay_values.RelayBool(False)
        self.cas_host(
            rb,
            name="CONNECT",
            interaction="report",
        )
        return rb

    @declarative.dproperty
    def rb_running(self):
        rb = relay_values.RelayBool(False)
        self.cas_host(
            rb,
            name="RUNNING",
            interaction="report",
        )
        return rb

    @declarative.dproperty
    def rb_queued(self):
        rb = relay_values.RelayBool(False)
        self.cas_host(
            rb,
            name="QUEUED",
            interaction="report",
        )
        return rb

    @declarative.dproperty
    def rv_error(self):
        rv = relay_values.RelayValueString("")
        self.cas_host(
            rv,
            name="ERROR",
            interaction="report",
        )
        return rv

    @declarative.dproperty
    def _block_data(self):
        return dict()

    @declarative.dproperty
    def _blocks_queued(self):
        return []

    def cmd_object(self):
        b = Bunch()

        def writeline(line):
            print("SERIAL: ", line)

        b.writeline = writeline

        def readline():
            return "100"

        b.readline = readline
        return b

    def block_enqueue(self, blockfunc):
        self._block_data[blockfunc]
        self._blocks_queued.append(blockfunc)

        self.reactor.enqueue_limited(self.run, future_s=0.1, limit_s=1)

    def block_add(
        self,
        func,
        ordering=None,
        parent=None,
        chain=[],
        name=None,
        prefix=None,
    ):
        """
        if ordering is None then it may LAST or FIRST - NO GUARANTEE, otherwise they are sorted by ordering

        returns a key-function that can be enqueued to indicate to run the serial block in its correct context. If called it enqueues itself
        """

        def block_func():
            self.block_enqueue(block_func)

        if name is not None:
            if prefix is not None:
                name = "_".join(list(prefix) + [name])
            block_func.__name__ = str(name)

        self._block_data[block_func] = dict(
            func=func,
            ordering=ordering,
            parent=parent,
            chain=list(chain),
        )
        # can add to chain later
        return block_func

    def block_chain(self, bfunc, *chains):
        # TODO check that the chains are also block-functions
        self._block_data[bfunc]["chain"].extend(chains)

    def run(self):
        """
        generates the block-chain run tree and serial command object through the block-parents and chains. Doesn't need to check for parent loop because that is prevented currently
        through the block creation convention that parents are specified.
        """
        self.rb_running.assign(True)

        # first to bfunc completion
        checked = set()
        stack = list(self._blocks_queued)
        # clear the previous list
        self._blocks_queued[:] = []

        plists = {None: []}
        while stack:
            bfunc = stack.pop()
            if bfunc in checked:
                continue
            # plists[bfunc] = []
            checked.add(bfunc)
            bdata = self._block_data[bfunc]
            stack.extend(bdata["chain"])

            bparent = bdata["parent"]
            plist = plists.setdefault(bparent, [])
            plist.append(bfunc)
            if bparent is not None:
                stack.append(bparent)

        cmd = self.cmd_object()
        # utilities.dprint(plists)

        # get first list
        def block_call(bfunc):
            plist = plists.get(bfunc, [])
            plist.sort(key=lambda bfunc: self._block_data[bfunc]["ordering"])
            for bfunc in plist:
                was_called = [False]

                def remainder_call():
                    was_called[0] = True
                    return block_call(bfunc)

                cmd.block_remainder = remainder_call
                self._block_data[bfunc]["func"](cmd)
                cmd.block_remainder = None
                if not was_called[0]:
                    remainder_call()

        # call on the root parent
        block_call(None)
        # the block list is a sequence of bfunc, list pairs. The bfunc serial functions are called and any associated inner blocks are in the following sequence
        self.rb_running.assign(False)
        self.rb_queued.assign(False)
