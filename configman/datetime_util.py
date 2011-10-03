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
