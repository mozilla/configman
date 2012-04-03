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

import datetime


def datetime_from_ISO_string(s):
    """ Take an ISO date string of the form YYYY-MM-DDTHH:MM:SS.S
    and convert it into an instance of datetime.datetime
    """
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        try:
            return datetime.datetime.strptime(s, '%Y-%m-%d')
        except ValueError:
            return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')


def date_from_ISO_string(s):
    """ Take an ISO date string of the form YYYY-MM-DD
    and convert it into an instance of datetime.date
    """
    return datetime.datetime.strptime(s, '%Y-%m-%d').date()


def datetime_to_ISO_string(aDate):
    """ Take a datetime and convert to string of the form YYYY-MM-DDTHH:MM:SS.S
    """
    return aDate.isoformat()


def date_to_ISO_string(aDate):
    """ Take a datetime and convert to string of the form YYYY-MM-DD
    """
    return aDate.strftime('%Y-%m-%d')


def hours_str_to_timedelta(hoursAsString):
    return datetime.timedelta(hours=int(hoursAsString))


def timedelta_to_seconds(td):
    return td.days * 24 * 60 * 60 + td.seconds


def str_to_timedelta(input_str):
    """ a string conversion function for timedelta for strings in the format
    DD:HH:MM:SS
    """
    days, hours, minutes, seconds = 0, 0, 0, 0
    details = input_str.split(':')
    if len(details) >= 4:
        days = int(details[-4])
    if len(details) >= 3:
        hours = int(details[-3])
    if len(details) >= 2:
        minutes = int(details[-2])
    if len(details) >= 1:
        seconds = int(details[-1])
    return datetime.timedelta(days=days,
                              hours=hours,
                              minutes=minutes,
                              seconds=seconds)


def timedelta_to_str(aTimedelta):
    """ a conversion function for time deltas to string in the form
    DD:HH:MM:SS
    """
    days = aTimedelta.days
    temp_seconds = aTimedelta.seconds
    hours = temp_seconds / 3600
    minutes = (temp_seconds - hours * 3600) / 60
    seconds = temp_seconds - hours * 3600 - minutes * 60
    return '%d:%d:%d:%d' % (days, hours, minutes, seconds)
