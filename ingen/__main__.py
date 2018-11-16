import sys

from .preprocessors import GoogleDatasetProcessor
from .preprocessors import DataReader
from .binning import RegularBinning
from .binning import IrregularBinning
from .binning import ClusteredBinning
from .binning import Pad_Modes
from .model import ModelParams
from .model import Model
from .histogram import Pad_Values
from .model import Interpolation_Modes
from .histogram import Histogram
from .kpis import KPIs
from .bundles import BundleGenerator

output = sys.argv[1]
filenames = sys.argv[2:]
# source = GoogleDatasetProcessor(name="Pedro",
#                       output_filename=output,
#                       source_filenames=filenames).process()

source = DataReader(filename=output).read()

bing = RegularBinning(8, source.domain)
model_params = ModelParams(Pad_Modes.MIRROR, Pad_Values.NEG_COPY,
                           Interpolation_Modes.LINEAR)
histogram = source.get_histogram(bing)
model = Model.from_histogram(model_params, histogram,
                             column_names=source.column_names)
model.to_file("/tmp/a")
model2 = Model.from_file("/tmp/a")

gebing = RegularBinning(8, source.domain)

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


# TODO: Bundle amount recommendation to BundleGenerator.
# Error/Quality stuff
# Some plotting.

#bing = IrregularBinning(8, source.domain, spread=0.3)
# print(bing.edges)
#print("Random seed =", bing.random_seed)

#bing = ClusteredBinning(8, source)
# print(bing.edges)
#print("Random seed =", bing.random_seed)
