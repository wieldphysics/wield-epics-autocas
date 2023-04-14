#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import time
import sys
import logging
import readline
from optparse import OptionParser

from . import __version__
from .vxi11 import Instrument, Vxi11Exception

try:
    input = raw_input
except NameError:
    pass

LOCAL_COMMANDS = {
    "%SLEEP": (1, 1, lambda a: time.sleep(float(a[0]) / 1000)),
}


def process_local_command(cmd):
    args = cmd.split()
    if args[0] in LOCAL_COMMANDS:
        cmd_info = LOCAL_COMMANDS[args[0]]
        if cmd_info[0] <= len(args[1:]) <= cmd_info[1]:
            cmd_info[2](args[1:])
        else:
            print("Invalid number of arguments for command %s" % args[0])
    else:
        print('Unknown command "%s"' % cmd)


def main():
    usage = "usage: %prog [options] <host> [<name>]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-d", action="store_true", dest="debug", help="enable debug messages"
    )
    parser.add_option("-v", action="store_true", dest="verbose", help="be more verbose")
    parser.add_option("-V", action="store_true", dest="version", help="show version")
    parser.add_option(
        "--always-check-esr",
        action="store_true",
        dest="check_esr",
        help="Check the error status register after every command",
    )

    (options, args) = parser.parse_args()

    if options.version:
        print("vxi11-cli v%s" % (__version__,))
        sys.exit(0)

    logging.basicConfig()
    if options.verbose:
        logging.getLogger("vxi11").setLevel(logging.INFO)
    if options.debug:
        logging.getLogger("vxi11").setLevel(logging.DEBUG)

    if len(args) < 1:
        print(parser.format_help())
        sys.exit(1)

    host = args[0]
    name = None
    if len(args) > 1:
        name = args[1]

    v = Instrument(host, name)
    v.open()

    print("Enter command to send. Quit with 'q'. Read with '?'.")
    try:
        while True:
            cmd = input("=> ")
            if cmd == "q":
                break
            if cmd.startswith("%"):
                process_local_command(cmd)
                continue
            if len(cmd) > 0:
                is_query = cmd.split(" ")[0][-1] == "?"
                try:
                    if is_query:
                        if len(cmd) > 1:
                            v.write(cmd)
                        print(v.read())
                    else:
                        v.write(cmd)
                    if options.check_esr:
                        esr = int(v.ask("*ESR?").strip())
                        if esr != 0:
                            print("Warning: ESR was %d" % esr)
                except Vxi11Exception:
                    e = sys.exc_info()[1]
                    print("ERROR: %s" % e)
    except EOFError:
        print("exiting...")

    v.close()


if __name__ == "__main__":
    main()
