#!/usr/bin/env python
"""
Script for EPICS communication with Newport 3040 Temperature controller
"""
from __future__ import print_function, division
import time
from wavestate import declarative
import numpy as np
from YALL.controls.filters.sos_cascades2 import sos_zp
from openLoop.utilities.np import logspaced


class GPIBControllerScript(declarative.OverridableObject):
    """
    """
    @declarative.dproperty
    def reactor(self):
        from YALL.controls.core.coroutine.main_reactor import PolyReactor, reactor
        if isinstance(reactor, PolyReactor):
            from YALL.controls.core.coroutine.main_reactor_sync import reactor
            print("BOOTUP STD")
            reactor.bootup_from_poly()
            #reactor.elevate_to_thread()
        return reactor

    @declarative.dproperty
    def state_connect(self):
        rb = declarative.RelayBool(True)
        return rb

    @declarative.dproperty
    def ebridge(self, ebr):
        self.reactor
        ebr.state_connect_local.assign(True)
        ebr.state_connect.bool_register(self.state_connect)
        ebr.rv_connect_mode.value = 'master'
        return ebr

    def main(self):
        ctime = time.time()
        self.reactor.flush(to_time = ctime + 1)

        F_Hz = logspaced(1, 100e3, 1000)
        #filt = sos_zp((-1000. + 1j, -1000. - 1j), (-10.+1j, -10.-1j), gain = 1.)
        filt = sos_zp((-1000., -1000.), (-10., -10.), gain = 1.)

        resp = filt.response(F_Hz)

        print(filt)
        print(filt.poles)
        print(filt.A_coefficients)
        print(filt.response(1.))
        print(filt.response(1000.))
        self.ebridge.rv_freq_Hz.value = F_Hz
        self.ebridge.rv_magnitude.value = abs(resp)
        self.ebridge.rv_magnitude_up.value = abs(resp) * 1.1
        self.ebridge.rv_magnitude_dn.value = abs(resp) * .9
        self.ebridge.rv_phase_deg.value = np.angle(resp, deg = True)
        self.ebridge.rv_SNR.value = np.ones_like(F_Hz)

        ctime = time.time()
        self.reactor.flush(to_time = ctime + 1/4)

        print(self.ebridge.rv_trig.value)
        self.ebridge.rv_trig.value += 1
        self.reactor.flush(to_time = ctime + 1/4)
        return


if __name__ == '__main__':
    from YALL.controls.peripherals.SR785.test.TST import EBridge
    ebr = EBridge(
        ifo = 'T1',
        local = True,
    )
    prg = GPIBControllerScript(
        ebridge = ebr.SR785,
    )
    prg.main()
