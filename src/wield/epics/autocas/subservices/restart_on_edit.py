#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


import sys
import os
from os import path

# TODO import this later or make it failsafe
import inotify_simple

from .. import cascore


class RestartOnEdit(cascore.CASUser):
    _myinotify = None

    poll_rate_s = 1

    @cascore.dproperty
    def policy(self, val="EXIT"):
        assert val in ["EXIT", "REPLACE"]
        return val

    @cascore.dproperty
    def setup_action(self):
        self.reactor.enqueue(self._startup_task, future_s=3)

    def _startup_task(self):
        modfiles = modlist(
            ignores=self.ignore_list,
            accepts=self.accept_list,
        )
        inotify = inotify_simple.INotify()
        for fpath in modfiles:
            try:
                inotify.add_watch(fpath, inotify_simple.flags.MODIFY)
            except OSError as E:
                print("inotify error: ", E)
        # also check the config files
        for fpath in self.root.config_files:
            try:
                inotify.add_watch(fpath, inotify_simple.flags.MODIFY)
            except OSError as E:
                print("inotify error: ", E)
        self._myinotify = inotify

        self.reactor.enqueue_looping(self._loop_check_task, period_s=self.poll_rate_s)

    def _loop_check_task(self):
        events = self._myinotify.read(timeout=0)
        # only modify is registered
        if events:
            print("RestartOnEdit noticed a modified file on inotify!")
            if self.policy == "REPLACE":
                print("RESTARTING and REPLACING process")
                os.execv(
                    sys.executable,
                    ["python{v.major}.{v.minor}".format(v=sys.version_info)] + sys.argv,
                )
            elif self.policy == "EXIT":
                print("Exiting Process")
                sys.exit(0)

    @cascore.dproperty_ctree(default=lambda self: default_ignores())
    def ignore_list(self, lval):
        """
        List of substrings that will cause the inotify system to ignore python packages
        """
        assert isinstance(lval, (list, tuple))
        for val in lval:
            assert isinstance(val, str)
        return lval

    @cascore.dproperty_ctree(default=lambda self: [])
    def accept_list(self, lval):
        """
        List of substrings that will cause the inotify system to accept python packages even if they match the ignore list.
        """
        assert isinstance(lval, (list, tuple))
        for val in lval:
            assert isinstance(val, str)
        return lval


def default_ignores():
    pyname = "python{v.major}.{v.minor}".format(v=sys.version_info)
    return [pyname, "site-packages"]


def modlist(include_pyc=True, ignores=None, accepts=[]):
    if ignores is None:
        ignores = default_ignores()

    mods = []
    for _modname, mod in sys.modules.items():
        if mod is not None:
            try:
                fname = mod.__file__
            except AttributeError:
                continue
            if fname is None:
                continue
            else:
                pbase, pext = path.splitext(fname)
                if pext in [".py", ".pyc"]:
                    fnamepy = pbase + ".py"
                    fnamepyc = pbase + ".py"

                    skip = False
                    for ignore in ignores:
                        if ignore in fnamepy:
                            skip = True
                            break

                    for accept in accepts:
                        if accept in fnamepy:
                            skip = False
                            break
                    if skip:
                        continue

                    mods.append(fnamepy)
                    if include_pyc:
                        mods.append(fnamepyc)
    return mods
