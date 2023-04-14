#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import logging
from collections import namedtuple, Mapping

from wield.bunch.deep_bunch import DeepBunchSingleAssign, DeepBunch

CTreeKey = namedtuple('CTreeKey', ['namespace', 'name'])

class ConfigTree(object):
    """
    This object is an access wrapper for configuration tree needs. Values can only be gathered using specific methods, rather than the typical
    dictionary/mapping interface.
    """
    __slots__ = ('_dict',)
    VALUE_KEY                = CTreeKey('ctree', 'value')
    CONFIG_KEY               = CTreeKey('ctree', 'config')
    DEFAULT_KEY              = CTreeKey('ctree', 'default')
    ABOUT_KEY                = CTreeKey('ctree', 'about')
    CLASSIFICATION_KEY       = CTreeKey('ctree', 'classification')
    CLASSIFICATION_PRIME_KEY = CTreeKey('ctree', 'classification_prime')

    def __init__(self, _subdict):
        self._dict = _subdict
        return

    def _keygen(self, name):
        return CTreeKey('ctree extra', name)

    def __getitem__(self, key):
        subdict = self._dict[key]

        if self._check_type(subdict) in ['bad', 'value']:
            #TODO, make this check as safe as possible given what can come from configuration files
            logging.warning((
                'Accessing Configuration Subtree For key {0} but'
                ' it is storing a value for this key'
            ).format(key))

        return self.__class__(_subdict = subdict,)

    #not wanted for config tree's, too confusing
    #def __getattr__(self, key):
    #    try:
    #        return self.__getitem__(key)
    #    except KeyError:
    #        raise AttributeError("'{0}' not in {1}".format(key, self))

    def _check_type(self, subdict):
        ctreekeys = 0
        otherkeys = 0
        for k in subdict:
            if isinstance(k, CTreeKey):
                ctreekeys += 1
            else:
                otherkeys += 1
        if ctreekeys > 0 and otherkeys > 0:
            return 'bad'
        elif ctreekeys > 0:
            return 'value'
        elif otherkeys > 0:
            return 'tree'
        else:
            return 'empty'

    def get_configured(
            self,
            key,
            default,
            about = None,
            classification = None,
            validator = None,
            **kwargs
    ):
        """
        Gets the configured setting, using the default if not set in configuration file. Takes some arguments to annotate
        the configuration. These are stored by default, though the ctree system used through a subclass may not store these annotations

        about: a string describing the setting
        classification: a list of classification strings, the first in the list is the primary classification
        validator: a function to validate/cast both the default setting and the configured setting
        to ensure correct typing. It may generate warnings
        """
        cdict = self._dict[key]

        if self._check_type(cdict) in ['bad', 'tree']:
            #TODO, make this check as safe as possible given what can come from configuration files
            logging.warning((
                'Accessing Configuration For key {0} but'
                ' it is storing a subtree rather than a single value'
            ).format(key))

        try:
            return cdict.get(self.VALUE_KEY)
        except KeyError:
            pass

        #normalize the classification if it is a single string
        if isinstance(classification, str):
            classification = [classification]

        #add in annotation information if the keys are set
        if self.ABOUT_KEY is not None and about is not None:
            cdict[self.ABOUT_KEY] = about
        if self.CLASSIFICATION_KEY is not None and classification is not None:
            #convert to a set for easier search later
            cdict[self.CLASSIFICATION_KEY] = set(classification)
        if self.CLASSIFICATION_PRIME_KEY is not None and classification is not None:
            cdict[self.CLASSIFICATION_PRIME_KEY] = classification[0]
        for k, v in kwargs.items():
            cdict[self._keygen(k)] = v

        #if the key is None then we are not storing defaults
        if self.DEFAULT_KEY is not None:
            #ok, value has not yet been set
            ctdefault = cdict.setdefault(self.DEFAULT_KEY, default)
            if ctdefault != default:
                raise RuntimeError((
                    "Inconsistent defaults provided to configtree, "
                    "key: {0}, default: {1}, prev default: {2}"
                ).format(key, default, ctdefault))

        #now check if it is already configured
        try:
            config = cdict.get(self.CONFIG_KEY)
        except KeyError:
            #no configuration, so use default
            config = default

        if validator is not None:
            use_value = validator(config)
            if use_value != config:
                logging.warning((
                    "Configuration validator coerced value "
                    "for key {0} from {1} to {2}"
                ).format(key, config, use_value))
        else:
            use_value = config

        cdict[self.VALUE_KEY] = use_value
        return use_value

    def __contains__(self, key):
        for d in self._dicts:
            if key in d:
                return True
        return False

    def has_key(self, key):
        return key in self

    def __dir__(self):
        return dir(self._dict)

    def __repr__(self):
        return (
            '{0}({1})'
        ).format(
            self.__class__.__name__,
            self._dict,
        )

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(self.__class__.__name__ + '(<recurse>)')
        else:
            with p.group(4, self.__class__.__name__ + '([', '])'):
                first = True
                for d in self._dicts:
                    p.pretty(d)
                    p.breakable()
                if not first:
                    p.text(',')
                    p.breakable()
        return

class ConfigTreeBare(ConfigTree):
    #set these to None so that they are not stored
    DEFAULT_KEY        = None
    ABOUT_KEY          = None
    CLASSIFICATION_KEY = None


class ConfigTreeRoot(object):

    def __init__(
        self,
        annotations = True,
    ):
        self._dict = DeepBunchSingleAssign()
        self.annotations = annotations
        if annotations:
            self._ctree = ConfigTree(_subdict = self._dict)
        else:
            self._ctree = ConfigTreeBare(_subdict = self._dict)

    @property
    def ctree(self):
        return self._ctree

    def _key_load_recursive(self, key, nested_dict):
        #subCD is the inner configuration dict
        #subND is the inner nested dict
        def load_recursive(subCD, subND):
            if isinstance(subND, Mapping):
                for k, v in subND.items():
                    load_recursive(subCD[k], v)
            else:
                subCD[key] = subND
        load_recursive(self._dict, nested_dict)
        return

    def _key_retrieve_recursive(self, key):
        ctree_key = key
        #storage dict
        SD = DeepBunch()

        #subCD is the inner configuration dict
        #subSD is the inner nested storage dict
        def retrieve_recursive(subCD, subSD, elem_key):
            ctreekeys = 0
            otherkeys = 0
            for k, v in subCD.items():
                if isinstance(k, CTreeKey):
                    ctreekeys += 1
                else:
                    otherkeys += 1
                    #the key access of subSD is staggered with subCD
                    #since the current key of subSD must be the previous key of subCD
                    retrieve_recursive(v, subSD[elem_key], k)

            if ctreekeys > 0 and otherkeys > 0:
                raise RuntimeError("Config tree somehow has both kinds of keys, internal ctree keys and standard keys")
            elif ctreekeys > 0:
                #didn't do the assignment during the for loop, so do it now
                try:
                    subSD[elem_key] = subCD.get(ctree_key)
                except KeyError:
                    #missing this type of ctree key, oh well
                    pass

        #the bottom should always have sub-dictionaries
        for k, v in self._dict.items():
            retrieve_recursive(v, SD, k)
        return SD

    def config_load_recursive(self, nested_dict):
        return self._key_load_recursive(ConfigTree.CONFIG_KEY, nested_dict)

    def config_retrieve_recursive(self):
        return self._key_retrieve_recursive(ConfigTree.CONFIG_KEY)

    def value_retrieve_recursive(self):
        return self._key_retrieve_recursive(ConfigTree.VALUE_KEY)

    def about_retrieve_recursive(self):
        return self._key_retrieve_recursive(ConfigTree.ABOUT_KEY)

    def classification_retrieve_recursive(self):
        return self._key_retrieve_recursive(ConfigTree.CLASSIFICATION_KEY)

    def classification_prime_retrieve_recursive(self):
        return self._key_retrieve_recursive(ConfigTree.CLASSIFICATION_PRIME_KEY)

    def extra_retrieve_recursive(self, key):
        return self._key_retrieve_recursive(self._dict._keygen(key))

