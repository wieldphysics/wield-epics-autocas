"""
"""
from __future__ import division, print_function, unicode_literals

import declarative
import pcaspy
import pcaspy.tools

from . import relay_values


class CADriverServer(pcaspy.Driver):
    def _put_cb_generator_immediate(self, channel):
        def put_cb(value):
            self.setParam(channel, value)
            self.updatePVs()
        return put_cb

    def _put_cb_generator_deferred(self, channel):
        def put_cb(value):
            self.setParam(channel, value)
            self.updatePVs()
        return put_cb

    def _put_elem_cb_generator(self, channel, elem):
        def put_cb(value):
            use_entry = self.db_use[channel]
            #TODO 'value' maybe shouldn't be in this..
            use_entry[elem] = value
            self.setParamInfo(channel, use_entry)
        return put_cb

    def __init__(
            self,
            db,
            reactor,
            deferred_write_period = 1/4.
    ):
        self.db = db
        self.reactor = reactor

        self.cas = pcaspy.SimpleServer()
        self.cas_thread = pcaspy.tools.ServerThread(self.cas)
        self.cas_thread.daemon = True

        db_use = {}

        for channel, db_entry in self.db.items():
            rv = db_entry['rv']
            entry_use = {}

            if db_entry.get('immediate', True):
                rv.register(
                    callback = self._put_cb_generator_immediate(channel)
                )
            else:
                if deferred_write_period is not None and deferred_write_period > 0:
                    rv.register(
                        callback = self._put_cb_generator_deferred(channel)
                    )
                else:
                    rv.register(
                        callback = self._put_cb_generator_immediate(channel)
                    )

            #setup relays for any of the channel values to be inserted
            for elem in [
                    #"type" 	,  # 'float' PV data type. enum, string, char, float or int
                    "count" 	,  # 1 	Number of elements
                    "enums" 	,  # [] 	String representations of the enumerate states
                    "states" 	,  # [] 	Severity values of the enumerate states.
                    "prec",     # 0 	Data precision
                    "unit",     # '' 	Physical meaning of data
                    "lolim" 	,  # 0 	Data low limit for graphics display
                    "hilim" 	,  # 0 	Data high limit for graphics display
                    "low",     # 0 	Data low limit for alarm
                    "high",     # 0 	Data high limit for alarm
                    "lolo",     # 0 	Data low low limit for alarm
                    "hihi",     # 0 	Data high high limit for alarm
                    "adel",     # 0 	Archive deadband
                    "mdel",     # 0 	Monitor,                    value change deadband
                    #"scan", #  0 	Scan period in second. 0 means passive
                    #"asyn", #  False 	Process finishes asynchronously if True
                    #"asg",     #  '' 	Access security group name
                    #"value",  # 0 or '' 	Data initial value
            ]:
                if elem in db_entry:
                    elem_val = db_entry[elem]
                    if isinstance(elem_val, relay_values.RelayValueDecl):
                        entry_use[elem] = elem_val.value
                        elem_val.register(
                            callback = self._put_elem_cb_generator(channel, elem)
                        )

            if 'value' not in entry_use:
                entry_use['value'] = rv.value
            db_use[channel] = entry_use

            #writable = db_entry['writable']
        self.db_use = db_use
        #have to setup createPV before starting the driver
        self.cas.createPV('', db)
        super(CADriverServer, self).__init__()

        #pre-set all values, since this is apparently not done for you
        for channel, db_entry in self.db_use.items():
            self.setParam(channel, db_entry['value'])
            self.setParamInfo(channel, db_entry)
        self.updatePVs()

        #the deferred writes will happen this often
        if deferred_write_period is not None and deferred_write_period > 0:
            self.reactor.enqueue_looping(
                self.updatePVs,
                period_s = deferred_write_period,
            )

    def write(self, channel, value):
        # NOTE: for enum records the value here is the numeric value,
        # not the string.  setParam() expects the numeric value.

        # reject writes to non-writable channels
        if not self.db[channel].get('writable', False):
            return False

        # reject values that don't correspond to an actual index of
        # the enum
        # FIXME: this is apparently a feature? of cas that allows for
        # setting numeric values higher than the enum?
        if (
                self.db[channel]['type'] == 'enum'
                and (
                    value >= len(self.db[channel]['enums'])
                    or value < 0
                )
        ):
            return False

        db = self.db[channel]
        rv = db['rv']
        mt_assign = db.get('mt_assign', False)
        try:
            if mt_assign:
                rv.put(value)
            else:
                with self.reactor.task_lock:
                    rv.put(value)
        except relay_values.RelayValueCoerced as E:
            value = E.preferred
            if mt_assign:
                rv.put_valid(E.preferred)
            else:
                with self.reactor.task_lock:
                    rv.put_valid(E.preferred)
            self.setParam(channel, value)
            self.updatePVs()
            return False
        except relay_values.RelayValueRejected:
            return False
        else:
            self.setParam(channel, value)
            #self.updatePVs()
            return True

    def start(self):
        self.cas_thread.start()

    def stop(self):
        self.cas_thread.stop()
        #join needed to prevent a sigabrt in python3
        self.cas_thread.join()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class CASCollector(declarative.OverridableObject):
    @declarative.dproperty
    def rv_names(self):
        return {}

    @declarative.dproperty
    def rv_db(self):
        return {}

    def cas_db_generate(self):
        db_gen = dict()
        for rv, db_entry in self.rv_db.items():
            name = self.rv_names.get(rv, None)
            if name is None:
                print("MISSING NAME: ", rv)
            elif isinstance(name, (list, tuple)):
                name = self.prefix2channel(name)
            dcopy = dict(db_entry)
            dcopy['rv'] = rv
            db_gen[name] = dcopy
        return db_gen

    def prefix2channel(self, prefix):
        raise NotImplementedError()

    def cas_host(
            self,
            rv,
            name      = None,
            prefix    = None,
            writable  = None,
            EDCU      = None,
            type      = None,
            count     = None,
            enum      = None,
            states    = None,
            prec      = None,
            unit      = None,
            lolim     = None,
            hilim     = None,
            low       = None,
            high      = None,
            lolo      = None,
            hihi      = None,
            adel      = None,
            mdel      = None,
            mt_assign = None,
    ):
        self.rv_names[rv] = list(prefix) + [name]

        if isinstance(rv, relay_values.CASRelay):
            db = rv.db_defaults()
        else:
            db = dict()

        # a convenient way to inject all of the settings
        db_inj = dict(
            writable = writable,
            EDCU     = EDCU,
            type     = type,
            count    = count,
            enum     = enum,
            states   = states,
            prec     = prec,
            unit     = unit,
            lolim    = lolim,
            hilim    = hilim,
            low      = low,
            high     = high,
            lolo     = lolo,
            hihi     = hihi,
            adel     = adel,
            mdel     = mdel,
        )
        for k, v in db_inj.items():
            if v is not None:
                db[k] = v

        #if 'states' in db:
        #    states = db['states']
        #    #must convert away from unicode to keep pcaspy happy
        #    states = [unicode(s).encode('ascii', 'replace') for s in states]
        #    db['states'] = states

        type = db['type']
        if type == 'float':
            pass
        elif type == 'int':
            pass
        elif type == 'string':
            pass
        elif type == 'char':
            pass
        elif type == 'enum':
            #check that this exists
            print(db)
            db['enums']
        else:
            raise RuntimeError("Type Not Recognized")
        self.rv_db[rv] = db
        return
