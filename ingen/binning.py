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
    G2PROGRESSION = 4
    SUBBINNING = 99


class Pad_Modes(Enum):
    EPSILON = 1
    MIRROR = 2


class Binning():

    def __init__(self, type, edges, random_seed=0):
        self.__type = type
        self.__edges = list(np.copy(edges))
        self.__counts = [len(x) - 1 for x in edges]
        self.__domain = [x.max() for x in self.edges]
        self.__random_seed = random_seed
        self.__distances = [edges_along_dim[1:] - edges_along_dim[:-1]
                            for edges_along_dim in edges]
        self.__centers = list(map(centering, edges))
        self.__total_volume = np.prod([edges_along_dim[-1] - edges_along_dim[0]
                                       for edges_along_dim in edges])

        mg_dists = np.meshgrid(*self.__distances, indexing='ij')
        self.__volumes = mg_dists[0]
        for mgd in mg_dists[1:]:
            self.__volumes = np.multiply(self.__volumes, mgd)

        self.__meshgrids = np.meshgrid(*self.__centers, indexing='ij')

    def copy(self):
        return Binning(self.type, self.edges, self.random_seed)

    @property
    def type(self):
        return self.__type

    @property
    def counts(self):
        return self.__counts

    @property
    def edges(self):
        return self.__edges

    @property
    def random_seed(self):
        return self.__random_seed

    @property
    def distances(self):
        return self.__distances

    @property
    def centers(self):
        return self.__centers

    @property
    def total_volume(self):
        return self.__total_volume

    @property
    def volumes(self):
        return self.__volumes

    @property
    def meshgrids(self):
        return self.__meshgrids

    @property
    def dimensions(self):
        return len(self.edges)

    @property
    def domain(self):
        return self.__domain

    def to_dict(self):
        return to_dict(self, [
            "type",
            ("edges", lambda x: [y.tolist() for y in x]),
            "random_seed"
        ])

    @staticmethod
    def from_dict(d):
        d["edges"] = [np.array(y) for y in d["edges"]]
        return Binning(**d)


class RegularBinning(Binning):

    def __init__(self, counts, domain):
        if isinstance(counts, int):
            counts = [counts] * len(domain)

        edges = self.__regularBinEdgeGenerator(counts, domain)
        super().__init__(type=Binning_Types.REGULAR,
                         edges=edges)

    def __regularBinEdgeGenerator(self, counts, domain):
        return [np.linspace(0.0, d, n + 1)
                for n, d in zip(counts, domain)]


class IrregularBinning(Binning):

    def __init__(self, counts, domain, spread=0.3):
        if isinstance(counts, int):
            counts = [counts] * len(domain)

        random_seed = int(time())
        edges = self.__irregularBinEdgeGenerator(
            counts, domain, spread, random_seed)
        super().__init__(type=Binning_Types.IRREGULAR,
                         edges=edges,
                         random_seed=random_seed)

    def __irregularBinEdgeGenerator(self, counts, domain, spread,
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
        return [single_dim(c, d) for c, d in zip(counts, domain)]


class ClusteredBinning(Binning):

    def __init__(self, counts, src):
        if isinstance(counts, int):
            counts = [counts] * len(src.domain)

        random_seed = int(time())
        edges = self.__clusteredBinEdgeGenerator(counts, src.domain,
                                                 src.data, random_seed)
        super().__init__(type=Binning_Types.CLUSTERED,
                         edges=edges,
                         random_seed=random_seed)

    def __clusteredBinEdgeGenerator(self, counts, domain, data,
                                    random_seed):
        def single_dim(count, domain, data1D):
            kmeans = KMeans(n_clusters=count, init='k-means++',
                            random_state=random_seed)
            kmeans = kmeans.fit(data1D.reshape((data1D.shape[0], 1)))
            centers = np.unique(kmeans.cluster_centers_.reshape((count,)))
            return np.concatenate(([0], centering(centers), [domain]),
                                  axis=None)

        return [single_dim(c, d, col)
                for c, d, col in zip(counts, domain, data.T)]


class G2ProgressionBinning(Binning):

    def __init__(self, counts, domain):
        if isinstance(counts, int):
            counts = [counts] * len(domain)

        edges = self.__g2progressionBinEdgeGenerator(counts, domain)
        super().__init__(type=Binning_Types.G2PROGRESSION,
                         edges=edges)

    def __g2progressionBinEdgeGenerator(self, counts, domain):
        return [d / np.logspace(0.0, n, n + 1, base=2)[::-1]
                for n, d in zip(counts, domain)]


class BinningExtender():

    @staticmethod
    def mirror(binning):
        extended_bin_edges = [np.concatenate((
            [edges_along_dim[0] + edges_along_dim[0] - edges_along_dim[1]],
            edges_along_dim,
            [edges_along_dim[-1] +
             edges_along_dim[-1] - edges_along_dim[-2]]
        )) for edges_along_dim in binning.edges]
        return Binning(binning.type, extended_bin_edges,
                       binning.random_seed)

    @staticmethod
    def epsilon(binning):
        # Calculate avg. bin size along all dimensions
        epsilons = [np.mean(dists) for dists in binning.distances]
        extended_bin_edges = [np.concatenate((
            [edges_along_dim[0] - epsilon],
            edges_along_dim,
            [edges_along_dim[-1] + epsilon]
        )) for epsilon, edges_along_dim in zip(epsilons, binning.edges)]
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
