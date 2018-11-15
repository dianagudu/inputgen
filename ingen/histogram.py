import numpy as np

from enum import Enum
from .binning import BinningExtender


class Pad_Values(Enum):
    ZERO = 0
    NEG_ONE = -1
    COPY = 2
    NEG_COPY = -2


class Histogram():
    def __init__(self, binning, values):
        self.__binning = binning
        self.__values = values

    def normalize(self, ord=np.inf):
        self.__values /= np.linalg.norm(self.__values.flatten(), ord=ord)

    def copy(self):
        bin_copy = self.binning.copy()
        val_copy = np.copy(self.values)
        return Histogram(bin_copy, val_copy)

    @property
    def values(self):
        return self.__values

    @property
    def binning(self):
        return self.__binning


class HistogramExtender():
    @staticmethod
    def __zero(values):
        return np.pad(values, 1,
                      mode='constant', constant_values=0.0)

    @staticmethod
    def __neg_one(values):
        return np.pad(
            values, 1, mode='constant', constant_values=-1.0)

    @staticmethod
    def __copy(values):
        return np.pad(values, 1, mode='edge')

    @staticmethod
    def __neg_copy(values):
        def pad_F(vector, pad_width, iaxis, kwargs):
            vector[:pad_width[0]] = -abs(vector[pad_width[0]])
            vector[-pad_width[1]:] = -abs(vector[-pad_width[1]-1])
            return vector
        return np.pad(values, 1, pad_F)

    @classmethod
    def extend(cls, histogram, pad_mode, pad_value):
        if (pad_value == Pad_Values.ZERO):
            extended_values = cls.__zero(histogram.values)
        elif (pad_value == Pad_Values.NEG_ONE):
            extended_values = cls.__neg_one(histogram.values)
        elif (pad_value == Pad_Values.COPY):
            extended_values = cls.__copy(histogram.values)
        elif (pad_value == Pad_Values.NEG_COPY):
            extended_values = cls.__neg_copy(histogram.values)
        else:
            raise Exception('Invalid pad_value.')

        extended_binning = BinningExtender.extend(histogram.binning,
                                                  pad_mode)
        return Histogram(extended_binning, extended_values)
