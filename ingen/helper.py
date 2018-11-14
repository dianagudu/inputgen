class objectview(object):
    def __init__(self, d):
        self.__dict__ = d

def centering(array):
    return (array[1:] + array[:-1]) / 2
