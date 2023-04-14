#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""

import threading
import time
import functools
from wield.bunch import Bunch

try:
    import queue as queue
except ImportError:
    import Queue as queue
import sys
import collections

from declarative.callbacks import callbackmethod
from ..utilities.priority_queue import HeapPriorityQueue


from . import interrupt_delay

TThread = threading.Thread

keyboard_interrupt_delay = interrupt_delay.DelayedKeyboardInterrupt()

_EXIT = "Finish The Reactor"


class Reactor(object):
    sleep = time.sleep
    time = time.time
    Event = threading.Event
    Queue = queue.Queue
    max_wait_s = 1 / 4.0

    _task_queue = None

    def __init__(self, task_lock=None):
        self._current_reactor_thread = None
        self._canary_thread = None
        self._task_num = 0
        self._task_send_num = 0
        self._canary_time = 5.0
        self._canary_poll = 2.0
        self._queue_lock = threading.Lock()
        if task_lock is None:
            self.task_lock = threading.Lock()
        else:
            self.task_lock = task_lock
        self.rate_latency_check = 1000

        # rendezvous point for the queue to be generated
        self._task_queue = queue.Queue()
        self._pqueue = HeapPriorityQueue()

        # this is a map from task keys to bunches storing run metadata for eager-rate-limiting queuing
        self._task_map = dict()
        # this is a map from task keys to bunches storing run metadata for non-eager-rate-limiting queuing
        # items in task_map get moved to _task_history when they are done to remember the last time a task-key is run
        self._task_history = dict()

        self._canary_thread = TThread(
            target=self._native_thread_canary,
            name="reactor canary",
        )
        self._canary_thread.daemon = True
        self._canary_thread.start()

        # the task lock is only free while the queue is acting and waiting
        self.task_lock.acquire()
        return  # ~__init__

    def run_reactor(self):
        self._reactor_loop()

    def _native_thread_canary(self):
        last_task_num = None
        last_task_time = 0
        while True:
            tnum = self._task_num
            if tnum is not None:
                time_now = time.time()
                if tnum != last_task_num:
                    if last_task_time == sys.float_info.max:
                        self.canary_revived()
                    last_task_num = tnum
                    last_task_time = time_now
                elif time_now - last_task_time > self._canary_time:
                    self.canary_died()
                    last_task_time = sys.float_info.max
            time.sleep(self._canary_poll)
        return

    @callbackmethod
    def canary_died(self):
        # TODO, log better
        print("Reactor canary died!")
        return

    @callbackmethod
    def canary_revived(self):
        # TODO, log better
        print("Reactor canary revived!")
        return

    def flush(
        self,
        for_s=None,
        modulo_s=None,
        mtime_to=None,
    ):
        if for_s is not None:
            if mtime_to is None:
                mtime_to = time.time()
            mtime_to += for_s

        if modulo_s is not None:
            if mtime_to is None:
                mtime_to = time.time()
            mtime_to = mtime_to + modulo_s - mtime_to % modulo_s
        # if mtime_to is None at this point, then it means to flush and quit immediately

        self._queue_lock.acquire()
        self.task_lock.release()
        self._current_reactor_thread = threading.current_thread()
        try:
            task_num = self._task_num
            while True:
                task_num += 1
                self._task_num = task_num
                mtime = time.time()
                if self._pqueue:
                    ntime, nitem = self._pqueue.peek()
                    if ntime < mtime:
                        item = nitem
                        self._pqueue.pop()
                    else:
                        try:
                            item = self._task_queue.get(False)
                        except queue.Empty:
                            if mtime_to is None or mtime >= mtime_to:
                                break
                            try:
                                self._queue_lock.release()
                                item = self._task_queue.get(
                                    True,
                                    min(
                                        mtime_to - mtime, ntime - mtime, self.max_wait_s
                                    ),
                                )
                            except queue.Empty:
                                continue
                            finally:
                                self._queue_lock.acquire()
                else:
                    try:
                        item = self._task_queue.get(False)
                    except queue.Empty:
                        if mtime_to is None or mtime >= mtime_to:
                            break
                        try:
                            self._queue_lock.release()
                            item = self._task_queue.get(
                                True, min(mtime_to - mtime, self.max_wait_s)
                            )
                        except queue.Empty:
                            continue
                        finally:
                            self._queue_lock.acquire()
                if item is _EXIT:
                    break
                else:
                    # print("FLUSH: ", item)
                    with self.task_lock, keyboard_interrupt_delay:
                        item()
        finally:
            self._current_reactor_thread = None
            self.task_lock.acquire()
            self._queue_lock.release()
        return

    def time(self):
        return time.time()

    def _reactor_loop(self):
        self._queue_lock.acquire()
        self.task_lock.release()
        try:
            self._current_reactor_thread = threading.current_thread()
            task_num = self._task_num
            while True:
                task_num += 1
                self._task_num = task_num
                mtime = time.time()
                if self._pqueue:
                    ntime, nitem = self._pqueue.peek()
                    if ntime <= mtime:
                        item = nitem
                        self._pqueue.pop()
                    else:
                        try:
                            item = self._task_queue.get(False)
                        except queue.Empty:
                            try:
                                self._queue_lock.release()
                                item = self._task_queue.get(
                                    True, min(ntime - mtime, self.max_wait_s)
                                )
                            except queue.Empty:
                                continue
                            finally:
                                self._queue_lock.acquire()
                else:
                    try:
                        item = self._task_queue.get(False)
                    except queue.Empty:
                        try:
                            self._queue_lock.release()
                            item = self._task_queue.get(True, self.max_wait_s)
                        except queue.Empty:
                            continue
                        finally:
                            self._queue_lock.acquire()
                if item is _EXIT:
                    break
                else:
                    with self.task_lock, keyboard_interrupt_delay:
                        item()
            try:
                # slurp up remaining tasks
                while True:
                    task_num += 1
                    self._task_num = task_num

                    item = self._task_queue.get_nowait()
                    with self.task_lock, keyboard_interrupt_delay:
                        item()
            except queue.Empty:
                pass
        finally:
            self._current_reactor_thread = None
            self.task_lock.acquire()
            self._queue_lock.release()
        return

    def loop_kill(self):
        self._task_queue.put(_EXIT)

    def reactor_shutdown(self):
        return self.loop_kill()

    def _check_latency(self, send_time):
        now_time = time.time()
        self.latency_cb(now_time - send_time, self._task_queue.qsize())

    def send_task(self, item, run_at=None):
        if not isinstance(item, collections.Callable):
            raise RuntimeError("Reactor Item must be a nullary Callable")
        self._task_send_num += 1
        if (self._task_send_num % self.rate_latency_check) == 0:
            my_time = time.time()
            self.send_task(lambda: self._check_latency(my_time))
        _queue = self._task_queue
        if _queue is None:
            print(("Send occured after queue death! {0}".format(item)))
            return
        if run_at is None:
            _queue.put(item)
        else:
            self._pqueue.push(QueueItem(run_at, item))
            # put a do nother item in the main queue to force a wakeup if nothing is currently in it
            # TODO see if this can be avoided if an item is already in the queue (race condition?)
            _queue.put(lambda: None)
        return

    def cb_send_task(self, cb):
        def deferred(*args, **kwargs):
            self.send_task(lambda: cb(*args, **kwargs))

        return deferred

    def enqueue(
        self,
        command,
        key=None,
        future_s=None,
        limit_s=None,
        mtime_at=None,
        modulo_s=None,
        force_requeue=False,
    ):
        return self._enqueue(
            command,
            key=key,
            future_s=future_s,
            limit_s=limit_s,
            mtime_at=mtime_at,
            modulo_s=modulo_s,
            force_requeue=force_requeue,
        )

    def enqueue_looping(
        self,
        command,
        key=None,
        period_s=None,
        skip_fraction=0.4,
        skip_cb=None,
    ):
        """
        a period_s of None (default) stops any looping!
        skip_cb is called if the loop is ever skipped
        """
        loop_settings = Bunch()
        loop_settings.period_s = period_s
        loop_settings.skip_fraction = skip_fraction
        loop_settings.skip_cb = skip_cb
        if period_s is not None:
            return self._enqueue(
                command,
                key=key,
                modulo_s=period_s,
                loop_settings=loop_settings,
                force_requeue=True,
            )
        else:
            # not specifying modulo_s, future_s, or mtime_at will unqueue any current task (no need to specify force_requeue although it doesn't hurt)
            return self._enqueue(
                command,
                key=key,
                modulo_s=None,
                loop_settings=loop_settings,
                force_requeue=True,
            )

    def _enqueue(
        self,
        command,
        key=None,
        future_s=None,
        limit_s=None,
        mtime_at=None,
        modulo_s=None,
        force_requeue=False,
        loop_settings=None,
    ):
        """
        Specialty method for rate-limited queuing. The task is keyed and so this can be called multiple times and it won't requeue. If it is already queued, the timing can be
        moved more immediate if the mtime_at is EARLIER than the previously queued version. future_s adds to either the current time or mtime_at.

        limit_s checks the last time this was run and pushes the queue time up to honor the rate limit.

        modulo_s rounds the queue time up to nearest fraction of a second modulo this time.

        if mtime_at, future_s and modulo_s are all None, then the task is unqueued. force_requeue does not need to be specified for this to happen
        if loop_settings is set, then the command will be re-queued
        """
        if key is None:
            key = command

        mtime = mtime_at
        if future_s is not None:
            if mtime is None:
                mtime = time.time()
            mtime += future_s

        if modulo_s is not None:
            if mtime is None:
                mtime = time.time()
            mtime = mtime + modulo_s - mtime % modulo_s
        # if mtime is None at this point, then it means to not enqueue or to cancel queuing if force_requeue is set

        qdat_prev = self._task_history.get(key, None)
        qdat_current = self._task_map.get(key, None)

        if mtime is not None and qdat_prev is not None:
            if limit_s is not None and (mtime - qdat_prev.mtime < limit_s):
                mtime = qdat_prev.mtime + limit_s

        # create a closure for the task which is aware of the qdata bunch.
        # that bunch allows this task wrapper to be cancellable and loopable
        # if the qdata has_run is changed to False, then the task will be cancelled
        def inner_task():
            if not qdata.has_run:
                qdata.has_run = True
                # move to history
                self._task_history[key] = qdata
                qdat_current = self._task_map.pop(key)
                if qdat_current is not qdata:
                    # put it back if it isn't the recently finished one!
                    self._task_map[key] = qdat_current
                    assert False

                loop_settings = qdata.loop_settings

                if loop_settings is not None:
                    if loop_settings.period_s is not None:
                        mtime_current = time.time()
                        mtime_last = qdata.mtime
                        mtime_next = (
                            mtime_last
                            + loop_settings.period_s
                            - mtime_last % loop_settings.period_s
                        )

                        fraction = (mtime_next - mtime_current) / loop_settings.period_s
                        if fraction < loop_settings.skip_fraction:
                            mtime_next += loop_settings.period_s
                            skip_cb = loop_settings.skip_cb
                            if skip_cb is not None:
                                skip_cb()
                        self._enqueue(
                            qdata.command,
                            qdata.key,
                            mtime_at=mtime_next,
                            loop_settings=loop_settings,
                        )

                # run the task last, after updating the task run setup
                qdata.command()

        if qdat_current is not None:
            # task currently exists and we need to update the time
            assert not qdat_current.has_run
            if mtime is None:
                # remove the task
                # first tell the task not to run itself
                qdat_current.has_run = True
                # set it to None so the later block can return the correct value
                qdat_current = None
                self._task_map.pop(key)
            elif mtime < qdat_current.mtime:
                # push up the run time and reinject the task
                qdat_current.mtime = mtime
                # have to specify qdata because the closure of inner_task needs it
                qdata = qdat_current
                self.send_task(inner_task, run_at=mtime)
            elif force_requeue or loop_settings is not None:
                qdat_current.has_run = True
                # go ahead and remove it from the map for safety
                self._task_map.pop(key)
                # set it to None so the later block reqeueues it
                qdat_current = None
                # carry over if the task was looping and it is not forcing new loop settings
                if loop_settings is None:
                    loop_settings = qdat_current.loop_settings
                # this is more complex as we have to cancel the current task and recreate the qdata

        # handle task creation and injection
        # would be an "else of the previous if, but this allows it to handle force_requeue as well
        if qdat_current is None:
            if mtime is not None:
                qdata = Bunch()
                qdata.key = key
                qdata.command = command
                qdata.has_run = False
                qdata.mtime = mtime
                qdata.loop_settings = loop_settings

                self._task_map[key] = qdata
                self.send_task(inner_task, run_at=mtime)
            else:
                # if mtime is None here, then the task should NOT be queued or re-queued
                pass
            return True
        return False

    def capture(self):
        self._queue_lock.acquire()

    def release(self):
        self._queue_lock.release()

    def assert_living_in_reactor(self):
        if self._current_reactor_thread is None:
            return
        assert threading.current_thread() == self._current_reactor_thread

    def check_living_in_reactor(self):
        if self._current_reactor_thread is None:
            return True
        return threading.current_thread() == self._current_reactor_thread

    def send_task_partial(self, func, *args, **kwargs):
        p = functools.partial(func, *args, **kwargs)
        self.send_task(p)

    def send_task_synchronous(self, func, *args, **kwargs):
        if self.check_living_in_reactor():
            return func(*args, **kwargs)
        else:
            ev_did_run = threading.Event()
            retval = []

            def reactor_run():
                try:
                    ret = func(*args, **kwargs)
                    retval.append(ret)
                except Exception as E:
                    retval.append(None)
                    retval.append(E)
                finally:
                    ev_did_run.set()
                return

            self.send_task(reactor_run)
            while not ev_did_run.wait(timeout=0.05):
                pass
            if len(retval) == 2:
                raise retval[1]
            else:
                return retval[0]

    def reactor_only(self, func):
        """
        Decorator to ensure that method call is only made from the reactor
        """

        def alt_launch(*args, **kwargs):
            if self.check_living_in_reactor():
                return func(*args, **kwargs)
            else:
                ev_did_run = threading.Event()
                retval = []

                def reactor_run():
                    try:
                        ret = func(*args, **kwargs)
                        retval.append(ret)
                    except Exception as E:
                        retval.append(None)
                        retval.append(E)
                    finally:
                        ev_did_run.set()
                    return

                print("Shifting call: {0} to reactor thread and waiting result")
                self.send_task(reactor_run)
                ev_did_run.wait()
                if len(retval) == 2:
                    raise retval[1]
                else:
                    return retval[0]

        functools.update_wrapper(alt_launch, func)
        return alt_launch

    @callbackmethod
    def latency_cb(self, latency_s, latency_items):
        return


class QueueItem(collections.namedtuple("QueueTuple", ["run_at", "item"])):
    """
    Need a special container for the (mtime_run, item) pairs used in the scheduler.
    The heap queue sometimes sorts on the second item and function callbacks cannot be sorted.
    """

    def __lt__(self, other):
        return self[0] < other[0]

    def __gt__(self, other):
        return self[0] > other[0]

    def __eq__(self, other):
        return self[0] == other[0]

    def __le__(self, other):
        return self[0] <= other[0]

    def __ge__(self, other):
        return self[0] >= other[0]

    def __ne__(self, other):
        return self[0] != other[0]
