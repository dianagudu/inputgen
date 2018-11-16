import numpy as np

class KPIs():
    def __init__(self, hist1, hist2):
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

        ab_quality = sum([get_quality(r, delta) * vol
                            for r, delta, vol
                                in zip(self.__h1f,
                                    self.__diff,
                                    self.__h2.binning.volumes.flatten())]) / \
                                        self.__h2.binning.total_volume

        nebi = self.__h1f > 0
        ebi = self.__h1f == 0

        neb_quality = sum([get_quality(r, delta) * vol
                            for r, delta, vol
                                in zip(self.__h1f[nebi],
                                    self.__diff[nebi],
                                    self.__h2.binning.volumes.flatten()[nebi])]) / \
                                        self.__h2.binning.volumes.flatten()[nebi].sum()

        if not any(ebi):
            eb_quality = 2.0
        else:
            eb_quality = sum([get_quality(r, delta) * vol
                                for r, delta, vol
                                    in zip(self.__h1f[ebi],
                                        self.__diff[ebi],
                                        self.__h2.binning.volumes.flatten()[ebi])]) / \
                                            self.__h2.binning.volumes.flatten()[ebi].sum()

        return (ab_quality, neb_quality, eb_quality)


