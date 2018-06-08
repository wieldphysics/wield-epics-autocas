"""
"""
from __future__ import division, print_function
import numpy as np
import time

import declarative

import YALL.controls.core.contexts as contexts
import YALL.controls.epics as epics

from .epics_relay import EpicsIndirectEBridge, EpicsIndirectController


class PDCalibratorEBridge(
    #contexts.EpicsCarrier,
    epics.EpicsRelayUser,
    contexts.ParentCarrier,
    epics.Connectable,
):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    name = '<NONAME>'

    @declarative.dproperty
    def indirect(self, ind = declarative.NOARG):
        if ind is declarative.NOARG:
            ind = EpicsIndirectEBridge(
                parent = self,
                egroup = self.egroup,
                #rv_chn_out = None,
            )
        ind.state_connect.bool_register(self.state_connect)
        return ind

    @RELAY_EPICS.bool_add('USE_REF', buttons = True, binding_type = 'RW')
    @declarative.dproperty
    def rv_use_ref(self):
        rv = declarative.RelayBool(False)
        return rv

    @RELAY_EPICS.float_value_add('MW', precision = 5, value = 0, binding_type = 'ext')
    @declarative.dproperty
    def rv_mw(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add('PERCREF', precision = 5, value = 0, binding_type = 'ext')
    @declarative.dproperty
    def rv_mw_perc(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add('V', precision = 5, value = 0, binding_type = 'ext')
    @declarative.dproperty
    def rv_V(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add('REF', precision = 5, value = 0, shadow = True)
    @declarative.dproperty
    def rv_reference(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add('TRANS_OHMS', precision = 5, value = 1000, shadow = True)
    @declarative.dproperty
    def rv_transimpedance(self):
        rv = declarative.RelayValue(1000)
        return rv

    @RELAY_EPICS.float_value_add('GAIN', precision = 5, value = 1, shadow = True)
    @declarative.dproperty
    def rv_gain(self):
        rv = declarative.RelayValue(1)
        return rv

    @RELAY_EPICS.float_value_add('GAIN_DB', precision = 5, value = 1, shadow = True)
    @declarative.dproperty
    def rv_gain_db(self):
        rv = declarative.RelayValue(1)
        return rv

    @RELAY_EPICS.float_value_add('LAMBDA_NM', precision = 5, value = 1064, shadow = True)
    @declarative.dproperty
    def rv_lambda_nm(self):
        rv = declarative.RelayValue(1064)
        return rv

    @RELAY_EPICS.float_value_add('SUBV', precision = 5, value = 0, shadow = True)
    @declarative.dproperty
    def rv_subtract(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add('LP_HZ', precision = 5, value = 1, shadow = True)
    @declarative.dproperty
    def rv_lowpass_Hz(self):
        rv = declarative.RelayValue(1, validator = declarative.min_max_validator(.0001, 100))
        return rv

    @RELAY_EPICS.float_value_add('WIN_PERC', precision = 5, value = 10, shadow = True)
    @declarative.dproperty
    def rv_lowpass_window_percent(self):
        rv = declarative.RelayValue(10)
        return rv

    @RELAY_EPICS.float_value_add('WIN_MINV', precision = 5, value = 0, shadow = True)
    @declarative.dproperty
    def rv_lowpass_window_min(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.callback_add('SET_REFERENCE')
    @declarative.callbackmethod
    def set_reference(self):
        return

    @RELAY_EPICS.callback_add('SET_TRANS')
    @declarative.callbackmethod
    def ref_to_trans(self):
        return

    @RELAY_EPICS.callback_add('SET_SUBTRACT')
    @declarative.callbackmethod
    def set_subtract_V(self):
        return

    @declarative.mproperty
    def medm_settings_panel(self):
        medm = epics.MEDMSystemScreen(
            system        = self,
            relpath       = __file__,
            medm_template = 'PD_CAL_SETTINGS.adl',
        )
        medm.medm_screen_filename_from_namechain(self.egroup.name_chain.child('SETTINGS'))
        return medm

    @declarative.mproperty
    def medm_view_panel(self):
        medm = epics.MEDMSystemScreen(
            system        = self,
            relpath       = __file__,
            medm_template = 'PD_CAL_VIEW_BIG.adl',
        )
        return medm

    def medm_embed_panels(self):
        return {'PANEL_FNAME' : self.medm_settings_panel}

    def augment_medm(self, pvs_by_part, extra_replace, prefix = ''):
        super(PDCalibratorEBridge, self).augment_medm(pvs_by_part, extra_replace, prefix = prefix)
        self.indirect.augment_medm(pvs_by_part, extra_replace, prefix = prefix + 'IND_')
        extra_replace['TITLE'] = self.name
        #extra_replace['PANEL_FNAME'] = self.medm_settings_panel.medm_screen_filename
        return


class PDCalibratorController(
    contexts.AlertsUser,
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject
):
    master_mode = True

    _last_update_t = 0

    @declarative.dproperty
    def ebridge(self, ebr):
        ebr.rv_connect_mode.value = 'master'
        ebr.state_connect.bool_register(self.state_connect_epics)
        return ebr

    @declarative.dproperty
    def indirect(self):
        if self.ebridge.indirect is not None:
            ctrl = EpicsIndirectController(
                parent = self,
                ebridge = self.ebridge.indirect,
            )
        return ctrl

    @declarative.dproperty
    def setup_callbacks(self):
        def set_reference():
            self.ebridge.rv_reference.value = self.ebridge.rv_mw.value
        self.ebridge.set_reference.register(
            callback = set_reference,
        )
        def ref_to_trans():
            self.ebridge.rv_transimpedance.value *= self.ebridge.rv_mw.value / self.ebridge.rv_reference.value
        self.ebridge.ref_to_trans.register(
            callback = ref_to_trans,
        )
        def subtract_V():
            self.ebridge.rv_subtract.value += self.ebridge.rv_V.value
        self.ebridge.set_subtract_V.register(
            callback = subtract_V,
        )
        return declarative.Bunch(locals())

    @declarative.dproperty
    def V_to_MW_setup(self):
        rv_mw = self.ebridge.rv_mw
        rv_mw_perc = self.ebridge.rv_mw_perc
        rv_ref = self.ebridge.rv_reference
        rv_V = self.ebridge.rv_V
        rv_V_sub = self.ebridge.rv_subtract
        rv_LP_Hz = self.ebridge.rv_lowpass_Hz
        def Vind_to_V(value):
            new_t = time.time()
            delta_t = new_t - self._last_update_t
            self._last_update_t = new_t

            value = value - rv_V_sub.value

            if abs(value - rv_V.value) > abs(rv_V.value + self.ebridge.rv_lowpass_window_min.value) * self.ebridge.rv_lowpass_window_percent.value / 100:
                LP_weight = 1
            else:
                LP_weight = delta_t * rv_LP_Hz.value
                if LP_weight > 1:
                    LP_weight = 1
            rv_V.value = (1 - LP_weight) * rv_V.value + LP_weight * value

        self.ebridge.indirect.rv_relay.register(
            callback = Vind_to_V,
        )
        def V_to_MW(value):
            val_mw = value * self._gain
            try:
                rv_mw_perc.value = 100 * val_mw / rv_ref.value
            except ZeroDivisionError:
                rv_mw_perc.value = -8888.888
            if not self.ebridge.rv_use_ref:
                rv_mw.value = val_mw
            else:
                rv_mw.value = rv_ref.value
        self.ebridge.rv_V.register(
            callback = V_to_MW,
        )

        def Vsub_to_MW(value):
            V_to_MW(self.ebridge.rv_V.value)
        self.ebridge.rv_subtract.register(
            callback = Vsub_to_MW,
        )

        def Vref_to_MW(value):
            V_to_MW(self.ebridge.rv_V.value)
        self.ebridge.rv_reference.register(
            callback = Vref_to_MW,
        )
        #so that we can access all of the methods for potential removal
        return declarative.Bunch(locals())

    _gain = 0

    @declarative.dproperty
    def gain_setup(self):
        def gain_cb_generic(value = None):
            try:
                self._gain = 1000 * (1.2398e3 / self.ebridge.rv_lambda_nm.value) / (self.ebridge.rv_transimpedance.value * self.ebridge.rv_gain.value)
            except ZeroDivisionError:
                self._gain = 0
            #call the other callback to force an update
            self.V_to_MW_setup.V_to_MW(self.ebridge.rv_V.value)
            return
        self.ebridge.rv_transimpedance.register(
            callback = gain_cb_generic,
            call_immediate = True,
        )
        self.ebridge.rv_lambda_nm.register(
            callback = gain_cb_generic,
        )
        def gain_cb(value):
            if value > 0:
                self.ebridge.rv_gain_db.put_exclude_cb(
                    20 * np.log10(value),
                    key = gain_db_cb,
                )
            elif value < 0:
                self.ebridge.rv_gain_db.put_exclude_cb(
                    20 * np.log10(-value),
                    key = gain_db_cb,
                )
            else:
                self.ebridge.rv_gain_db.put_exclude_cb(
                    -8888.8888,
                    key = gain_db_cb,
                )
            gain_cb_generic()
        self.ebridge.rv_gain.register(
            callback = gain_cb,
        )
        def gain_db_cb(value):
            if self.ebridge.rv_gain.value >= 0:
                self.ebridge.rv_gain.put_exclude_cb(
                    10**(value / 20),
                    key = gain_cb,
                )
            else:
                self.ebridge.rv_gain.put_exclude_cb(
                    -10**(value / 20),
                    key = gain_cb,
                )
            gain_cb_generic()

        self.ebridge.rv_gain_db.register(
            callback = gain_db_cb,
        )
        #so that we can access all of the methods for potential removal
        return declarative.Bunch(locals())

