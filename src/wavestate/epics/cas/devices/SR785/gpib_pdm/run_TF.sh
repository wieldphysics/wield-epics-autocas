#!/usr/bin/env bash
python plotCohereTF.py -V -i gpib2.mit.edu -s 100000Hz -e 1Hz -n 200 -x .5 --showplot -t 20 -c 2 "$@"
