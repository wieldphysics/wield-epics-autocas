"""
"""
from __future__ import division, print_function, unicode_literals

from .. import cas9core
from ..serial import SerialError
import re


float_re = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'


class IFRSigGenChannel(
    cas9core.CASUser,
):
    "Must be hosted by a IFR2026"

    @cas9core.dproperty
    def serial(self):
        return self.parent.serial

    @cas9core.dproperty
    def SBlist_readbacks(self):
        return []

    @cas9core.dproperty
    def SBlist_setters(self):
        return []

    @cas9core.dproperty
    def SB_parent(self, val):
        """
        Parent serial-block
        """
        return val

    @cas9core.dproperty
    def FM(self):
        fm = IFRSigGenChannelFM(
            parent = self,
            name = 'FM',
            SB_parent = self.SB_parent,
        )
        self.SBlist_setters.extend(fm.SBlist_setters)
        self.SBlist_readbacks.extend(fm.SBlist_readbacks)
        return

    @cas9core.dproperty_ctree(default = 10e3)
    def frequency_limit_low(self, val):
        assert(val > 0)
        return val

    @cas9core.dproperty_ctree(default = 1.4e9)
    def frequency_limit_high(self, val):
        assert(val > 0)
        return val

    #############################
    # RF FREQUENCY
    #############################
    @cas9core.dproperty
    def rv_frequency_set(self):
        default = self.ctree.setdefault('frequency_set', 100e6)

        rv = cas9core.RelayValueFloatLowHighMod(
            default,
            low  = self.frequency_limit_low,
            high = self.frequency_limit_high,
            modulo = 1,
        )

        self.cas_host(
            rv,
            'freq_set',
            writable   = True,
            urgentsave = 10,
            prec       = 6,
        )
        return rv

    @cas9core.dproperty
    def SB_freq_set(self):
        def action_sequence(cmd):
            cmd.writeline(':CFRQ:VALUE {0:f}Hz'.format(self.rv_frequency_set.value))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'freq_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.SB_freq_RB)
        self.SBlist_setters.append(block)

        self.rv_frequency_set.register(callback = block)

        return block

    @cas9core.dproperty
    def rv_frequency_RB(self):
        default = self.ctree.setdefault('frequency_RB', -1, about = "frequency readback default (used when value unavailable)")
        rv = cas9core.RelayValueFloat(default)
        self.cas_host(
            rv,
            'FREQ_RB',
            writable = False,
            prec     = 6,
        )
        return rv

    @cas9core.dproperty
    def SB_freq_RB(self):
        #two groups 0: the frequency in Hz 1: The increment in Hz
        #the last group allows parsing 2026 and 2023 return values
        re_FREQVALUE = re.compile('^:CFRQ:VALUE ({0});INC ({0})(?:|;MODE FIXED)$'.format(float_re))

        def action_sequence(cmd):
            cmd.writeline('CFRQ?')
            response = cmd.readline()
            match = re_FREQVALUE.match(response)
            if not match:
                raise SerialError("Frequency Request: {0}".format(response))
            self.rv_frequency_RB.value = float(match.group(1))

        block = self.serial.block_add(
            action_sequence,
            ordering = 10,
            parent   = self.SB_parent,
            name = 'freq_RB',
            prefix = self.prefix_full,
        )
        self.SBlist_readbacks.append(block)
        return block

    #############################
    # RF LEVEL
    #############################
    @cas9core.dproperty_ctree(default = -120)
    def level_dbm_limit_low(self, val):
        """
        low limit of RF Output level in dbm
        """
        assert(val >= -120)
        return val

    @cas9core.dproperty_ctree(default = -10)
    def level_dbm_limit_high(self, val):
        """
        high limit of RF Output level in dbm (This can damage equipment to be too high! Be conservative here)
        """
        assert(val <= 20)
        return val

    @cas9core.dproperty
    def rv_level_dbm_set(self):
        default = self.ctree.setdefault('level_dbm_set', -120, about = 'default RF level')

        rv = cas9core.RelayValueFloatLowHighMod(
            default,
            low = self.level_dbm_limit_low,
            high = self.level_dbm_limit_high,
            modulo = 0.01,
        )

        self.cas_host(
            rv,
            'level_set',
            writable   = True,
            urgentsave = 10,
            prec       = 3,
        )
        return rv

    @cas9core.dproperty
    def SB_level_set(self):
        def action_sequence(cmd):
            level_dbm = self.rv_level_dbm_set.value
            if level_dbm > self.level_dbm_limit_high:
                print(level_dbm, self.level_dbm_limit_high)
                raise RuntimeError("RF Level above limit!")
            cmd.writeline(':RFLV:UNITS DBM;:RFLV:VALUE {0:.3f}DBM'.format(level_dbm))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'level_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.SB_level_RB)
        self.SBlist_setters.append(block)
        self.rv_level_dbm_set.register(callback = block)

        return block

    @cas9core.dproperty
    def rv_level_dbm_RB(self):
        default = self.ctree.setdefault('level_dbm_RB', -1, about = "level_dbm readback default (used when value unavailable)")
        rv = cas9core.RelayValueInt(default)
        self.cas_host(
            rv,
            'level_RB',
            writable = False,
            prec     = 3,
        )
        return rv

    @cas9core.dproperty
    def SB_level_RB(self):
        re_LEVELVALUE = re.compile('^:RFLV:UNITS DBM;TYPE (PD|EMF);VALUE ({0});INC {0};(ON|OFF)$'.format(float_re))

        def action_sequence(cmd):
            cmd.writeline('RFLV?')
            response = cmd.readline()
            match = re_LEVELVALUE.match(response)
            if not match:
                raise SerialError("Level_dbm Request: {0}".format(response))

            level_dbm = float(match.group(2))
            level_on = {"ON" : True, "OFF" : False}[match.group(3)]

            self.rv_level_dbm_RB.value = level_dbm
            self.rb_output_RB.value = level_on

        block = self.serial.block_add(
            action_sequence,
            ordering = 10,
            parent   = self.SB_parent,
            name = 'level_RB',
            prefix = self.prefix_full,
        )
        self.SBlist_readbacks.append(block)
        return block

    #####################################
    #  RF Output ON/OFF
    #####################################
    @cas9core.dproperty
    def rb_output_set(self):
        default = self.ctree.setdefault('output_set', False, about = 'default for activating RF output')

        rv = cas9core.RelayBool(default)

        self.cas_host(
            rv,
            'output_set',
            writable   = True,
            urgentsave = 10,
        )
        return rv

    @cas9core.dproperty
    def SB_output_set(self):
        def action_sequence(cmd):
            if self.rb_output_set:
                cmd.writeline(':RFLV:ON')
            else:
                cmd.writeline(':RFLV:OFF')
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'output_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.SB_level_RB)
        self.SBlist_setters.append(block)
        self.rb_output_set.register(callback = block)
        return block

    @cas9core.dproperty
    def rb_output_RB(self):
        default = self.ctree.setdefault('output_RB', True, about = "output status readback default (used when value unavailable)")
        rv = cas9core.RelayBool(default)
        self.cas_host(
            rv,
            'output_RB',
            writable = False,
        )
        return rv

    ###############################
    # Modulation Mode
    ###############################

    @cas9core.dproperty
    def rv_modmode_RB(self):
        rv = cas9core.RelayValueString('')
        self.cas_host(
            rv,
            'MODMODE_RB',
            writable = False,
        )
        return rv

    @cas9core.dproperty
    def SB_modmode_RB(self):
        def action_sequence(cmd):
            cmd.writeline('MODE?')
            response = cmd.readline()
            self.rv_modmode_RB.value = response

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent   = self.SB_parent,
            name = 'modmode_RP',
            prefix = self.prefix_full,
        )
        self.SBlist_readbacks.append(block)
        return block

    ###############################
    # Modulation Status
    ###############################
    @cas9core.dproperty
    def rb_mod_status_set(self):
        default = self.ctree.setdefault('modulation_status', False, about = 'default for activating modulation')

        rv = cas9core.RelayBool(default)

        self.cas_host(
            rv,
            'MODSTAT',
            writable   = True,
            urgentsave = 10,
        )
        return rv

    @cas9core.dproperty
    def SB_mod_status_set(self):
        def action_sequence(cmd):
            if self.rb_mod_status_set:
                cmd.writeline(':MOD:ON')
            else:
                cmd.writeline(':MOD:OFF')
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'mod_status_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.SB_mod_status_RB)
        self.SBlist_setters.append(block)
        self.rb_mod_status_set.register(callback = block)
        return block

    @cas9core.dproperty
    def rb_mod_status_RB(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb,
            'MODSTAT_RB',
            writable = False,
        )
        return rb

    @cas9core.dproperty
    def SB_mod_status_RB(self):
        #three groups 0: EMF type (not used) 1: output level in DBM 2: output power state
        re_MODSTAT = re.compile('^:MOD:(ON|OFF)$')

        def action_sequence(cmd):
            cmd.writeline('MOD?')
            response = cmd.readline()
            match = re_MODSTAT.match(response)
            if not match:
                raise SerialError("mod status request: {0}".format(response))

            mod_on = {"ON" : True, "OFF" : False}[match.group(1)]
            self.rb_mod_status_RB.value = mod_on

        block = self.serial.block_add(
            action_sequence,
            ordering = 10,
            parent   = self.SB_parent,
            name = 'level_RB',
            prefix = self.prefix_full,
        )
        self.SBlist_readbacks.append(block)
        return block


class IFRSigGenChannelFM(
    cas9core.CASUser,
):
    """
    Must be hosted by a IFRSigGenChannel
    """

    @cas9core.dproperty
    def serial(self):
        return self.parent.serial

    @cas9core.dproperty
    def SB_parent(self, val):
        """
        Parent serial-block used for FM control
        """
        return val

    @cas9core.dproperty
    def SBlist_readbacks(self):
        return []

    @cas9core.dproperty
    def SBlist_setters(self):
        return []

    @cas9core.dproperty_ctree(default = 1)
    def FM_devn_limit_low(self, val):
        assert(val > 0)
        return val

    @cas9core.dproperty_ctree(default = 100e3)
    def FM_devn_limit_high(self, val):
        assert(val > 0)
        return val

    #############################
    # RF FM_DEVN
    #############################
    @cas9core.dproperty
    def rv_FM_devn_set(self):
        default = self.ctree.setdefault('FM_devn_set', 10e3)

        rv = cas9core.RelayValueFloatLowHighMod(
            default,
            low  = self.FM_devn_limit_low,
            high = self.FM_devn_limit_high,
            modulo = 1,
        )

        self.cas_host(
            rv,
            'DEVN',
            writable   = True,
            urgentsave = 10,
            prec       = 3,
        )
        return rv

    @cas9core.dproperty
    def SB_devn_set(self):
        def action_sequence(cmd):
            cmd.writeline(':FM:DEVN {0:f}Hz'.format(self.rv_FM_devn_set.value))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'devn_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.SB_FM_RB)
        self.SBlist_setters.append(block)
        self.rv_FM_devn_set.register(callback = block)
        return block

    @cas9core.dproperty
    def rv_FM_devn_RB(self):
        default = self.ctree.setdefault('devn_RB', -1, about = "FM devn readback default (used when value unavailable)")
        rv = cas9core.RelayValueFloat(default)
        self.cas_host(
            rv,
            'DEVN_RB',
            writable = False,
            prec     = 3,
        )
        return rv

    @cas9core.dproperty
    def rv_coupling_RB(self):
        rv = cas9core.RelayValueEnum(0, ['INT', 'EXTAC', 'EXTALC', 'EXTDC'])
        self.cas_host(
            rv,
            'CPLG_RB',
            writable = False,
        )
        return rv

    @cas9core.dproperty
    def SB_FM_RB(self):
        #two groups 0: the frequency devn in Hz, 1: the coupling mode; 2: the local on/off; 3: the increment value
        re_DEVNVALUE = re.compile('^:FM:DEVN ({0});(INT|EXTAC|EXTALC|EXTDC)\s*;(ON|OFF)\s*;INC ({0})$'.format(float_re))

        def action_sequence(cmd):
            cmd.writeline('FM?')
            response = cmd.readline()
            match = re_DEVNVALUE.match(response)
            if not match:
                raise SerialError("FM Query: {0}".format(response))

            self.rv_FM_devn_RB.value = float(match.group(1))
            self.rv_coupling_RB.put_coerce(match.group(2))
            self.rb_FM_mod_status_RB.value = {"ON" : True, "OFF" : False}[match.group(3)]

        block = self.serial.block_add(
            action_sequence,
            ordering = 10,
            parent   = self.SB_parent,
            name = 'FM_RB',
            prefix = self.prefix_full,
        )
        self.SBlist_readbacks.append(block)
        return block

    ###############################
    # Modulation Status
    ###############################
    @cas9core.dproperty
    def rb_mod_status_set(self):
        default = self.ctree.setdefault('modulation_status', False, about = 'default for activating modulation')

        rv = cas9core.RelayBool(default)

        self.cas_host(
            rv,
            'MODSTAT',
            writable   = True,
            urgentsave = 10,
        )
        return rv

    @cas9core.dproperty
    def SB_mod_status_set(self):
        def action_sequence(cmd):
            if self.rb_mod_status_set:
                cmd.writeline(':FM:ON')
            else:
                cmd.writeline(':FM:OFF')
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'mod_status_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.SB_FM_RB)
        self.SBlist_setters.append(block)
        self.rb_mod_status_set.register(callback = block)
        return block

    @cas9core.dproperty
    def rb_FM_mod_status_RB(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb,
            'MODSTAT_RB',
            writable = False,
        )
        return rb
