from datetime import datetime

class Timer():

    def __init__(self, start=True):
        self.start()
        self.ticks = []

    def start(self):
        self.start = datetime.now()
        self.ticks = []
        self.last_tick = self.start

    def stop(self):
        self.end = datetime.now()
        print '    Total time: %s' %  (self.end - self.start)

    def tick(self, msg=''):
        now = datetime.now()
        duration = now-self.last_tick
        print '    %s : %s' % (msg, duration)
        self.last_tick = now
        self.ticks.append(duration.seconds + duration.microseconds/1000000.0)


class Counter(object):
    """ simpler counter class """

    def __init__(self):
        self.value = 0

    def __iadd__(self, other):
        self.value += other

    def __repr__(self):
        return str(self.value)