from enum import Enum
import numpy as np
from time import time
from sklearn.cluster import KMeans
from .helper import centering


class Binning_Types(Enum):
    REGULAR = 1
    IRREGULAR = 2
    CLUSTERED = 3


class Binning():
    def __init__(self, bin_type, bin_edges, random_seed=0):
        self.__type = bin_type
        self.__bin_edges = bin_edges
        self.__bin_counts = [
            len(x) - 1 for x in bin_edges
        ]
        self.__random_seed = random_seed

    @property
    def bin_counts(self):
        return self.__bin_counts

    @property
    def bin_edges(self):
        return self.__bin_edges

    @property
    def random_seed(self):
        return self.__random_seed


class RegularBinning(Binning):
    def __init__(self, bin_counts, src):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        bin_edges = self.__regularBinEdgeGenerator(bin_counts, src.domain)
        super().__init__(bin_type=Binning_Types.REGULAR,
                         bin_edges=bin_edges)

    def __regularBinEdgeGenerator(self, bin_counts, domain):
        return [np.linspace(0.0, d, n + 1)
                for n, d in zip(bin_counts, domain)]


class IrregularBinning(Binning):
    def __init__(self, bin_counts, src, spread=0.3):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        random_seed = int(time())
        np.random.seed(random_seed)
        bin_edges = self.__irregularBinEdgeGenerator(
            bin_counts, src.domain, spread)
        super().__init__(bin_type=Binning_Types.IRREGULAR,
                         bin_edges=bin_edges,
                         random_seed=random_seed)

    def __irregularBinEdgeGenerator(self, bin_counts, domain, spread):
        def single_dim(count, domain):
            dst = np.random.randint(1, int(count * (1. + spread)), size=count)
            dst = dst / dst.sum()
            dst *= domain

            bins = []
            ws = 0
            for w in dst:
                ws += w
                bins.append(ws)

            bins = [0.0] + bins
            bins[-1] = domain
            return np.array(bins)

        return [single_dim(c, d) for c, d in zip(bin_counts, domain)]


class ClusteredBinning(Binning):
    def __init__(self, bin_counts, src):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        random_seed = int(time())
        bin_edges = self.__clusteredBinEdgeGenerator(bin_counts, src.domain,
                                                     src.data, random_seed)
        super().__init__(bin_type=Binning_Types.CLUSTERED,
                         bin_edges=bin_edges,
                         random_seed=random_seed)

    def __clusteredBinEdgeGenerator(self, bin_counts, domain, data,
                                    random_seed):
        def single_dim(count, domain, data1D):
            kmeans = KMeans(n_clusters=count, init='k-means++',
                            random_state=random_seed)
            kmeans = kmeans.fit(data1D.reshape((data1D.shape[0], 1)))
            centers = np.unique(kmeans.cluster_centers_.reshape((count,)))
            return np.concatenate(([0], centering(centers), [domain]),
                                  axis=None)

        return [single_dim(c, d, col)
                for c, d, col in zip(bin_counts, domain, data.T)]
