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

from .bundles import BundleGenerator

output = sys.argv[1]
filenames = sys.argv[2:]
#source = GoogleDatasetProcessor(name="Pedro",
#                       output_filename=output,
#                       source_filenames=filenames).process()

source = DataReader(filename=output).read()

bing = RegularBinning(8, source.domain)
print(bing.edges)
print(bing.distances)
print(bing.total_volume)

model_params = ModelParams(Pad_Modes.MIRROR, Pad_Values.NEG_COPY,
                           Interpolation_Modes.LINEAR)

histogram = source.get_histogram(bing)

model = Model.from_histogram(model_params, histogram)

model.to_file("/tmp/a")
model2 = Model.from_file("/tmp/a")

bg = BundleGenerator(model, RegularBinning(8, source.domain))
fundle = bg.generate_uniform(2)
bundle = bg.generate(1)
print()


#bing = IrregularBinning(8, source.domain, spread=0.3)
#print(bing.edges)
#print("Random seed =", bing.random_seed)

#bing = ClusteredBinning(8, source)
#print(bing.edges)
#print("Random seed =", bing.random_seed)