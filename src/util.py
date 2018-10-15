import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def dtstr(dtime):
    t1 = [dtime.year, dtime.month, dtime.day]
    t2 = [dtime.hour, dtime.minute, dtime.second]
    return ' '.join([':'.join([str(x) for x in t1]),
                     '-'.join([str(x) for x in t2])])

def to_fb(tstamp):
    return tstamp*1000.0

def from_fb(tstamp):
    return tstamp/1000.0
