"""
"""
from __future__ import division, print_function, unicode_literals

import declarative
import declarative.argparse as declarg


class ListArgs(
    declarg.OOArgParse,
    declarative.OverridableObject
):
    @declarative.dproperty
    def cmd(self, val):
        return val

    @declarg.command()
    def hostedPVs(self, argv):
        """
        List the CAS PVs hosted by this task
        """
        program = self.cmd.meta_program_generate()
        #TODO, make this not list external
        cas_db = program.root.cas_db_generate()
        pvs = list(cas_db.keys())
        pvs.sort()
        for pv in pvs:
            if not cas_db[pv]['remote']:
                print(pv)

    @declarg.command()
    def remotePVs(self, argv):
        """
        List the external PVs connected by this task
        """
        program = self.cmd.meta_program_generate()
        #TODO, make this not list external
        cas_db = program.root.cas_db_generate()
        pvs = list(cas_db.keys())
        pvs.sort()
        for pv in pvs:
            if cas_db[pv]['remote']:
                print(pv)



