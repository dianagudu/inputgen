from enum import Enum
import numpy as np


class Binning_Types(Enum):
    REGULAR = 1
    IRREGULAR = 2
    CLUSTERED = 3


class Binning():
    def __init__(self, bin_type, bin_edges):
        self.__type = bin_type
        self.__bin_edges = bin_edges
        self.__bin_counts = [
            len(x) - 1 for x in bin_edges
        ]

    @property
    def bin_counts(self):
        return self.__bin_counts

    @property
    def bin_edges(self):
        return self.__bin_edges


class RegularBinning(Binning):
    def __init__(self, bin_counts, src):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        bin_edges = self.__regularBinEdgeGenerator(bin_counts, src.domain)
        super().__init__(bin_type=Binning_Types.REGULAR,
                         bin_edges=bin_edges)

    def __regularBinEdgeGenerator(self, bin_amounts, domain):
        return [np.linspace(0.0, d, n + 1)
                for n, d in zip(bin_amounts, domain)]


class IrregularBinning(Binning):
    pass


class ClusteredBinning(Binning):
    pass
