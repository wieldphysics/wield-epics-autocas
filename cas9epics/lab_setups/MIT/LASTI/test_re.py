import re

float_re = r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?'

re_SOURCE = re.compile('^:SOURCE (.)$')
re_FREQVALUE = re.compile('^:CFRQ:VALUE ({0});INC {0}$'.format(float_re))
re_LEVELVALUE = re.compile('^:RFLV:UNITS DBM;TYPE (PD|EMF);VALUE ({0});INC {0};(ON|OFF)$'.format(float_re))

print(re_LEVELVALUE.match(':RFLV:UNITS DBM;TYPE PD;VALUE -100.0;INC 1.0;ON').group(2))
