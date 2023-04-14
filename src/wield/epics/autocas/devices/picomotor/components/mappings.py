#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""

#TODO, reorganize this
from YALL.controls.epics.epics_bridge_base import (
    EpicsBridgeBase,
    declarative.dproperty, declarative.mproperty, declarative.NOARG,
    declarative.callbackmethod,
    epics.EpicsDBRecord, epics.EpicsDBRecordStr,
    ValuePV, PVBooleanToggles, epics.PVBooleanSwitches,
)

from .medm import PicomotorMEDM, PicomotorSingleMEDM


class PicomotorConnectionMapping(EpicsBridgeBase):
    """
    """
    EPICS_PARTS_DB = {
        'CONNECTION_STATUS'   : epics.EpicsDBRecord(precision = 0, value = 0, burtRO=True),
        'CONNECTION_STR'      : epics.EpicsDBRecordStr(burtRO=True),
    }

    master_mode = False
    _NUM_STATUS = 1

    _connection_str   = ''
    PV_connection_str = None
    _control_switches = None

    def connect(self):
        if super(PicomotorConnectionMapping, self).connect():
            self.PV_connection_str = ValuePV(self.PVs_by_part['CONNECTION_STR'])

            self._control_switches = epics.PVBooleanSwitches(
                self.PVs_by_part["CONNECTION_STATUS"],
                bit_flip_react = self._controller_switches_react,
                maskset = list(range(self._NUM_STATUS)),
                value_lock = self.master_mode,
            )

            self._control_switches.connect()
            self.PV_connection_str.callback_register(key = self, callback = self._pv_callback_connection_str, call_immediate = True)
            return True
        return False

    def disconnect(self):
        if super(PicomotorConnectionMapping, self).disconnect():
            self._control_switches.disconnect()
            self.PV_connection_str.callback_register(key = self, remove = True)

            del self.PV_connection_str
            del self._control_switches
            return True
        return False

    @property
    def connection_str(self):
        return self._connection_str
    @connection_str.setter
    def connection_str(self, value):
        if not self.master_mode:
            raise RuntimeError("Can't set connection string unless master")
        if(self._connection_str != value):
            self._connection_str = value
            self.PV_connection_str.value = value
        return
    @callbackmethod
    def connection_str_react(self, value):
        return

    def _pv_callback_connection_str(self, value):
        if self._connection_str != value:
            self._connection_str = value
            self.connection_str_react(value)
        return

    def _controller_switches_react(self, bitnum, value):
        if bitnum == 0:
            self.connection_status_react(value)
        else:
            raise RuntimeError("got bitnum outside of mask")

    def connection_status_set(self, value):
        if not self.master_mode:
            raise RuntimeError("Can't set connection string unless master")
        self._control_switches.bit_assign(0, value)
        return

    @callbackmethod
    def connection_status_react(self, value):
        return


class PicomotorMapping(EpicsBridgeBase):
    """
    """

    EPICS_PARTS_DB = {
        'CONTROL_T'   : epics.EpicsDBRecord(precision = 0, value = 0, burtRO=True),
        'X_OFFSET'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'X_CONTROL'   : epics.EpicsDBRecord(precision = 0, value = 0),
        'Y_OFFSET'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'Y_CONTROL'   : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_0_DESC' : epics.EpicsDBRecordStr(),
        'PARK_1_DESC' : epics.EpicsDBRecordStr(),
        'PARK_1_X'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_1_Y'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_2_DESC' : epics.EpicsDBRecordStr(),
        'PARK_2_X'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_2_Y'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_3_DESC' : epics.EpicsDBRecordStr(),
        'PARK_3_X'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_3_Y'    : epics.EpicsDBRecord(precision = 0, value = 0),
    }

    @declarative.dproperty
    def display_name(self, name = declarative.NOARG):
        if name is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return name

    @declarative.dproperty
    def connect_epics(self, emapping = declarative.NOARG):
        if emapping is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return emapping

    @declarative.mproperty
    def medm_panel(self):
        return PicomotorMEDM(ebridge = self)

    _NUM_CONTROLS = 3
    NUM_CHANNELS = 2
    master_mode = False

    _x_offset    = 0.
    _y_offset    = 0.
    _x_control   = 0.
    _y_control   = 0.
    _park_0_desc = ''
    _control_switches = None

    PV_x_offset    = None
    PV_y_offset    = None
    PV_x_control   = None
    PV_y_control   = None
    PV_park_0_desc = None
    PV_park_1_X    = None
    PV_park_1_Y    = None
    PV_park_1_DESC = None
    PV_park_2_X    = None
    PV_park_2_Y    = None
    PV_park_2_DESC = None
    PV_park_3_X    = None
    PV_park_3_Y    = None
    PV_park_3_DESC = None

    def connect(self):
        if super(PicomotorMapping, self).connect():
            self._control_switches = PVBooleanToggles(
                self.PVs_by_part["CONTROL_T"],
                bit_toggle_react = self._controller_switches_react,
                maskset = list(range(self._NUM_CONTROLS)),
                control_only = not self.master_mode,
            )

            self.PV_x_offset    = ValuePV(self.PVs_by_part['X_OFFSET'])
            self.PV_y_offset    = ValuePV(self.PVs_by_part['Y_OFFSET'])
            self.PV_x_control   = ValuePV(self.PVs_by_part['X_CONTROL'])
            self.PV_y_control   = ValuePV(self.PVs_by_part['Y_CONTROL'])
            self.PV_park_0_desc = ValuePV(self.PVs_by_part['PARK_0_DESC'])

            #we don't add callbacks to these, but they are needed when setting the master
            self.PV_park_1_X    = ValuePV(self.PVs_by_part['PARK_1_X'])
            self.PV_park_1_Y    = ValuePV(self.PVs_by_part['PARK_1_Y'])
            self.PV_park_1_DESC = ValuePV(self.PVs_by_part['PARK_1_DESC'])
            self.PV_park_2_X    = ValuePV(self.PVs_by_part['PARK_2_X'])
            self.PV_park_2_Y    = ValuePV(self.PVs_by_part['PARK_2_Y'])
            self.PV_park_2_DESC = ValuePV(self.PVs_by_part['PARK_2_DESC'])
            self.PV_park_3_X    = ValuePV(self.PVs_by_part['PARK_3_X'])
            self.PV_park_3_Y    = ValuePV(self.PVs_by_part['PARK_3_Y'])
            self.PV_park_3_DESC = ValuePV(self.PVs_by_part['PARK_3_DESC'])

            self._control_switches.connect()
            self.PV_x_offset.callback_register(key = self, callback = self._pv_callback_x_offset, call_immediate = True)
            self.PV_x_control.callback_register(key = self, callback = self._pv_callback_x_control, call_immediate = True)
            self.PV_y_offset.callback_register(key = self, callback = self._pv_callback_y_offset, call_immediate = True)
            self.PV_y_control.callback_register(key = self, callback = self._pv_callback_y_control, call_immediate = True)
            self.PV_park_0_desc.callback_register(key = self, callback = self._pv_callback_park_0_desc, call_immediate = True)
            return True
        return False

    def disconnect(self):
        if super(PicomotorMapping, self).connect():
            self._control_switches.disconnect()
            self.PV_x_offset.callback_register(key = self, callback = self._pv_callback_x_offset, remove = True)
            self.PV_x_control.callback_register(key = self, callback = self._pv_callback_x_control, remove = True)
            self.PV_y_offset.callback_register(key = self, callback = self._pv_callback_y_offset, remove = True)
            self.PV_y_control.callback_register(key = self, callback = self._pv_callback_y_control, remove = True)
            self.PV_park_0_desc.callback_register(key = self, callback = self._pv_callback_park_0_desc, remove = True)

            del self._control_switches
            del self.PV_x_offset
            del self.PV_y_offset
            del self.PV_x_control
            del self.PV_y_control
            del self.PV_park_0_desc
            del self.PV_park_1_X
            del self.PV_park_1_Y
            del self.PV_park_1_DESC
            del self.PV_park_2_X
            del self.PV_park_2_Y
            del self.PV_park_2_DESC
            del self.PV_park_3_X
            del self.PV_park_3_Y
            del self.PV_park_3_DESC
            return True
        return False

    @property
    def x_offset(self):
        return self._x_offset
    @x_offset.setter
    def x_offset(self, value):
        if(self._x_offset != value):
            self._x_offset = value
            self.PV_x_offset.value = value
        return
    @callbackmethod
    def x_offset_react(self, value):
        return

    def _pv_callback_x_offset(self, value):
        if self._x_offset != value:
            self._x_offset = value
            self.x_offset_react(value)
        return

    @property
    def y_offset(self):
        return self._y_offset
    @y_offset.setter
    def y_offset(self, value):
        if(self._y_offset != value):
            self._y_offset = value
            self.PV_y_offset.value = value
        return
    @callbackmethod
    def y_offset_react(self, value):
        return

    def _pv_callback_y_offset(self, value):
        if self._y_offset != value:
            self._y_offset = value
            self.y_offset_react(value)
        return

    @property
    def x_control(self):
        return self._x_control
    @x_control.setter
    def x_control(self, value):
        if(self._x_control != value):
            self._x_control = value
            self.PV_x_control.value = value
        return
    @callbackmethod
    def x_control_react(self, value):
        return

    def _pv_callback_x_control(self, value):
        if self._x_control != value:
            self._x_control = value
            self.x_control_react(value)
        return

    @property
    def y_control(self):
        return self._y_control
    @y_control.setter
    def y_control(self, value):
        if(self._y_control != value):
            self._y_control = value
            self.PV_y_control.value = value
        return
    @callbackmethod
    def y_control_react(self, value):
        return

    def _pv_callback_y_control(self, value):
        if self._y_control != value:
            self._y_control = value
            self.y_control_react(value)
        return

    @property
    def park_0_desc(self):
        return self._park_0_desc
    @park_0_desc.setter
    def park_0_desc(self, value):
        if(self._park_0_desc != value):
            self._park_0_desc = value
            self.PV_park_0_desc.value = value
        return
    @callbackmethod
    def park_0_desc_react(self, value):
        return

    def _pv_callback_park_0_desc(self, value):
        if self._park_0_desc != value:
            self._park_0_desc = value
            self.park_0_desc_react(value)
        return

    def _controller_switches_react(self, bitnum):
        if bitnum == 0:
            self.park_1_set_react()
        elif bitnum == 1:
            self.park_2_set_react()
        elif bitnum == 2:
            self.park_3_set_react()
        else:
            raise RuntimeError("got bitnum outside of mask")

    #@callbackmethod
    def park_1_set_react(self):
        self.x_offset = self.PV_park_1_X.value
        self.y_offset = self.PV_park_1_Y.value
        self.park_0_desc = self.PV_park_1_DESC.value

    #@callbackmethod
    def park_2_set_react(self):
        self.x_offset = self.PV_park_2_X.value
        self.y_offset = self.PV_park_2_Y.value
        self.park_0_desc = self.PV_park_2_DESC.value

    #@callbackmethod
    def park_3_set_react(self):
        self.x_offset = self.PV_park_3_X.value
        self.y_offset = self.PV_park_3_Y.value
        self.park_0_desc = self.PV_park_3_DESC.value


class PicomotorSingleMapping(EpicsBridgeBase):
    """
    """
    EPICS_PARTS_DB = {
        'CONTROL_T'   : epics.EpicsDBRecord(precision = 0, value = 0, burtRO=True),
        'X_OFFSET'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'X_CONTROL'   : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_0_DESC' : epics.EpicsDBRecordStr(),
        'PARK_1_DESC' : epics.EpicsDBRecordStr(),
        'PARK_1_X'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_2_DESC' : epics.EpicsDBRecordStr(),
        'PARK_2_X'    : epics.EpicsDBRecord(precision = 0, value = 0),
        'PARK_3_DESC' : epics.EpicsDBRecordStr(),
        'PARK_3_X'    : epics.EpicsDBRecord(precision = 0, value = 0),
    }

    @declarative.dproperty
    def display_name(self, name = declarative.NOARG):
        if name is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return name

    _NUM_CONTROLS = 3
    NUM_CHANNELS = 1

    @declarative.dproperty
    def connect_epics(self, emapping = declarative.NOARG):
        if emapping is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return emapping

    @declarative.mproperty
    def medm_panel(self):
        return PicomotorSingleMEDM(ebridge = self)

    _x_offset    = 0.
    _x_control   = 0.
    _park_0_desc = ''
    master_mode  = False

    _control_switches = None
    PV_x_offset    = None
    PV_x_control   = None
    PV_park_0_desc = None
    PV_park_1_X    = None
    PV_park_1_DESC = None
    PV_park_2_X    = None
    PV_park_2_DESC = None
    PV_park_3_X    = None
    PV_park_3_DESC = None

    def connect(self):
        if super(PicomotorSingleMapping, self).connect():
            self._control_switches = PVBooleanToggles(
                self.PVs_by_part["CONTROL_T"],
                bit_toggle_react = self._controller_switches_react,
                maskset = list(range(self._NUM_CONTROLS)),
                control_only = not self.master_mode,
            )

            self.PV_x_offset    = ValuePV(self.PVs_by_part['X_OFFSET'])
            self.PV_x_control   = ValuePV(self.PVs_by_part['X_CONTROL'])
            self.PV_park_0_desc = ValuePV(self.PVs_by_part['PARK_0_DESC'])

            #we don't add callbacks to these, but they are needed when setting the master
            self.PV_park_1_X    = ValuePV(self.PVs_by_part['PARK_1_X'])
            self.PV_park_1_DESC = ValuePV(self.PVs_by_part['PARK_1_DESC'])
            self.PV_park_2_X    = ValuePV(self.PVs_by_part['PARK_2_X'])
            self.PV_park_2_DESC = ValuePV(self.PVs_by_part['PARK_2_DESC'])
            self.PV_park_3_X    = ValuePV(self.PVs_by_part['PARK_3_X'])
            self.PV_park_3_DESC = ValuePV(self.PVs_by_part['PARK_3_DESC'])

            self._control_switches.connect()
            self.PV_x_offset.callback_register(key = self, callback = self._pv_callback_x_offset, call_immediate = True)
            self.PV_x_control.callback_register(key = self, callback = self._pv_callback_x_control, call_immediate = True)
            self.PV_park_0_desc.callback_register(key = self, callback = self._pv_callback_park_0_desc, call_immediate = True)
            return True
        return False

    def disconnect(self):
        if super(PicomotorSingleMapping, self).connect():
            self._control_switches.disconnect()
            self.PV_x_offset.callback_register(key = self, callback = self._pv_callback_x_offset, remove = True)
            self.PV_x_control.callback_register(key = self, callback = self._pv_callback_x_control, remove = True)
            self.PV_park_0_desc.callback_register(key = self, callback = self._pv_callback_park_0_desc, remove = True)

            del self.PV_x_offset
            del self.PV_x_control
            del self.PV_park_0_desc
            del self.PV_park_1_X
            del self.PV_park_1_DESC
            del self.PV_park_2_X
            del self.PV_park_2_DESC
            del self.PV_park_3_X
            del self.PV_park_3_DESC
            del self._control_switches
            return True
        return False

    @property
    def x_offset(self):
        return self._x_offset
    @x_offset.setter
    def x_offset(self, value):
        if(self._x_offset != value):
            self._x_offset = value
            self.PV_x_offset.value = value
        return
    @callbackmethod
    def x_offset_react(self, value):
        return

    def _pv_callback_x_offset(self, value):
        if self._x_offset != value:
            self._x_offset = value
            self.x_offset_react(value)
        return

    @property
    def x_control(self):
        return self._x_control
    @x_control.setter
    def x_control(self, value):
        if(self._x_control != value):
            self._x_control = value
            self.PV_x_control.value = value
        return
    @callbackmethod
    def x_control_react(self, value):
        return

    def _pv_callback_x_control(self, value):
        if self._x_control != value:
            self._x_control = value
            self.x_control_react(value)
        return

    @property
    def park_0_desc(self):
        return self._park_0_desc
    @park_0_desc.setter
    def park_0_desc(self, value):
        if(self._park_0_desc != value):
            self._park_0_desc = value
            self.PV_park_0_desc.value = value
        return
    @callbackmethod
    def park_0_desc_react(self, value):
        return

    def _pv_callback_park_0_desc(self, value):
        if self._park_0_desc != value:
            self._park_0_desc = value
            self.park_0_desc_react(value)
        return

    def _controller_switches_react(self, bitnum):
        if bitnum == 0:
            self.park_1_set_react()
        elif bitnum == 1:
            self.park_2_set_react()
        elif bitnum == 2:
            self.park_3_set_react()
        else:
            raise RuntimeError("got bitnum outside of mask")

    #@callbackmethod
    def park_1_set_react(self):
        self.x_offset = self.PV_park_1_X.value
        self.park_0_desc = self.PV_park_1_DESC.value
        return

    #@callbackmethod
    def park_2_set_react(self):
        self.x_offset = self.PV_park_2_X.value
        self.park_0_desc = self.PV_park_2_DESC.value
        return

    #@callbackmethod
    def park_3_set_react(self):
        self.x_offset = self.PV_park_3_X.value
        self.park_0_desc = self.PV_park_3_DESC.value
        return


