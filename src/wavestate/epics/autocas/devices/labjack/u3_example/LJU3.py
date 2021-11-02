"""
"""


import cas9epics


from YALL.controls.peripherals.labjack.service import LJRelay
from YALL.controls.peripherals.labjack.u3relays import (
    LJU3ADCRelay,
    LJU3DACRelay,
    LJU3DOUTRelay,
    LJU3DINRelay,
)


class SHGLJU3Relay(LJRelay):
    @staticmethod
    def construct_device():
        import u3

        return u3.U3()

    @cas9epics.dproperty
    def DAC_io(self):
        return [
            LJU3DACRelay(
                ebridge=self.ebridge.DAC_map[0],
                parent=self,
                dacChannel=0,
            ),
            LJU3DACRelay(
                ebridge=self.ebridge.DAC_map[1],
                parent=self,
                dacChannel=1,
            ),
        ]

    @cas9epics.dproperty
    def ADC_io(self):
        return [
            LJU3ADCRelay(
                ebridge=self.ebridge.ADC_map[0],
                parent=self,
                posChannel=0,
                clear_val=float("inf"),
            ),
            LJU3ADCRelay(
                ebridge=self.ebridge.ADC_map[1],
                parent=self,
                posChannel=1,
            ),
            LJU3ADCRelay(
                ebridge=self.ebridge.ADC_map[2],
                parent=self,
                posChannel=2,
            ),
            LJU3ADCRelay(
                ebridge=self.ebridge.ADC_map[3],
                parent=self,
                posChannel=3,
            ),
            LJU3ADCRelay(
                ebridge=self.ebridge.ADC_map["p4n5"],
                parent=self,
                posChannel=4,
                negChannel=5,
            ),
            LJU3ADCRelay(
                ebridge=self.ebridge.ADC_map["p6n7"],
                parent=self,
                posChannel=6,
                negChannel=7,
            ),
        ]

    @cas9epics.dproperty
    def DOUT_io(self):
        return [
            LJU3DOUTRelay(
                ebridge=self.ebridge.DOUT_map[8],
                parent=self,
                dChannel=8,
            ),
            LJU3DOUTRelay(
                ebridge=self.ebridge.DOUT_map[9],
                parent=self,
                dChannel=9,
            ),
        ]

    @cas9epics.dproperty
    def DIN_io(self):
        return [
            LJU3DINRelay(
                ebridge=self.ebridge.DIN_map[10],
                parent=self,
                dChannel=10,
            ),
            LJU3DINRelay(
                ebridge=self.ebridge.DIN_map[11],
                parent=self,
                dChannel=11,
            ),
        ]
