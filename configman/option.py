# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is configman
#
# The Initial Developer of the Original Code is
# Mozilla Foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    K Lars Lohn, lars@mozilla.com
#    Peter Bengtsson, peterbe@mozilla.com
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import collections

import converters as conv
from config_exceptions import CannotConvertError, OptionError


#==============================================================================
class Option(object):
    #--------------------------------------------------------------------------
    def __init__(
        self,
        name,
        default=None,
        doc=None,
        from_string_converter=None,
        to_string_converter=None,
        value=None,
        short_form=None,
        exclude_from_print_conf=False,
        exclude_from_dump_conf=False,
        is_argument=False,
        likely_to_be_changed=False,
        not_for_definition=False,
        reference_value_from=None,
    ):
        self.name = name
        self.short_form = short_form
        self.default = default
        self.doc = doc
        if from_string_converter is None:
            if default is not None:
                # take a qualified guess from the default value
                from_string_converter = self._deduce_converter(default)
        if isinstance(from_string_converter, basestring):
            from_string_converter = conv.class_converter(from_string_converter)
        self.from_string_converter = from_string_converter
        # if this is not set, the type is used in converters.py to attempt
        # the conversion
        self.to_string_converter = to_string_converter
        if value is None:
            value = default
        self.value = value
        self.is_argument = is_argument
        self.exclude_from_print_conf = exclude_from_print_conf
        self.exclude_from_dump_conf = exclude_from_dump_conf
        self.likely_to_be_changed = likely_to_be_changed
        self.not_for_definition = not_for_definition
        self.reference_value_from = reference_value_from

    #--------------------------------------------------------------------------
    def __str__(self):
        """return an instance of Option's value as a string.

        The option instance doesn't actually have to be from the Option class.
        All it requires is that the passed option instance has a ``value``
        attribute.
        """
        if self.value is None:
            return ''
        if self.to_string_converter:
            s = self.to_string_converter(self.value)
        else:
            try:
                converter = conv.to_string_converters[type(self.value)]
                s = converter(self.value)
            except KeyError:
                if not isinstance(self.value, basestring):
                    s = unicode(self.value)
                else:
                    s = self.value
        if self.from_string_converter in conv.converters_requiring_quotes:
            s = "'''%s'''" % s
        return s

    #--------------------------------------------------------------------------
    def __eq__(self, other):
        if isinstance(other, Option):
            return (
                self.name == other.name
                and
                self.default == other.default
                and
                self.doc == other.doc
                and
                self.short_form == other.short_form
                and
                self.value == other.value
            )

    #--------------------------------------------------------------------------
    def __repr__(self):  # pragma: no cover
        if self.default is None:
            return '<Option: %r>' % self.name
        else:
            return '<Option: %r, default=%r>' % (self.name, self.default)

    #--------------------------------------------------------------------------
    def _deduce_converter(self, default):
        default_type = type(default)
        return conv.from_string_converters.get(default_type, default_type)

    #--------------------------------------------------------------------------
    def set_value(self, val=None):
        if val is None:
            val = self.default
        if isinstance(val, basestring):
            try:
                self.value = self.from_string_converter(val)
            except TypeError:
                self.value = val
            except ValueError:
                error_message = "In '%s', '%s' fails to convert '%s'" % (
                    self.name,
                    self.from_string_converter,
                    val
                )
                raise CannotConvertError(error_message)
        elif isinstance(val, Option):
            self.value = val.default
        elif isinstance(val, collections.Mapping) and 'default' in val:
            self.set_value(val["default"])
        else:
            self.value = val

    #--------------------------------------------------------------------------
    def set_default(self, val, force=False):
        """this function allows a default to be set on an option that dosen't
        have one.  It is used when a base class defines an Option for use in
        derived classes but cannot predict what value would useful to the
        derived classes.  This gives the derived classes the opportunity to
        set a logical default appropriate for the derived class' context.

        For example:

            class A(RequiredConfig):
                required_config = Namespace()
                required_config.add_option(
                  'x',
                  default=None
                )

            class B(A):
                A.required_config.x.set_default(68)

        parameters:
            val - the value for the default
            force - normally this function only works on Options that have not
                    had a default set (default is None).  This boolean allows
                    you to override an existing default.
        """
        if self.default is None or force:
            self.default = val
            self.set_value(val)
        else:
            raise OptionError(
                "cannot override existing default without using the 'force' "
                "option"
            )

    #--------------------------------------------------------------------------
    def copy(self):
        """return a copy"""
        o = Option(
            name=self.name,
            default=self.default,
            doc=self.doc,
            from_string_converter=self.from_string_converter,
            to_string_converter=self.to_string_converter,
            value=self.value,
            short_form=self.short_form,
            exclude_from_print_conf=self.exclude_from_print_conf,
            exclude_from_dump_conf=self.exclude_from_dump_conf,
            is_argument=self.is_argument,
            likely_to_be_changed=self.likely_to_be_changed,
            not_for_definition=self.not_for_definition,
            reference_value_from=self.reference_value_from
        )
        return o


#==============================================================================
class Aggregation(object):
    #--------------------------------------------------------------------------
    def __init__(
        self,
        name,
        function
    ):
        self.name = name
        if isinstance(function, basestring):
            self.function = conv.class_converter(function)
        else:
            self.function = function
        self.value = None

    #--------------------------------------------------------------------------
    def aggregate(self, all_options, local_namespace, args):
        self.value = self.function(all_options, local_namespace, args)

    #--------------------------------------------------------------------------
    def __eq__(self, other):
        if isinstance(other, Aggregation):
            return (
                self.name == other.name
                and self.function == other.function
            )
