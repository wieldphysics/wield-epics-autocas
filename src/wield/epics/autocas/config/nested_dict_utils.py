#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
from wield.bunch.deep_bunch import DeepBunch
import collections


def remap_recursive(d, remap=None):
    if remap is not None:
        d = remap(d)
    if isinstance(d, collections.Mapping):
        d2 = dict()
        for k, v in d.items():
            d2[remap_recursive(k, remap)] = remap_recursive(v, remap)
        return d2
    elif isinstance(d, (list, tuple)):
        d2 = []
        for v in d:
            d2.append(remap_recursive(v, remap))
        return d2
    elif isinstance(d, (int, float)):
        return d
    elif isinstance(d, str):
        return str(d)
    elif d is None:
        return d
    else:
        raise TypeError("Unknown Config Export type: {0}".format(repr(d)))


def dict_diff(d1, d2):
    d_unused = DeepBunch()
    d1_diff = DeepBunch()
    d2_diff = DeepBunch()
    _dict_diff(d1, d2, d_unused, d1_diff, d2_diff, None)
    d1_diff = d1_diff.mydict.get(None, None)
    d2_diff = d2_diff.mydict.get(None, None)
    return d_unused.mydict, d1_diff, d2_diff


def _dict_diff(d1, d2, d_unused, d1_diff, d2_diff, k_prev):
    """
    determines d1 - d2 in the set-subtraction sense. Separates d_unused and d1_diff and d2_diff
    """
    if isinstance(d1, collections.Mapping):
        if not isinstance(d2, collections.Mapping):
            d1_diff[k_prev] = d1
            d2_diff[k_prev] = d2

        for k, v in d1.items():
            if k not in d2:
                d_unused[k] = v
            else:
                _dict_diff(
                    d1[k],
                    d2[k],
                    d_unused[k],
                    d1_diff[k_prev],
                    d2_diff[k_prev],
                    k_prev=k,
                )
    else:
        if d1 != d2:
            d1_diff[k_prev] = d1
            d2_diff[k_prev] = d2


def dict_kinclude(d1, d2, d_keep):
    """
    Keep only keys of d1 that are in d2
    """
    if isinstance(d1, collections.Mapping):
        if not isinstance(d2, collections.Mapping):
            return True

        for k, v in d1.items():
            if k not in d2:
                return False
            else:
                if dict_kinclude(d1[k], d2[k], d_keep[k]):
                    d_keep[k] = d1[k]
        return False
    else:
        return False


def dict_about_merge(d1, d2):
    """
    Merges d2 into d1, adds "about" keys which are missing from d2. Intended to merge the CAS9CmdLine._ctree_about with the root.ctree.about dictionary
    """
    if not isinstance(d2, collections.Mapping):
        d1["about"] = d2
    else:
        for k, v in d2.items():
            dict_about_merge(d1[k], v)
