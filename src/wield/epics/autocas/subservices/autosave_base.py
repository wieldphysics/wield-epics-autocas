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
import datetime

from .. import cascore


class AutoSaveBase(cascore.CASUser):
    """
    The writing within the rollover rate is atomic. Writes are done to a temp file, then atomically moved to the old snapshot.
    """

    _my_pvdb = None
    _my_chnlist = None
    _my_casdriver = None

    @cascore.dproperty
    def username(self):
        import getpass

        return getpass.getuser()

    def set_db_driver(self, db, driver):
        """
        db set by the cas system driver, which this must integrate with.
        """
        self._my_pvdb = db
        self._my_casdriver = driver
        chnlist = []
        for pv, db_entry in db.items():
            do_burt = db_entry["burt"]
            if not do_burt:
                continue
            RO = db_entry["burtRO"]
            chnlist.append((pv, RO))
        chnlist.sort()
        self._my_chnlist = chnlist

    def load_snap_file_raw(self, fobj):
        # "--- Start BURT header"
        # "--- End BURT header"

        PV_vals = dict()
        ROPV_vals = dict()

        while True:
            line = fobj.readline()
            # check if it is the header bunch
            if line.startswith("---") and line.lower().find("start burt header") != 1:
                while True:
                    line = fobj.readline()
                    if not line:
                        # can only happen if it is the last line of the file, otherwise '\n' is left on
                        break

                    if (
                        line.startswith("---")
                        and line.lower().find("end burt header") != 1
                    ):
                        # load the next line before continuing so that the line can have PVinfo on it
                        line = fobj.readline()
                        break
                    # ignore any other data in the header
            if not line:
                # can only happen if it is the last line of the file, otherwise '\n' is left on
                break

            line = line.strip().split()
            if line[0] == "RO":
                isRO = True
                line = line[1:]
            else:
                isRO = False

            pv = line[0]
            count = line[1]

            if int(count) != 1:
                print(
                    "WARNING: can't handle PVs with count > 1 yet for PV: {0}".format(
                        pv
                    )
                )
                continue

            val = line[2]

            # check for null strings
            if val == r"\0":
                val = ""

            if isRO:
                ROPV_vals[pv] = val
            else:
                PV_vals[pv] = val

        for pv, pvRO in self._my_chnlist:
            if pvRO:
                val = ROPV_vals.get(pv, None)
                if val is None:
                    print(
                        "WARNING: RO PV missing on load: {0} (even though it is unused)".format(
                            pv
                        )
                    )
                continue

            val = PV_vals.get(pv, None)
            if val is None:
                val = ROPV_vals.get(pv, None)
                if val is None:
                    print("WARNING: PV missing on load: {0}".format(pv))
                else:
                    print(
                        "WARNING: non-RO PV listed as RO in snapshot on load (not loading)"
                    )
                continue

            # TODO, make the internal/remote save decision better
            remote = self._my_pvdb[pv].get("remote", False)
            if not remote:
                did_write = self._my_casdriver.write_sync_typecast(pv, val)
                if not did_write:
                    print(
                        'WARNING, write failed loading non-RO PV: "{0}" with value {1}'.format(
                            pv, val
                        )
                    )
        return

    def save_snap_file_raw(self, fobj):
        # TODO have it write time and other info
        dt = datetime.datetime.now()
        header = burt_header_template.format(
            uname=self.username,
            time=dt.strftime("%c"),
        )
        fobj.write(header)
        fobj.write("\n")
        for pv, pvRO in self._my_chnlist:
            # TODO, make the internal/remote save decision better
            remote = self._my_pvdb[pv].get("remote", False)
            if remote:
                continue
            val = self._my_casdriver.read(pv)

            if val == "":
                val = r"\0"

            # prevent it writing "True" and "False" for bools
            if isinstance(val, bool):
                val = int(val)

            if not pvRO:
                fobj.write("{0} 1 {1}\n".format(pv, val))
            else:
                fobj.write("RO {0} 1 {1}\n".format(pv, val))
        return

    def save_req_file_raw(self, fobj):
        for pv, pvRO in self._my_chnlist:
            if not pvRO:
                fobj.write("{0}\n".format(pv))
            else:
                fobj.write("RO {0}\n".format(pv))
        return

    def urgentsave_notify(self, pvname):
        """
        Urgent channel was modified. This is notified through the CAS Driver.
        """
        return


burt_header_template = """
--- Start BURT header
Time:     {time}
Login ID: {uname} ()
Eff  UID:
Group ID:
Keywords:
Comments:
Type:     Absolute
Directory
Req File:
--- End BURT header
""".strip()
