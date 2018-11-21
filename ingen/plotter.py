import numpy as np
import pylab as plt
from matplotlib import cm
from matplotlib.colors import LogNorm


class HairyPlotter():

    @staticmethod
    def plot_histogram(histogram, cmap=cm.Blues, norm=LogNorm,      # pylint: disable=E1101
                       column_names=None, title=None):
        HairyPlotter.__plot(histogram.binning, histogram.values,
                            cmap, norm, column_names, title)

    @staticmethod
    def plot_model(model, binning,
                   cmap=cm.Blues, norm=LogNorm,      # pylint: disable=E1101
                   column_names=None, title=None):
        values = model.F(*binning.meshgrids)
        HairyPlotter.__plot(binning, values,
                            cmap, norm,
                            column_names=model.column_names, title=title)

    @staticmethod
    def __plot(binning, values,
                cmap=cm.Blues, norm=LogNorm,                        # noqa pylint: disable=E1101
                column_names=None, title=None):
        if not column_names:
            column_names = ["Resource%s" % i
                            for i in range(binning.dimensions)]

        projections = [(x, y)
                       for y in range(binning.dimensions)
                       for x in range(binning.dimensions)
                       if x < y]

        plt.figure(figsize=(
            len(projections) * 4 + (len(projections) - 1) * 0.75,
            4.5))

        for i, p in enumerate(projections):
            ax1, ax2 = p
            plt.subplot(1, len(projections), i + 1)

            mg = np.meshgrid(binning.edges[ax1],
                             binning.edges[ax2],
                             indexing='ij')
            mx = tuple([x for x in range(binning.dimensions)
                        if x not in (ax1, ax2)])
            projected_values = np.sum(values, axis=mx)

            plt.pcolor(*mg, projected_values, cmap=cmap, norm=norm())
            plt.xlim((0, binning.edges[ax1].max()))
            plt.ylim((0, binning.edges[ax2].max()))
            plt.xlabel(column_names[ax1])
            plt.ylabel(column_names[ax2])
            # plt.gca().set_aspect('equal')
            plt.tight_layout()
            plt.subplots_adjust(top=0.85)

        if title:
            plt.suptitle(title)
