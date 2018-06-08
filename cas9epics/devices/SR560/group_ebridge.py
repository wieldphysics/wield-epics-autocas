"""
"""
import declarative

from YALL.controls.core import contexts
from YALL.controls import epics
from YALL.controls.epics import panels as epics_panels

from .components.ebridge import (
    SR560Mapping,
)

from .components.service import (
    SR560ConnectionEBridge,
)


class SR560GroupEBridge(
    contexts.ParentCarrier,
    epics.EpicsCarrier,
    declarative.OverridableObject
):

    @declarative.dproperty
    def connection_service(self):
        ebrg = SR560ConnectionEBridge(
            egroup     = self.egroup,
        )
        return ebrg

    @declarative.dproperty
    def carm(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = SR560Mapping(
                display_name = "CARM control",
                egroup       = self.egroup.child("CARM"),
                parent       = self,
            )
        return ebrg

    @declarative.dproperty
    def medm_panel_1(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            panel = epics_panels.HVNestedMEDM(
                [
                    self.carm.medm_panel,
                ],
            )
        panel.medm_screen_filename_from_namechain(self.egroup.name_chain.child('SR560_1'))
        return panel



