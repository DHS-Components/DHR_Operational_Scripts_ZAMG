# helper function to have a timedelta object formatted to a nice 'H:M:S' string
def strfdelta(tdelta):
    d = {}
    hours, rem = divmod(int(tdelta.total_seconds()), 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    return "{H}:{M}:{S}".format(**d)