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
import sys
import os
import datetime
import time
import errno
from os import path

from .. import cascore
from . import autosave_base

save_programs = dict(
    gzip=["gzip"],
    bzip2=["bzip2"],
)

load_programs = dict(
    gzip=["gzip", "-c", "-d"],
    bzip2=["bzip2", "-c", "-d"],
)

suffix_programs = {
    ".gz": "gzip",
    ".bz": "bzip2",
}


class AutoSave(autosave_base.AutoSaveBase):
    """
    The writing within the rollover rate is atomic. Writes are done to a temp file, then atomically moved to the old snapshot.
    """

    @cascore.dproperty_ctree(default=600)
    def save_rate_s(self, val):
        """
        Rate to autosave the snapshot. within the rollover rate_these will all have the same name and will be overwritten until rollover.
        This prevents excessive saving while providing recent saves. If variables are marked "urgentsave_s", then saving may be more frequent
        as those variables are edited.
        """
        return val

    @cascore.dproperty_ctree(default=8 * 3600)
    def rollover_rate_s(self, val):
        """
        Rate to rollover to a new snapshot filename
        """
        return val

    # @cascore.dproperty_ctree(default = 'bzip')
    # def zip_rollover_program(self, val):
    #    """
    #    Use this program to zip files as they rollover to take less space. If null, then the files will not be zipped. Good values are ['gzip', 'bzip']
    #    """
    #    return val

    @cascore.dproperty_ctree(default=lambda self: path.abspath("./burt/"))
    def save_folder(self, val):
        """
        Folder to store burt save files within.
        """
        return val

    @cascore.dproperty_ctree(default=lambda self: self.save_folder)
    def load_folder(self, val):
        """
        folder to put the load-file symlinks. Defaults in unspecified to using save_folder.
        """
        if val is None:
            val = self.save_folder
        return val

    @cascore.dproperty_ctree(
        default="{modname}_burt_{year}{month}{day}_{hour}{minute}{second}.snap"
    )
    def save_fname_template(self, val):
        """
        Template to generate save file names. It can use formatting keys:
        {modname}, {year}, {month}, {day}, {hour}, {minute}, {second}
        If null, then rolling save will NOT be active.
        """
        return val

    @cascore.dproperty
    def modname(self):
        return self.root.module_name

    @cascore.dproperty_ctree(default="{modname}_last.snap")
    def load_fname(self, val):
        """
        File name that the latest snapshot is symlinked to. May use {modname} template. It is also the snapshot loaded at startup. if null, then symlink save is not supported and load will not be automatic.
        """
        return val

    @cascore.dproperty
    def load_fpath(self):
        """
        load_fname with templates resolved
        """
        if self.load_folder is None or self.load_fname is None:
            return None
        return path.join(self.load_folder, self.load_fname.format(modname=self.modname))

    def folders_make_ready(self):
        if self.save_folder is not None and self.save_fname_template is not None:
            try:
                os.makedirs(self.save_folder)
            except OSError as E:
                if E.errno != errno.EEXIST:
                    raise

        if self.load_folder is not None and self.load_fpath is not None:
            try:
                os.mkdir(self.load_folder)
            except OSError as E:
                if E.errno != errno.EEXIST:
                    raise
        return

    def load_snap(self):
        """
        Loads the configured snapshot into the CAS Driver database
        """
        load_fpath = path.join(self.load_folder, self.load_fpath)
        self.load_snap_file(load_fpath)

    def load_snap_file(self, fname):
        """
        May need to unzip first.
        """
        # store the program to unzip in zipper_prog
        for suffix, zipper_prog in suffix_programs.items():
            if fname.endswith(suffix):
                break
        else:
            zipper_prog = None

        # TODO
        if zipper_prog is not None:
            raise NotImplementedError("Can't unzip yet")

        try:
            with open(fname, "r") as F:
                self.load_snap_file_raw(F)
        except IOError as E:
            if E.errno == errno.ENOENT:
                print("WARNING: No snapshot to load")
            else:
                raise

    _future_savesnap = None

    def urgentsave_notify(self, pvname, window_s):
        """
        Urgent channel was modified. This is notified through the CAS Driver.
        """
        if self._future_savesnap is None or window_s < self._future_savesnap:
            self._future_savesnap = window_s
            # push the rolling time ahead a bit in the queue to meet the urgency requirement
            self.reactor.enqueue(self.save_snap_rolling, future_s=window_s)
        return

    @declarative.callbackmethod
    def save_notify(self, time_now, time_epoch):
        return

    _last_linkpath = None

    def save_snap_rolling(self):
        self._future_savesnap = None
        ptime_now = time.time()
        ptime_epoch = ptime_now - (ptime_now % self.rollover_rate_s)
        dt_epoch = datetime.datetime.fromtimestamp(ptime_epoch)

        if self.save_fname_template is None:
            return

        fill = str("0")
        fname = self.save_fname_template.format(
            year=str(dt_epoch.year).rjust(4, fill),
            month=str(dt_epoch.month).rjust(2, fill),
            day=str(dt_epoch.day).rjust(2, fill),
            hour=str(dt_epoch.hour).rjust(2, fill),
            minute=str(dt_epoch.minute).rjust(2, fill),
            second=str(dt_epoch.second).rjust(2, fill),
            ptime=ptime_epoch,
            modname=self.modname,
        )
        fpath_save = path.abspath(path.join(self.save_folder, fname))

        prev_file_exists = path.exists(fpath_save)

        if prev_file_exists:
            fbase, fext = path.splitext(fpath_save)
            fpath_temp = fbase + "_temp" + fext
        else:
            fpath_temp = fpath_save

        with open(fpath_temp, "w") as F:
            self.save_snap_file_raw(F)

        # atomic rename, so the existing snap file is always correct
        if fpath_temp != fpath_save:
            os.rename(fpath_temp, fpath_save)

        fpath_previous = self._last_linkpath
        fpath_do_link = True
        if fpath_previous is None:
            # now update the symlink
            if path.exists(self.load_fpath):
                if path.islink(self.load_fpath):
                    fpath_previous = path.abspath(os.readlink(self.load_fpath))
                else:
                    print("WARNING: load path is not symlink, wont update load file")
                    fpath_do_link = False

        if fpath_do_link:
            if fpath_previous != fpath_save:
                try:
                    os.unlink(self.load_fpath)
                except OSError as E:
                    if E.errno == errno.ENOENT:
                        pass
                    else:
                        raise
                # then update!
                os.symlink(fpath_save, self.load_fpath)
                self._last_linkpath = fpath_save
                # TODO, optionally zip the previous path

        self.save_notify(ptime_now, ptime_epoch)
        return

    @cascore.dproperty
    def setup_snap_rolling(self):
        if self.save_rate_s is not None:
            self.reactor.enqueue_looping(
                self.save_snap_rolling,
                period_s=self.save_rate_s,
            )
