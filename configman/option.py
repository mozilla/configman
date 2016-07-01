# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, division, print_function

import collections
import six

from configman.converters import (
    str_to_python_object,
    from_string_converters,
    to_str
)
from configman.config_exceptions import (
    CannotConvertError,
    OptionError
)


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
        secret=False,
        has_changed=False,
        foreign_data=None,
    ):
        self.name = name
        self.short_form = short_form
        self.default = default
        if isinstance(doc, (six.binary_type, six.text_type)):
            doc = to_str(doc).strip()
        self.doc = doc
        if from_string_converter is None:
            if default is not None:
                # take a qualified guess from the default value
                from_string_converter = self._deduce_converter(default)
        if isinstance(from_string_converter, (six.binary_type, six.text_type)):
            from_string_converter = str_to_python_object(from_string_converter)
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
        self.secret = secret
        self.has_changed = has_changed
        self.foreign_data = foreign_data

    #--------------------------------------------------------------------------
    def __str__(self):
        """return an instance of Option's value as a string.

        The option instance doesn't actually have to be from the Option class.
        All it requires is that the passed option instance has a ``value``
        attribute.
        """
        try:
            return self.to_string_converter(self.value)
        except TypeError:
            return to_str(self.value)

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
            return '<Option: %r, default=%r, value=%r, is_argument=%r>' % (
                self.name, self.default, self.value, self.is_argument
            )

    #--------------------------------------------------------------------------
    def _deduce_converter(self, default):
        default_type = type(default)

        return from_string_converters.get(
            default_type,
            default_type
        )

    #--------------------------------------------------------------------------
    def set_value(self, val=None):
        if val is None:
            val = self.default
        if isinstance(val, (six.binary_type, six.text_type)):
            val = to_str(val)
            try:
                new_value = self.from_string_converter(val)
                self.has_changed = new_value != self.value
                self.value = new_value
            except TypeError:
                self.has_changed = val != self.value
                self.value = val
            except ValueError:
                error_message = "In '%s', '%s' fails to convert '%s'" % (
                    self.name,
                    self.from_string_converter,
                    val
                )
                raise CannotConvertError(error_message)
        elif isinstance(val, Option):
            self.has_changed = val.default != self.value
            self.value = val.default
        elif isinstance(val, collections.Mapping) and 'default' in val:
            self.set_value(val["default"])
        else:
            self.has_changed = val != self.value
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
            self.has_changed = True
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
            reference_value_from=self.reference_value_from,
            secret=self.secret,
            has_changed=self.has_changed,
            foreign_data=self.foreign_data,
        )
        return o


#==============================================================================
class Aggregation(object):
    #--------------------------------------------------------------------------
    def __init__(
        self,
        name,
        function,
        secret=False,
    ):
        self.name = name
        if isinstance(function, (six.binary_type, six.text_type)):
            self.function = str_to_python_object(function)
        else:
            self.function = function
        self.value = None
        self.secret = secret

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
