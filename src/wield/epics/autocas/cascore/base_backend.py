#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


from wield import declarative
import numpy as np
import pcaspy
import pcaspy.tools

from . import relay_values


class CASCollector(declarative.OverridableObject):
    @declarative.dproperty
    def rv_names(self):
        """
        Mapping from RelayValue or RelayBool to a PV name
        """
        return {}

    @declarative.dproperty
    def rv_db(self):
        """
        Mapping from RelayValue or RelayBool to a PV settings dictionary
        """
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
            dcopy["rv"] = rv
            db_gen[name] = dcopy
        return db_gen

    def prefix2channel(self, prefix):
        raise NotImplementedError()

    def cas_host(
        self,
        rv,
        name=None,
        prefix=None,
        self_prefix=None,
        conf_name=None,
        ctree=None,
        # deprecated, use "interaction" instead
        writable=None,
        # must be one of ['report', 'external', 'internal', 'setting']
        interaction=None,
        # defaults to True, warns if externally hosted PV's are changed. Also warns if setting RV's are changed
        warnings=None,
        type=None,
        count=None,
        enums=None,
        mt_assign=None,
        prec=None,
        unit=None,
        lolim=None,
        hilim=None,
        low=None,
        high=None,
        lolo=None,
        hihi=None,
        adel=None,
        mdel=None,
        EDCU=None,
        burt=None,
        burtRO=None,
        urgentsave_s=None,
        deferred=False,
        remote=False,
        # **kwargs
    ):
        # TODO, need some way to check that multiple PV's of the same name are not registered
        if conf_name is None:
            conf_name = name

        if conf_name is None:
            raise RuntimeError("Must specify either conf_name or name")

        if ctree is not None:
            cdb = ctree[conf_name]
        else:
            cdb = None

        if prefix is None:
            prefix = list(self_prefix) + [name]

        if cdb is not None:
            prefix = cdb.get_configured(
                "prefix",
                default=prefix,
                about="Prefix to construct the PV channel name",
            )

        # TODO allow direct setting channel name from ctree

        if self.rv_names.get(rv, None) is not None:
            raise RuntimeError(
                "Can't host the same RV with different names (yet) hosting {0} and {1}".format(
                    self.rv_names.get(rv), prefix
                )
            )
        self.rv_names[rv] = prefix

        if isinstance(rv, relay_values.CASRelay):
            db = rv.db_defaults()
        else:
            db = dict()

        # check interaction types and set some defaults based on interaction on the given type
        interaction_types = ["report", "external", "internal", "setting", "command"]

        def check_interaction(interaction):
            if interaction is None:
                raise RuntimeError("Must Specify the interaction type for all PV's")
            if interaction not in interaction_types:
                raise RuntimeError(
                    "Unknown interaction type: must be one of {0}".format(
                        interaction_types
                    )
                )
            return interaction

        interaction = check_interaction(interaction)
        if interaction == "command":
            if burt is None:
                burt = False
            if burtRO is None:
                burtRO = True
            if EDCU is None:
                EDCU = False
        elif interaction == "setting":
            if burt is None:
                burt = True
            if burtRO is None:
                burtRO = False
        elif interaction == "report":
            if burt is None:
                burt = True
            if burtRO is None:
                burtRO = True
        elif interaction == "external":
            if burt is None:
                burt = False
            if burtRO is None:
                burtRO = True
        elif interaction == "internal":
            if burt is None:
                burt = True
            if burtRO is None:
                burtRO = False

        # ----------------- SETUP DEFAULTS
        # use the values already specified to setup and generate defaults

        # a convenient way to inject all of the settings
        db_inj = dict(
            EDCU=EDCU,
            type=type,
            count=count,
            enums=enums,
            prec=prec,
            unit=unit,
            lolim=lolim,
            hilim=hilim,
            low=low,
            high=high,
            lolo=lolo,
            hihi=hihi,
            adel=adel,
            mdel=mdel,
            burt=burt,
            burtRO=burtRO,
            urgentsave_s=urgentsave_s,
            remote=remote,
            deferred=deferred,
            interaction=interaction,
        )
        for k, v in db_inj.items():
            if v is not None:
                db[k] = v

        def ctree_check(pname, tfunc):
            """
            This checks that the config tree has a value casted to type tfunc and overrides the
            current setting only if it is specified in the ctree.
            """
            cval = db.get(pname, None)
            # can't configure ones that are live
            if isinstance(cval, relay_values.RelayValueDecl):
                return
            cval2 = cdb.get_configured(pname, default=cval)

            # actually insert the parameter value
            if cval2 is not None and cval2 != cval:
                db[pname] = tfunc(cval2)
            return

        # TODO annotate all of these
        if cdb is not None:
            dtype = db["type"]
            ctree_check("remote", bool)
            ctree_check("deferred", bool)
            ctree_check("interaction", check_interaction)

            if dtype in ["float", "int"]:
                if db.get("count", None) is None:
                    ctree_check("EDCU", bool)
                    ctree_check("prec", int)
                    ctree_check("unit", str)
                    ctree_check("lolim", float)
                    ctree_check("hilim", float)
                    ctree_check("low", float)
                    ctree_check("high", float)
                    ctree_check("lolo", float)
                    ctree_check("hihi", float)
                    ctree_check("burt", bool)
                    ctree_check("burtRO", bool)
                else:
                    # nothing for waveforms
                    # TODO, allow waveforms
                    #
                    pass
            elif dtype in ["enum"]:
                ctree_check("EDCU", bool)
                ctree_check("burt", burt)
                ctree_check("burtRO", bool)
            elif dtype in ["char", "string"]:
                ctree_check("EDCU", bool)
                ctree_check("burt", burt)
                ctree_check("burtRO", bool)

        # special case for urgentsave_s type to only check the config if it is relevant
        def urgentsave_float_bool_none(val):
            if val is None:
                return False
            if isinstance(val, bool):
                return val
            return float(val)

        if db.get("burt"):
            ctree_check("urgentsave_s", urgentsave_float_bool_none)

        type = db["type"]
        if type == "float":
            pass
        elif type == "int":
            pass
        elif type == "string":
            pass
        elif type == "char":
            pass
        elif type == "enum":
            # check that this exists
            db["enums"]
        else:
            raise RuntimeError("Type Not Recognized")
        self.rv_db[rv] = db
        return
