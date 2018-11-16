import numpy as np

class KPIs():
    def __init__(self, hist1, hist2):
        """hist1 is the histogram of the data the model is derived from,
           hist2 is the histogram of the newly generated data.
           Note: both must be using the same binning!"""
        self.__h1 = hist1           # Model Source, realH
        self.__h2 = hist2           # ndH, generated

        self.__h1f = hist1.values.flatten()
        self.__h2f = hist2.values.flatten()

        self.__diff = (self.__h2f - self.__h1f)

    def error(self):
        # bins with too many generated packages
        return sum(self.__diff[self.__diff > 0]) / sum(self.__h2f)

    def quality(self):
        def get_quality(r, delta):
            if (r == 0 and delta == 0):
                return 1
            if (r == 0 or abs(delta) > r):
                return 0
            return 1 - abs(delta) / r

        def quality(index):
            if not any(index):
                return 2.0
            else:
                bin_vols = self.__h2.binning.volumes.flatten()
                pairs = zip(self.__h1f[index],
                            self.__diff[index],
                            bin_vols[index])
                return sum([get_quality(r, delta) * vol
                            for r, delta, vol in pairs]) / bin_vols[index].sum()

        abi = [True] * self.__h1f.size
        nebi = self.__h1f > 0
        ebi = self.__h1f == 0

        return (quality(abi), quality(nebi), quality(ebi))

