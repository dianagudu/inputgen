import numpy as np
import zlib
import pickle
import yaml

from enum import Enum

from scipy.interpolate import Rbf
from scipy.interpolate import LinearNDInterpolator

from .binning import BinningExtender
from .histogram import HistogramExtender

from .helper import to_dict

from .binning import Binning


class Interpolation_Modes(Enum):
    LINEAR = 1
    RBF_LINEAR = 2
    RBF_MULTIQUAD = 3


class ModelParams():
    def __init__(self, pad_mode, pad_value, interpolation_mode):
        self.__pad_mode = pad_mode
        self.__pad_value = pad_value
        self.__interpolation_mode = interpolation_mode

    @property
    def pad_mode(self):
        return self.__pad_mode

    @property
    def pad_value(self):
        return self.__pad_value

    @property
    def interpolation_mode(self):
        return self.__interpolation_mode

    def to_dict(self):
        props = ["pad_mode", "pad_value", "interpolation_mode"]
        return to_dict(self, props)

    @staticmethod
    def from_dict(d):
        return ModelParams(**d)


class Model():
    def __init__(self, binning, model_params, function, column_names):
        self.__binning = binning.copy()
        self.__model_params = model_params
        self.__function = function
        self.__column_names = column_names

    @staticmethod
    def from_file(filename):
        with open(filename, "r") as f:
            mobj = yaml.load(f)
        return Model.from_dict(mobj)

    def to_file(self, filename):
        with open(filename, "w") as f:
            yaml.dump(self.to_dict(), f)

    @staticmethod
    def from_dict(mobj):
        binning = Binning.from_dict(mobj["binning"])
        model_params = ModelParams.from_dict(mobj["model_params"])
        function = pickle.loads(zlib.decompress(mobj["function"]))
        column_names = mobj["column_names"]
        return Model(binning, model_params, function, column_names)

    @staticmethod
    def from_histogram(model_params, histogram, column_names=None):
        extended_histogram = histogram.copy()
        extended_histogram.normalize()
        extended_histogram = HistogramExtender.extend(
            extended_histogram,
            model_params.pad_mode,
            model_params.pad_value)

        extended_binning = extended_histogram.binning
        extended_values = extended_histogram.values

        interpolation_mode = model_params.interpolation_mode
        if (interpolation_mode == Interpolation_Modes.LINEAR):
            function = LinearNDInterpolator(
                np.stack([x.flatten() for x in extended_binning.meshgrids],
                         axis=-1), extended_values.flatten())
        elif (interpolation_mode == Interpolation_Modes.RBF_LINEAR):
            function = Rbf(*extended_binning.meshgrids,
                                  extended_values.flatten(), smooth=0.0,
                                  function="linear")
        elif (interpolation_mode == Interpolation_Modes.RBF_MULTIQUAD):
            function = Rbf(*extended_binning.meshgrids,
                                  extended_values.flatten(), smooth=0.0,
                                  function="multiquadric")
        else:
            raise Exception("Invalid interpolation_mode.")

        if not column_names:
            column_names = ["Resource%s" % i
                            for i in range(histogram.binning.dimensions)]

        return Model(histogram.binning, model_params, function, column_names)


    def to_dict(self):
        mobj = {
            "binning": self.binning.to_dict(),
            "column_names": self.column_names,
            "model_params": self.model_params.to_dict(),
            "function": zlib.compress(pickle.dumps(self.__function))
        }
        return mobj

    @property
    def binning(self):
        return self.__binning

    @property
    def F(self):
        return self.__function

    @property
    def model_params(self):
        return self.__model_params

    @property
    def column_names(self):
        return self.__column_names
