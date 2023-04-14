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
import socket
import errno
import queue

from YALL.utilities.async import async_method

from declarative import (
    declarative.OverridableObject,
    declarative.dproperty, declarative.NOARG,
    declarative.RelayBool,
)
from YALL.controls.core.coroutine.main_reactor import reactor

import logging; module_logger = logging.getLogger(__name__)

class PicomotorBridgeReactor(declarative.OverridableObject):
    _params_socket = None
    _connection_queue = None
    _async_thread = None

    connection_timeout_s = 1.

    @declarative.dproperty
    def socket_address(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return val

    @declarative.dproperty
    def ebridge(self, ebridge = declarative.NOARG):
        if ebridge is declarative.NOARG:
            raise RuntimeError("Must Specify")
        #TODO master mode is stupid
        ebridge.master_mode = True
        return ebridge

    @declarative.dproperty
    def state_fake(self, rbool = declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBool(False)
        return rbool

    def __init__(self, **kwargs):
        self._params_socket = None
        self._lock = threading.Lock()
        self._quit_event = threading.Event()
        self._quit_epoch = 0
        self._ASYNC_quit_epoch = 0
        super(PicomotorBridgeReactor, self).__init__(**kwargs)
        return

    @declarative.dproperty
    def state_active(self, rbool = declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBool(False)
        rbool.register(
            key = self,
            callback = self._state_active_do,
            assumed_value = False,
        )
        return rbool

    @declarative.dproperty
    def state_connected(self, rbool = declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBool(False)
        #duck test
        rbool.assign
        return rbool

    def _state_active_do(self, bstate):
        if bstate:
            with self._lock:
                self.ebridge.connect()
                #this is run in a separate thread
                self._quit_event.clear()
                self._quit_epoch += 1
                prev_thread = self._async_thread
                self._async_thread = self._ASYNC_blocking_connection_loop(
                    prev_thread,
                    self._quit_epoch,
                    bool(self.state_fake),
                )
        else:
            with self._lock:
                self._ASYNC_quit_epoch = self._quit_epoch
                self._quit_event.set()
                sck = self._params_socket
                if sck is not None:
                    #should cancel the wait if we are timing out on a connection
                    sck.shutdown(socket.SHUT_RDWR)
                    sck.close()
                #and the send reactor queue
                queue = self._connection_queue
                if queue is not None:
                    queue.put(None)
                self.ebridge.disconnect()
                #now wait for finish
        return

    @async_method(thread_name = '{self} -> {name}', daemon = True)
    def _ASYNC_blocking_connection_loop(self, prev_thread, my_quit_epoch, fake_connection):
        """
        """
        if prev_thread is not None:
            prev_thread.join()

        def set_connection_str(s):
            def task():
                self.ebridge.connection_str = s[:40]
            reactor.send_task(task)
            return

        while(True):
            with self._lock:
                if self._ASYNC_quit_epoch >= my_quit_epoch:
                    break
            if not fake_connection:
                set_connection_str("connecting")
                try:
                    address = socket.gethostbyname(self.socket_address)
                except socket.gaierror as E:
                    set_connection_str(E.args[1])
                    return
                with self._lock:
                    if self._ASYNC_quit_epoch >= my_quit_epoch:
                        break
                    self._params_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                if not fake_connection:
                    try:
                        #use telnet port on the devices
                        self._params_socket.connect((address, 23))
                    except socket.error as E:
                        set_connection_str(str(E))
                        if E.errno in (
                            errno.ECONNREFUSED,
                            errno.ENOENT,
                            errno.EHOSTUNREACH,
                            errno.ETIMEDOUT,
                            errno.ECONNRESET,
                        ):
                            self._quit_event.wait(self.connection_timeout_s)
                            continue
                        elif E.errno in (errno.EBADF,):
                            break
                        else:
                            print("reactor unknown error", E)
                            self._quit_event.wait(self.connection_timeout_s)
                        continue
                    except socket.timeout:
                        continue
                    except Exception as E:
                        set_connection_str(str(E))
                        print("reactor unknown error", E)
                        self._quit_event.wait(self.connection_timeout_s)
                        continue

                self._connection_queue = queue.Queue()

                reactor.send_task(self._connected)
                try:
                    if not fake_connection:
                        #first command throws error, so flush
                        module_logger.info('Picomotor comm start\n')
                        self._params_socket.send('\n')
                        recv_msg = self._params_socket.recv(1024)
                    while True:
                        msg_list = self._connection_queue.get(block = True)
                        if msg_list is None:
                            break
                        else:
                            for msg in msg_list:
                                if not fake_connection:
                                    module_logger.info('Picomotor send: ' + msg)
                                    self._params_socket.send(msg)
                                    recv_msg = self._params_socket.recv(1024)
                                else:
                                    recv_msg = msg
                                #gotta limit to 40 chars because of PV limits
                                set_connection_str(recv_msg.strip())
                except IOError as E:
                    pass
                except Exception as E:
                    print("unknown socket error: ", E)
                    raise
                finally:
                    self._connection_queue = None
                    reactor.send_task(self._disconnected)
            finally:
                with self._lock:
                    if not fake_connection:
                        self._params_socket.close()
            set_connection_str("IDLE")
        return

    def insert_msg_list(self, msg_list):
        """
        returns true if msg list will be sent down
        """
        queue = self._connection_queue
        if queue is not None:
            queue.put(list(msg_list))
            return True
        else:
            return False

    def _connected(self):
        self.ebridge.connection_str = "connection made"
        self.ebridge.connection_status_set(True)
        self.state_connected.assign(True)

    def _disconnected(self):
        self.ebridge.connection_status_set(False)
        self.state_connected.assign(False)


class PicomotorRelay(declarative.OverridableObject):

    @declarative.dproperty
    def reactor(self, rct = declarative.NOARG):
        if rct is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return rct

    @declarative.dproperty
    def ebridge(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            raise RuntimeError("Must Specify")
        #TODO master_mode is dumb
        val.master_mode = True
        return val

    @declarative.dproperty
    def device_num_x(self, num = declarative.NOARG):
        if num is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return num

    @declarative.dproperty
    def motor_num_x(self, num = declarative.NOARG):
        if num is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return num

    @declarative.dproperty
    def device_num_y(self, num = declarative.NOARG):
        if num is declarative.NOARG:
            return None
        return num

    @declarative.dproperty
    def motor_num_y(self, num = declarative.NOARG):
        if num is declarative.NOARG:
            return None
        return num

    @declarative.dproperty
    def velocity(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            val = 500
        return val

    @declarative.dproperty
    def state_connected(self):
        rbool = self.reactor.state_connected
        rbool.register(
            key = self,
            callback = self._state_connected_do,
            assumed_value = False,
        )
        return rbool

    def _state_connected_do(self, bstate):
        if bstate:
            self.ebridge.connect()
            self.ebridge.x_control_react.register(self, self.x_control_move)
            self.ebridge.x_control = 0.
            msg_list = [
                ('vel {0} {1}={2}\n'
                 ).format(self.device_num_x, self.motor_num_x, self.velocity)
            ]
            if self.ebridge.NUM_CHANNELS > 1:
                self.ebridge.y_control_react.register(self, self.y_control_move)
                self.ebridge.y_control = 0.
                msg_list += [
                    ('vel {0} {1}={2}\n'
                     ).format(self.device_num_y, self.motor_num_y, self.velocity)
                ]
            #this sets the initial timing in the controller device
            self.reactor.insert_msg_list(msg_list)
        else:
            self.ebridge.x_control_react.register(self, self.x_control_move, remove = True)
            self.ebridge.x_control = 0.
            if self.ebridge.NUM_CHANNELS > 1:
                self.ebridge.y_control_react.register(self, self.y_control_move, remove = True)
                self.ebridge.y_control = 0.
            self.ebridge.disconnect()

    def x_control_move(self, value):
        #put limits on motion
        value = max(value, -1000)
        value = min(value, 1000)
        msg_list = [
            'CHL A{0}={1}\n'.format(self.device_num_x, self.motor_num_x),
            'REL A{0} {1} G\n'.format(self.device_num_x, int(value))
        ]
        did_commit = self.reactor.insert_msg_list(msg_list)
        if did_commit:
            self.ebridge.x_control = 0.
            self.ebridge.x_offset += value
        return

    def y_control_move(self, value):
        #put limits on motion
        value = max(value, -1000)
        value = min(value, 1000)
        msg_list = [
            'CHL A{0}={1}\n'.format(self.device_num_y, self.motor_num_y),
            'REL A{0} {1} G\n'.format(self.device_num_y, int(value))
        ]
        did_commit = self.reactor.insert_msg_list(msg_list)
        if did_commit:
            self.ebridge.y_control = 0.
            self.ebridge.y_offset += value
        return


