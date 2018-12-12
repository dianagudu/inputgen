import sys
import pylab as plt

from matplotlib import cm

from .preprocessors import GoogleDatasetProcessor
from .preprocessors import BitbrainsDatasetProcessor
from .preprocessors import UniformDatasetProcessor
from .preprocessors import HotspotsDatasetProcessor
from .preprocessors import DataSourceIO
from .binning import RegularBinning
from .binning import IrregularBinning
from .binning import ClusteredBinning
from .binning import G2ProgressionBinning
from .binning import Pad_Modes
from .model import ModelParams
from .model import Model
from .histogram import Pad_Values
from .model import Interpolation_Modes
from .histogram import Histogram
from .kpis import KPIs
from .bundles import BundleGenerator
from .plotter import HairyPlotter

output = sys.argv[1]
filenames = sys.argv[2:]
# source = GoogleDatasetProcessor(name="Pedro",
#                       output_filename=output,
#                       source_filenames=filenames).process()


# folder = "cloud_traces/bitbrains/fastStorage/2013-8/"
# folder = sys.argv[2]
# source2 = BitbrainsDatasetProcessor(name="Brainss",
#                                     output_filename=output,
#                                     source_folder=folder).process()

# source3 = UniformDatasetProcessor(name="uni",
#                                   output_filename=output,
#                                   dimensions=3).process()

# source4 = HotspotsDatasetProcessor(name="hot",
#                                    output_filename=output,
#                                    dimensions=3,
#                                    hotspot_count=16).process()


source = DataSourceIO.read(output)

gebing = G2ProgressionBinning(8, source.domain)


bing = RegularBinning(8, source.domain)
model_params = ModelParams(Pad_Modes.MIRROR, Pad_Values.ZERO,
                           Interpolation_Modes.LINEAR)
histogram = source.get_histogram(bing)
model = Model.from_histogram(model_params, histogram,
                             column_names=source.column_names)
model.to_file("/tmp/a")
model2 = Model.from_file("/tmp/a")

#gebing = RegularBinning(8, source.domain)

bg = BundleGenerator(model, gebing)
fundle = bg.generate_uniform(2)
bundle = bg.generate(1000)

source_hist_new_bin = source.get_histogram(gebing)
gen_hist_new_bin = bundle.get_histogram(gebing)

rca = bg.recommended_amount(source_hist_new_bin)
ebq = bg.expected_best_quality(1000, source_hist_new_bin)

print(rca, ebq)

kpis = KPIs(source_hist_new_bin, gen_hist_new_bin)

print(kpis.error(), kpis.quality())
print()

HairyPlotter.plot_histogram(
    source_hist_new_bin, column_names=source.column_names)

HairyPlotter.plot_histogram(
    gen_hist_new_bin, cmap=cm.Greens,               # noqa pylint: disable=E1101
    title="Generated Data")

HairyPlotter.plot_model(model, gen_hist_new_bin.binning,
        cmap=cm.Oranges,                            # noqa pylint: disable=E1101
        title="Model function")

plt.show()

# bing = IrregularBinning(8, source.domain, spread=0.3)
# print(bing.edges)
# print("Random seed =", bing.random_seed)

# bing = ClusteredBinning(8, source)
# print(bing.edges)
# print("Random seed =", bing.random_seed)
