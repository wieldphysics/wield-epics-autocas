import serial
import re
import time

ser = serial.Serial('/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PXFA9IBH-if00-port0',  baudrate=9600, timeout=.5)
print(ser)

ser.write('++addr\n')
print('ADDR:',ser.readline())
ser.write('++ver\n')
print('VER:',ser.readline())
ser.write('++addr 0\n')
print('addr 0', ser.readline())
ser.write('++addr\n')
print('ADDR:',ser.readline())
ser.write('++mode\n')
print('MODE:',ser.readline())
ser.write('++mode 1\n')
print('MODE 1:',ser.readline())
ser.write('++mode\n')
print('MODE:',ser.readline())
ser.write('++eoi\n')
print('EOI:',ser.readline())
ser.write('++eos 0\n')
print('eos:',ser.readline())

ser.write('++auto 0\n')

ser.write('++addr 0\n')
ser.write('*IDN?\n')
print('IDN', ser.readline())
ser.write('++read eoi\n')
print('IDN2', ser.readline())

ser.write('++addr 2\n')
ser.write('*IDN?\n')
print('IDN', ser.readline())
ser.write('++read eoi\n')
print('IDN2', ser.readline())

ser.write('++addr 3\n')
ser.write('*IDN?\n')
print('IDN', ser.readline())
ser.write('++read eoi\n')
print('IDN2', ser.readline())
