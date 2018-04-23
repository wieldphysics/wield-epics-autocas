"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import warnings
import serial
import declarative

from .. import relay_values
from .. import cas9core
from . serial_base import SerialConnection

#from . import utilities


class USBDeviceRS232(SerialConnection):

    @cas9core.dproperty
    def device_path(self, val = None):
        val = self.ctree.setdefault(
            'device_path', val,
            about = 'path to the serial block device, usually something in /dev/serial/by-id/'
        )
        if val.startswith('/dev/ttyUSB'):
            warnings.warn("Currently using a generic device name {0}, please use objects in /dev/serial/by-id/ for serial-number keyed usb devices".format(val))
        return val

    @cas9core.dproperty
    def poll_rate_s(self, val = 1):
        val = self.ctree.setdefault(
            'poll_rate_s', val,
            about = "Poll rate to attempt connections to the serial device in seconds"
        )
        val = float(val)
        assert(val > 0)
        return val

    @cas9core.dproperty
    def baud_rate(self, val = 9600):
        val = self.ctree.setdefault(
            'baud_rate', val,
            about = "Baud Rate for the connection"
        )
        return val

    @cas9core.dproperty
    def parity(self, val = 'None'):
        val = self.ctree.setdefault(
            'parity', val,
            about = "Parity of the connection, may be one of [N, O, E]",
        )
        assert(val in ["N", "O", "E"])
        return val

    @cas9core.dproperty_ctree(default = 1)
    def stop_bits(self, val):
        """
        Stop Bits for the connection, may be one of [1, 2]
        """
        val = int(val)
        assert(val in [1, 2])
        return val

    @cas9core.dproperty_ctree(default = 8)
    def byte_size(self, val):
        """
        byte size for the connection, may be one of [7, 8]
        """
        val = int(val)
        assert(val in [7, 8])
        return val

    @cas9core.dproperty
    def rb_communicating(self):
        rb = relay_values.RelayBool(False)
        self.cas_host(
            rb,
            name = 'COMM',
            writable = False,
        )
        return rb

    _serial_obj = None

    def _connect_task(self):
        assert(self._serial_obj is None)
        try:
            print("CHECKING: ", self.device_path)
            sdev = serial.Serial(
                self.device_path,
                baudrate = self.baud_rate,
                bytesize = self.byte_size,
                parity   = self.parity,
                stopbits = self.stop_bits,
                timeout = 1,
                xonxoff = 0,
                rtscts  = 0
            )
        except serial.SerialException as E:
            self.error(0, E.message)
        else:
            self._serial_obj = sdev
            self.error.clear()
            #stop this task
            self.reactor.enqueue_looping(self._connect_task, period_s = None)

            self.queue_clear()
            self.rb_connected.assign(True)

    @cas9core.dproperty
    def _startup(self):
        self.reactor.enqueue_looping(self._connect_task, period_s = self.poll_rate_s)

    def run(self):
        if self._serial_obj is not None:
            try:
                return super(USBDeviceRS232, self).run()
            except serial.SerialException as E:
                self.error(0, E.message)
                self._serial_obj = None
                self.rb_connected.assign(False)
                self.rb_communicating.assign(False)
                self.reactor.enqueue_looping(self._connect_task, period_s = self.poll_rate_s)
        else:
            #TODO, print warning or something? can't do anything if device isn't connected
            return

    def cmd_object(self):
        b = declarative.Bunch()
        b.writeline = self._device_writeline
        b.readline  = self._device_writeline
        b.flush     = self._device_flush
        b.reset_in  = self._device_reset_input
        b.reset_out = self._device_reset_output
        return b

    def _device_writeline(self, line):
        self._serial_obj.write(line + '\n')
        return

    def _device_readline(self):
        return self._serial_obj.readline()

    def _device_flush(self):
        self._serial_obj.flush()
        return

    def _device_reset_input(self):
        self._serial_obj.reset_input_buffer()
        return

    def _device_reset_output(self):
        self._serial_obj.reset_output_buffer()
        return






