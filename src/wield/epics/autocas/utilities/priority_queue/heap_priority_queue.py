#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
.. autoclass:: HeapPriorityQueue
"""
import heapq

try:
    import queue as queue
except ImportError:
    import Queue as queue
import threading


class HeapPriorityQueue(object):
    """
    Provide a priority Queue based on the :mod:`heapq` module. Should hold mostly to
    the :class:`queue.Queue` interface with the addition of a peek method.

    This implementation is **not** threadsafe

    .. automethod:: __init__

    .. automethod:: peek

    .. automethod:: is_empty

    .. automethod:: pop

    .. automethod:: push

    .. automethod:: replace

    .. automethod:: pushpop

    """

    def __init__(self, iterable=()):
        """
        :param iterable: iterable of initial items
        """
        heap = list(iterable)
        heapq.heapify(heap)
        self.heap = heap

    def peek(self):
        """
        View the first element without discarding

        :raises: :exc:`queue.Empty` if no items contained
        """
        try:
            return self.heap[0]
        except IndexError:
            raise queue.Empty()

    def is_empty(self):
        """
        Returns True when empty
        """
        return not self.heap

    def __nonzero__(self):
        return bool(self.heap)

    def __bool__(self):
        return bool(self.heap)

    def __len__(self):
        return len(self.heap)

    def pop(self):
        """
        return first item

        :raises: :exc:`queue.Empty` if no items contained
        """
        try:
            return heapq.heappop(self.heap)
        except IndexError:
            raise queue.Empty()

    def push(self, item):
        """
        Add an item to the priority queue
        """
        return heapq.heappush(self.heap, item)

    def replace(self, item):
        """
        get the smallest item and replace it with a new one

        :raises: :exc:`IndexError` when empty
        """
        return heapq.heapreplace(self.heap, item)

    def pushpop(self, item):
        """
        add item into the queue then return the smallest
        """
        return heapq.heappushpop(self.heap, item)


class HeapPriorityQueueThreadsafe(object):
    """
    Provide a priority queue based on the :mod:`heapq` module. Should hold mostly to
    the :class:`queue.Queue` interface with the addition of a peek method.

    This implementation **is** threadsafe

    .. automethod:: __init__

    .. automethod:: peek

    .. automethod:: is_empty

    .. automethod:: pop

    .. automethod:: push

    .. automethod:: replace

    .. automethod:: pushpop

    """

    def __init__(self, iterable=()):
        """
        :param iterable: iterable of initial items
        """
        self.lock = threading.Lock()
        heap = list(iterable)
        heapq.heapify(heap)
        self.heap = heap

    def peek(self):
        """
        View the first element without discarding

        :raises: :exc:`queue.Empty` if no items contained
        """
        try:
            return self.heap[0]
        except IndexError:
            raise queue.Empty()

    def is_empty(self):
        """
        Returns True when empty
        """
        return not self.heap

    def pop(self):
        """
        return first item

        :raises: :exc:`queue.Empty` if no items contained
        """
        with self.lock:
            try:
                return heapq.heappop(self.heap)
            except IndexError:
                raise queue.Empty()

    def push(self, item):
        """
        Add an item to the priority queue
        """
        with self.lock:
            return heapq.heappush(self.heap, item)

    def replace(self, item):
        """
        get the smallest item and replace it with a new one

        :raises: :exc:`IndexError` when empty
        """
        with self.lock:
            return heapq.heapreplace(self.heap, item)

    def pushpop(self, item):
        """
        add item into the queue then return the smallest
        """
        with self.lock:
            return heapq.pushpop(self.heap, item)
