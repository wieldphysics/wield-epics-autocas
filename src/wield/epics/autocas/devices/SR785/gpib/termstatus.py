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
import pdb


class statusTxt:
    def __init__(self, initTxt):
        self.txtlen = len(initTxt)
        self.txt = initTxt
        print initTxt,
        sys.stdout.flush()

    def update(self, updateTxt):
        print "\010" + "\010" * self.txtlen + updateTxt,
        sys.stdout.flush()
        self.txtlen = len(updateTxt)
        self.txt = updateTxt

    def end(self, updateTxt=""):
        if updateTxt == "":
            print ""
        else:
            print "\010" + "\010" * self.txtlen + updateTxt

        sys.stdout.flush()
