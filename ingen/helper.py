class objectview(object):
    def __init__(self, d):
        self.__dict__ = d

def centering(array):
    return (array[1:] + array[:-1]) / 2


def to_dict(obj, props):
    ret = {}
    for p in props:
        if type(p) is tuple:
            p, f = p
            ret[p] = f(obj.__getattribute__(p))
        else:
            ret[p] = obj.__getattribute__(p)
    return ret