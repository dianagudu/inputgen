import sys

from .preprocessors import GoogleDatasetProcessor
from .preprocessors import DataReader
from .binning import RegularBinning


# from .model import Model

#source = DataReader(filename).read()

#binning = Binning(type="clustered", bin_amouts = [8,3,5], source)

#model = Model(input_data, bin_edges)
#model.generate()


###


output = sys.argv[1]
filenames = sys.argv[2:]
source = GoogleDatasetProcessor(name="Pedro",
                       output_filename=output,
                       source_filenames=filenames).process()

bing = RegularBinning(8, source)
print(bing.bin_edges)

source = DataReader(filename=output).read()
bing = RegularBinning(8, source)
print(bing.bin_edges)