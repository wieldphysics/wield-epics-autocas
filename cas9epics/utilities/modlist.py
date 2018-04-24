# -*- coding: utf-8 -*-
"""
"""
from __future__ import division, print_function, unicode_literals
import numpy as np


import os
import sys
from os import path
from cas9epics import utilities

def modlist(include_pyc = True):
    pyname = 'python{v.major}.{v.minor}'.format(v = sys.version_info)
    mods = []
    for modname, mod in sys.modules.items():
        if mod is not None:
            try:
                fname = mod.__file__
            except AttributeError:
                pass
            else:
                pbase, pext = path.splitext(fname)
                if pext in ['.py', '.pyc']:
                    fnamepy = pbase + '.py'
                    fnamepyc = pbase + '.py'

                    if fname.find(pyname) == -1 and fname.find('site-packages') == -1:
                        if include_pyc:
                            mods.append(fnamepyc)
                        mods.append(fnamepy)
    return mods
