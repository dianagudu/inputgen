import numpy as np
import datetime

from time import time

from .binning import Binning
from .binning import Binning_Types
from .helper import objectview
from .preprocessors import DataSource


class BundleGenerator():
    def __init__(self, model, binning):
        self.__model = model
        self.__binning = binning.copy()
        self.__last_seed = None
        self.__compute_probability_matrix()
        pass

    def recommended_amount(self, real_histogram):
        """real_histogram: the histogram of the model's source data
                           binned with the new binning."""
        min_prob = self.probabilities[
            (self.probabilities[:, -1] > 0) *
            (real_histogram.values.flatten() > 0),
            -1].min()

        if min_prob > 0:
            return int(1/min_prob)
        else:
            return 0

    def expected_best_quality(self, amount, real_histogram):
        """real_histogram: the histogram of the model's source data
                           binned with the new binning."""
        index = np.array([p * amount > 1 or
                          real_histogram.values.flatten()[i] == 0
                          for i, p in enumerate(self.probabilities[:, -1])])
        return self.binning.volumes.flatten()[index].sum() / \
                    self.binning.total_volume

    def __compute_probability_matrix(self):
        all_edges = [
            np.unique(np.concatenate((gbe, mbe)))
            for gbe, mbe in zip(self.binning.edges,
                                self.model.binning.edges)
        ]

        # Create sub_edges for each bin and along each dimension.
        sub_edges = []
        for edges, coarse in zip(all_edges, self.binning.edges):
            sub_edges.append(
                [edges[(edges >= left) * (edges <= right)]
                    for left, right in zip(coarse[:-1], coarse[1:])]
            )

        # sub_edges is an n-dim list of lists of arrays:
        #   sub_edges[dim][bin_index] contains the sub edges along dimension
        #   dim for bin with index bin_index along that dimension.

        # Create a 1d list of all bin indices (along all dimensions)
        bin_indices = [range(0, i) for i in self.binning.counts]
        bin_indices = np.meshgrid(*bin_indices, indexing='ij')
        bin_indices = list(zip(*[mg.flatten() for mg in bin_indices]))
        # here bin_indices equals [ (x0, y0, z0), (x0, y0, z1), (x0, y1, z0) ... ]

        # Probabilities is a matrix with one row per bin with the format:
        #   c_x, c_y, c_z, ... , probability
        # for each bin/row, where c_i indicates the center of the bin.
        probabilities = np.zeros((len(bin_indices),
                                  self.binning.dimensions + 1))
        for i, bin_index in enumerate(bin_indices):
            # Find center of current bin
            probabilities[i, :-1] = [cpd[idx] for idx, cpd in
                                     zip(bin_index, self.binning.centers)]

            # Create sub-binning to calculate probability of bin
            sub_binning = Binning(Binning_Types.SUBBINNING,
                                  [sub_edges[dim][idx] for dim, idx in enumerate(bin_index)])

            factors = sub_binning.volumes / sub_binning.total_volume
            alltF = self.model.F(*sub_binning.meshgrids).flatten()
            alltF = [x if x > 0.0 else 0.0 for x in alltF]
            alltF = alltF * factors.flatten()
            probabilities[i, -1] = sum(alltF)

        probabilities[:, -1] /= np.linalg.norm(probabilities[:, -1], ord=1)
        self.__probabilities = probabilities

    def generate(self, amount, name="", random_seed=None):
        def pick(p, n):
            # picks n coordinates from the probability matrix p
            return np.stack([p[x, :-1] for x in
                             np.random.choice(range(p.shape[0]), p=p[:, -1], size=n)])
        return self.__generate(amount, random_seed, pick, name)

    def generate_uniform(self, amount, name="", random_seed=None):
        def uniform_pick(p, n):
            # picks n coordinates from the probability matrix p
            return np.stack([p[x, :-1] for x in
                             np.random.randint(p.shape[0], size=n)])
        return self.__generate(amount, random_seed, uniform_pick, name)

    def __generate(self, amount, random_seed, picker, name):
        # generate bundles
        if not random_seed:
            random_seed = np.random.randint(2**32-1)
        np.random.seed(random_seed)
        self.__last_seed = random_seed

        mobj = {
            "name": name,
            "type": "Generated",
            "creation_date": datetime.datetime.now().isoformat(),
            "random_seed": self.__last_seed
        }

        ret = DataSource(
            info=objectview(mobj),
            domain=[max(b) for b in self.binning.edges],
            column_names=self.model.column_names,
            data=picker(self.probabilities, amount)
        )
        return ret

    @property
    def model(self):
        return self.__model

    @property
    def binning(self):
        return self.__binning

    @property
    def probabilities(self):
        return self.__probabilities

    @property
    def last_seed(self):
        return self.__last_seed
