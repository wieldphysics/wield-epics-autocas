"""
"""
from os import path

from YALL.controls.epics.medm_bridge_base import (
    MEDMBridgeBase, epics.MEDMTemplatePanel,
    #declarative.dproperty, declarative.NOARG,
)


class PicomotorMEDM(MEDMBridgeBase):
    """
    """
    MEDM_SOURCE_FNAME = path.join(path.dirname(__file__), 'medm', 'PICOMOTOR.adl')

    def generate_medm(self):
        pvs = dict(self.ebridge.PVs_by_part)
        pvs.update(self.ebridge.connect_epics.PVs_by_part)
        medm = epics.MEDMTemplatePanel(
            self.MEDM_SOURCE_FNAME,
            pvs,
            extra_replace = {'TITLE': self.ebridge.display_name},
        )
        return medm


class PicomotorSingleMEDM(MEDMBridgeBase):
    MEDM_SOURCE_FNAME = path.join(path.dirname(__file__), 'medm', 'PICOMOTOR_SINGLE.adl')

    def generate_medm(self):
        pvs = dict(self.ebridge.PVs_by_part)
        pvs.update(self.ebridge.connect_epics.PVs_by_part)
        medm = epics.MEDMTemplatePanel(
            self.MEDM_SOURCE_FNAME,
            pvs,
            extra_replace = {'TITLE': self.ebridge.display_name},
        )
        return medm


