def const(x):
    return x


def native(x):
    return x


def viper(x):
    return x


def schedule(func, arg):
    """Mock of micropython.schedule.

    On hardware this defers func(arg) to a soft interrupt shortly after the current
    interrupt returns. Tests run it immediately so that events are synchronous and
    assertions can follow the call that produced them.
    """
    func(arg)
