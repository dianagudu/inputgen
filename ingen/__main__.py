import sys

from .preprocessors import GoogleDatasetProcessor
from .preprocessors import DataReader
from .binning import RegularBinning
from .binning import IrregularBinning
from .binning import ClusteredBinning


# from .model import Model

#source = DataReader(filename).read()

#binning = Binning(type="clustered", bin_amouts = [8,3,5], source)

#model = Model(input_data, bin_edges)
#model.generate()


output = sys.argv[1]
filenames = sys.argv[2:]
#source = GoogleDatasetProcessor(name="Pedro",
#                       output_filename=output,
#                       source_filenames=filenames).process()

source = DataReader(filename=output).read()

#bing = RegularBinning(8, source)
#print(bing.bin_edges)

#bing = IrregularBinning(8, source, spread=0.3)
#print(bing.bin_edges)
#print("Random seed =", bing.random_seed)

bing = ClusteredBinning(8, source)
print(bing.bin_edges)
print("Random seed =", bing.random_seed)