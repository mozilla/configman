import datetime as dt


#-----------------------------------------------------------------------------------------------------------------
def datetime_from_ISO_string(s):
  """ Take an ISO date string of the form YYYY-MM-DDTHH:MM:SS.S
      and convert it into an instance of datetime.datetime
  """
  year = month = day = hour = minute = second = millisecond = 0
  try:
    year = int(s[0:4])
    month = int(s[5:7])
    day = int(s[8:10])
    if len(s) >= 19:
      hour = int(s[11:13])
      minute = int(s[14:16])
      second = int(s[17:19])
      if len(s) > 19:
        millisecond = int(s[20:])
  except Exception, e:
    raise ValueError('Invalid timestamp - "%s": %s' % (s, str(e)))
  return dt.datetime(year, month, day, hour, minute, second, millisecond)

#-----------------------------------------------------------------------------------------------------------------
def datetime_to_ISO_string(aDate):
  """ Take a datetime and convert to string of the form YYYY-MM-DDTHH:MM:SS.S
  """
  return aDate.isoformat()
#-----------------------------------------------------------------------------------------------------------------
def hours_str_to_timedelta(hoursAsString):
  return dt.timedelta(hours=int(hoursAsString))

#-----------------------------------------------------------------------------------------------------------------
def timedelta_to_seconds(td):
  return td.days * 24 * 60 * 60 + td.seconds

#-------------------------------------------------------------------------------
def str_to_timedelta(input_str):
    """ a string conversion function for timedelta for strings in the format
    DD:HH:MM:SS
    """
    days,hours,minutes,seconds = 0,0,0,0
    details = input_str.split(':')
    if len(details) >= 4:
        days = int(details[-4])
    if len(details) >= 3:
        hours = int(details[-3])
    if len(details) >= 2:
        minutes = int(details[-2])
    if len(details) >= 1:
        seconds = int(details[-1])
    return datetime.timedelta(days = days, hours = hours, minutes = minutes,
                              seconds = seconds)

#-------------------------------------------------------------------------------
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
