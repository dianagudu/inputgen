import numpy as np

from enum import Enum
from time import time
from sklearn.cluster import KMeans
from .helper import centering
from .helper import to_dict


class Binning_Types(Enum):
    REGULAR = 1
    IRREGULAR = 2
    CLUSTERED = 3


class Pad_Modes(Enum):
    EPSILON = 1
    MIRROR = 2


class Binning():
    def __init__(self, type, bin_edges, random_seed=0):
        self.__type = type
        self.__bin_edges = list(np.copy(bin_edges))
        self.__bin_counts = [
            len(x) - 1 for x in bin_edges
        ]
        self.__random_seed = random_seed
        self.__bin_distances = [edges_along_dim[1:] - edges_along_dim[:-1]
                                for edges_along_dim in bin_edges]
        self.__bin_centers = list(map(centering, bin_edges))
        self.__total_volume = np.prod([edges_along_dim[-1] - edges_along_dim[0]
                                       for edges_along_dim in bin_edges])

        mg_dists = np.meshgrid(*self.__bin_distances, indexing='ij')
        self.__bin_volumes = mg_dists[0]
        for mgd in mg_dists[1:]:
            self.__bin_volumes = np.multiply(self.__bin_volumes, mgd)

        self.__meshgrids = np.meshgrid(*self.__bin_centers, indexing='ij')

    def copy(self):
        return Binning(self.type, self.bin_edges, self.random_seed)

    @property
    def type(self):
        return self.__type

    @property
    def bin_counts(self):
        return self.__bin_counts

    @property
    def bin_edges(self):
        return self.__bin_edges

    @property
    def random_seed(self):
        return self.__random_seed

    @property
    def bin_distances(self):
        return self.__bin_distances

    @property
    def bin_centers(self):
        return self.__bin_centers

    @property
    def total_volume(self):
        return self.__total_volume

    @property
    def bin_volumes(self):
        return self.__bin_volumes

    @property
    def meshgrids(self):
        return self.__meshgrids

    def to_dict(self):
        return to_dict(self, [
            "type",
            ("bin_edges", lambda x: [y.tolist() for y in x]),
            "random_seed"
        ])

    @staticmethod
    def from_dict(d):
        d["bin_edges"] = [np.array(y) for y in d["bin_edges"]]
        return Binning(**d)


class RegularBinning(Binning):
    def __init__(self, bin_counts, src):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        bin_edges = self.__regularBinEdgeGenerator(bin_counts, src.domain)
        super().__init__(type=Binning_Types.REGULAR,
                         bin_edges=bin_edges)

    def __regularBinEdgeGenerator(self, bin_counts, domain):
        return [np.linspace(0.0, d, n + 1)
                for n, d in zip(bin_counts, domain)]


class IrregularBinning(Binning):
    def __init__(self, bin_counts, src, spread=0.3):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        random_seed = int(time())
        bin_edges = self.__irregularBinEdgeGenerator(
            bin_counts, src.domain, spread, random_seed)
        super().__init__(type=Binning_Types.IRREGULAR,
                         bin_edges=bin_edges,
                         random_seed=random_seed)

    def __irregularBinEdgeGenerator(self, bin_counts, domain, spread,
                                    random_seed):
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

        np.random.seed(random_seed)
        return [single_dim(c, d) for c, d in zip(bin_counts, domain)]


class ClusteredBinning(Binning):
    def __init__(self, bin_counts, src):
        if isinstance(bin_counts, int):
            bin_counts = [bin_counts] * len(src.domain)

        random_seed = int(time())
        bin_edges = self.__clusteredBinEdgeGenerator(bin_counts, src.domain,
                                                     src.data, random_seed)
        super().__init__(type=Binning_Types.CLUSTERED,
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


class BinningExtender():
    @staticmethod
    def mirror(binning):
        extended_bin_edges = [np.concatenate((
                [edges_along_dim[0] + edges_along_dim[0] - edges_along_dim[1]],
                edges_along_dim,
                [edges_along_dim[-1] + edges_along_dim[-1] - edges_along_dim[-2]]
            )) for edges_along_dim in binning.bin_edges]
        return Binning(binning.type, extended_bin_edges,
                       binning.random_seed)

    @staticmethod
    def epsilon(binning):
        # Calculate avg. bin size along all dimensions
        epsilons = [np.mean(dists) for dists in binning.bin_distances]
        extended_bin_edges = [np.concatenate((
            [edges_along_dim[0] - epsilon],
            edges_along_dim,
            [edges_along_dim[-1] + epsilon]
        )) for epsilon, edges_along_dim in zip(epsilons, binning.bin_edges)]
        return Binning(binning.type, extended_bin_edges,
                       binning.random_seed)

    @classmethod
    def extend(cls, binning, pad_mode):
        if pad_mode == Pad_Modes.EPSILON:
            return cls.epsilon(binning)
        elif pad_mode == Pad_Modes.MIRROR:
            return cls.mirror(binning)
        else:
            raise Exception("Invalid pad_mode.")