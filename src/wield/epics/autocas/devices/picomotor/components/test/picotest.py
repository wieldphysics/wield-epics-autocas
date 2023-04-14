#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import socket
import time

TCP_IP = "131.225.114.77"
TCP_PORT = 23
BUFFER_SIZE = 1024
MOVE_FORWARD_MESSAGE = "FOR A2 G"
MOVE_REVERSE_MESSAGE = "REV A2 G"
STOP_MESSAGE = "STO"
# SET_FAST_MESSAGE = 'VEL A1 0=2000'
# SET_SLOW_MESSAGE = 'VEL A1 0=250'
## does the same job:
SET_FAST_MESSAGE = "RES COARSE"
SET_SLOW_MESSAGE = "RES FINE"


def send(message):
    print(message)
    s.send(message + "\n")
    time.sleep(0.005)


def receive():
    data = s.recv(BUFFER_SIZE)
    time.sleep(0.005)
    return data


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
time.sleep(0.1)

for i in range(3):
    send("CHL A1=0")
    print(receive())
    time.sleep(1)
    send("REL A1 1000 G")
    print(receive())
    time.sleep(1)
    send("REL A1 -1000 G")
    print(receive())
    time.sleep(1)
    send("CHL A1=1")
    print(receive())
    time.sleep(1)
    send("REL A1 1000 G")
    print(receive())
    time.sleep(1)
    send("REL A1 -1000 G")
    print(receive())
    time.sleep(1)
    send("CHL A1=2")
    print(receive())
    time.sleep(1)
    send("REL A1 1000 G")
    print(receive())
    time.sleep(1)
    send("REL A1 -1000 G")
    print(receive())
    time.sleep(1)

s.close()
