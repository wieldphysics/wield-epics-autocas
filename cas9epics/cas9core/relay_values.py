"""
"""
from __future__ import division, print_function, unicode_literals

import numpy as np
import declarative

from declarative import (
    RelayValueRejected,
    RelayValueCoerced,
)

from declarative import RelayValue as RelayValueDecl


class CASRelay(object):
    """
    Mixin class to indicate that defaults exist for the CAS DB registration
    """
    def db_defaults(self):
        return {
            'rv' : self,
        }

class CASRelayBool(CASRelay):
    """
    Mixin class to indicate that defaults exist for the CAS DB registration
    """
    def db_defaults(self):
        return {
            'type':  'enum',
            'rv' :   self,
            "enums": ['False', 'True'],
        }

class CASRelayBoolRO(CASRelay):
    """
    Mixin class to indicate that defaults exist for the CAS DB registration
    """
    def db_defaults(self):
        return {
            'type':  'enum',
            'rv' :   self,
            "enums": ['False', 'True'],
            "writable" : False,
        }

class RelayValueFloat(CASRelay, RelayValueDecl):
    def validator(self, value):
        try:
            new_val = float(value)
        except ValueError:
            raise RelayValueRejected()
        if not np.isfinite(new_val):
            raise RelayValueRejected()
        if new_val != value:
            raise RelayValueCoerced(new_val)
        return new_val

    def db_defaults(self):
        return {
            'type': 'float',
            'rv' :  self,
        }


class RelayValueInt(CASRelay, RelayValueDecl):
    def validator(self, value):
        try:
            new_val = int(value)
        except ValueError:
            raise RelayValueRejected()
        if new_val != value:
            raise RelayValueCoerced(new_val)
        return new_val

    def db_defaults(self):
        return {
            'type': 'int',
            'rv' :  self,
        }


class RelayValueString(CASRelay, RelayValueDecl):
    def validator(self, value):
        try:
            new_val = str(value)[:40]
        except ValueError:
            raise RelayValueRejected()
        if new_val != value:
            raise RelayValueCoerced(new_val)
        return new_val

    def db_defaults(self):
        return {
            'type': 'string',
            'rv' :  self,
        }

class RelayValueLongString(CASRelay, RelayValueDecl):
    max_length = 100
    def validator(self, value):
        try:
            new_val = str(value)[:self.max_length]
        except ValueError:
            raise RelayValueRejected()
        if new_val != value:
            raise RelayValueCoerced(new_val)
        return new_val

    def db_defaults(self):
        return {
            'type': 'char',
            'rv' :  self,
            'count' : self.max_length,
        }


class RelayValueWaveform(CASRelay, RelayValueDecl):
    max_length = 100
    def validator(self, value):
        try:
            new_val = np.asarray(value, float)[:self.max_length]
        except ValueError:
            raise RelayValueRejected()
        if not np.all(np.isfinite(new_val)):
            raise RelayValueRejected()
        if new_val != value:
            raise RelayValueCoerced(new_val)
        #TODO catch shape mismatch and convert to Coerced
        return new_val

    def db_defaults(self):
        return {
            'type':   'float',
            'rv' :    self,
            'count' : self.max_length,
        }

class RelayValueEnum(CASRelay, RelayValueDecl):
    """
    Performs silent coercion to the integer state
    """
    def validator(self, value):
        if isinstance(value, str):
            try:
                new_val = self.state2int[value]
                return new_val
            except KeyError:
                raise RelayValueRejected()

        else:
            try:
                new_val = int(value)
            except ValueError:
                raise RelayValueRejected()

            if new_val != value:
                raise RelayValueRejected()

            try:
                self.int2state[new_val]
            except KeyError:
                raise RelayValueRejected()

            return new_val

    def __init__(self, initial_value, enum_map, validator = None):
        state2int = {}
        int2state = {}

        if isinstance(enum_map, (tuple, list)):
            for idx, state in enumerate(enum_map):
                state2int[state] = idx
                int2state[idx] = state
        else:
            for k, v in enum_map:
                if isinstance(k, str):
                    assert(isinstance(v, int))
                    state2int[v] = k
                    int2state[k] = v
                elif isinstance(k, int):
                    assert(isinstance(v, str))
                    int2state[v] = k
                    state2int[k] = v
                else:
                    raise RuntimeError("enum mapping must be mixture of integers and strings")

        self.state2int = state2int
        self.int2state = int2state

    @property
    def value_str(self):
        return self.int2state(self._value)

    def db_defaults(self):
        states = []
        try:
            for idx in range(len(self.int2state)):
                state = self.int2state[idx]
                states.append(state)
        except KeyError:
            raise RuntimeError("Enum must be sequential to use with EPICS CAS")
        return {
            'type':  'enum',
            'rv' :   self,
            "enums": states,
        }


class RelayBool(CASRelayBool, declarative.RelayBool):
    pass

class RelayBoolNot(CASRelayBoolRO, declarative.RelayBoolNot):
    pass

class RelayBoolAll(CASRelayBoolRO, declarative.RelayBoolAll):
    pass

class RelayBoolAny(CASRelayBoolRO, declarative.RelayBoolAny):
    pass

class RelayBoolNotAll(CASRelayBoolRO, declarative.RelayBoolNotAll):
    pass

class RelayBoolNotAny(CASRelayBoolRO, declarative.RelayBoolNotAny):
    pass