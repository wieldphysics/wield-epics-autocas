"""
"""
from __future__ import division, print_function, unicode_literals

import sys
import os
#TODO import this later or make it failsafe
import inotify_simple

from .. import cas9core
from ..utilities.modlist import modlist


class RestartOnEdit(cas9core.CASUser):
    _myinotify = None

    poll_rate_s = 1

    @cas9core.dproperty
    def policy(self, val = 'EXIT'):
        assert(val in ['EXIT', 'REPLACE'])
        return val

    @cas9core.dproperty
    def setup_action(self):
        self.reactor.enqueue(self._startup_task, future_s = 3)

    def _startup_task(self):
        modfiles = modlist()
        inotify = inotify_simple.INotify()
        for fpath in modfiles:
            inotify.add_watch(fpath, inotify_simple.flags.MODIFY)
        self._myinotify = inotify

        self.reactor.enqueue_looping(self._loop_check_task, period_s = self.poll_rate_s)

    def _loop_check_task(self):
        events = self._myinotify.read(timeout = 0)
        #only modify is registered
        if events:
            print("RestartOnEdit noticed a modified file on inotify!")
            if self.policy == 'REPLACE':
                print("RESTARTING and REPLACING process")
                os.execv(sys.executable, ['python{v.major}.{v.minor}'.format(v = sys.version_info)] + sys.argv)
            elif self.policy == 'EXIT':
                print("Exiting Process")
                sys.exit(0)

