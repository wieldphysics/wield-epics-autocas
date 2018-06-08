#!/usr/bin/env bash
python plotFFT.py -V -i gpib2.mit.edu -b 100kHz -n 1000 -v 30 --avgmode=RMS --ic1=AC --showplot "$@"
