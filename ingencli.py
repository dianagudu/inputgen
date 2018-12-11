#!/usr/bin/env python3
import click
import yaml

from ingen.preprocessors import GoogleDatasetProcessor
from ingen.preprocessors import BitbrainsDatasetProcessor
from ingen.preprocessors import UniformDatasetProcessor
from ingen.preprocessors import HotspotsDatasetProcessor
from ingen.preprocessors import DataReader

from ingen.binning import Binning_Types
from ingen.binning import BinningGenerator


def validate_binning_domain(ctx, param, value):
    # domain = None --> return None
    # domain != None --> validate domain: list of floats>0

    if value is None:
        return None

    def positive_float(f):
        if float(f) <= 0:
            raise ValueError(None)
        else:
            return float(f)

    try:
        return [positive_float(x) for x in value.split(",")]
    except ValueError:
        raise click.BadParameter('%s should be a comma-separated list of floats > 0, not \'%s\'' % (param.name, value))


def validate_binning_amount(ctx, param, value):
    def positive_int(i):
        if int(i) <= 0:
            raise ValueError(None)
        else:
            return int(i)

    try:
        if value is None:
            raise ValueError(None)
        if "," in value:
            return [positive_int(x) for x in value.split(",")]
        else:
            return positive_int(value)
    except ValueError:
        raise click.BadParameter('%s should be either an int > 0 or a comma-separated list of ints > 0, not \'%s\'' % (param.name, value))


@click.group()
def cli():
    pass


@cli.group(short_help='subcommand to create things', name='create')
def generate():
    pass


@cli.command(short_help='subcommand to calculate different KPIs',
             name='compare')
def compare():
    click.echo('Not implemented')
    pass


@cli.group(short_help='subcommand to visualize things', name='plot')
def plot():
    click.echo('Not implemented')
    pass


@generate.group(short_help='create datasource', name='datasource')
def g_datasource():
    pass


@generate.command(short_help='generate binning', name='binning')
@click.option("--datasource", type=click.Path(), help='path to datasource')
@click.option("--domain", callback=validate_binning_domain,
              help='upper limits for dataset domain (float or list of floats)')
@click.option("--spread", type=float,
              help='spread for irregular binning generation')
@click.argument("type", type=click.Choice(
                [name.lower() for name, value in Binning_Types.__members__.items()
                 if value.value < 90]
                ))
@click.argument("amount", callback=validate_binning_amount)
@click.argument("output", type=click.Path())
def g_binning(datasource, domain, type, amount, output, spread):
   """Generates a binning of a given type, with AMOUNT bins in each dimension.
   AMOUNT can be an integer or a comma-separated list of integers, representing
   the number of bins per dimension.

   The binning is written to "OUTPUT.yaml".
   """
   # datasource = None and domain == None --> Error
   # datasource = None and domain != None --> OK
   # datasource != None and domain = None --> derive domain from datasource
   # datasource != None and domain != None --> dim. should match, use domain
   source = None
   if domain is None and datasource is None:
      raise click.UsageError("Either a datasource or a domain is required.")
   elif not datasource is None:
      source = DataReader(datasource).read()
      if not domain is None:
         if len(source.domain) != len(domain):
               raise click.BadOptionUsage("domain",
                                          "Dimension mismatch for source domain (%d) and given domain (%d)."
                                          % (len(source.domain), len(domain)))
      else:
         domain = source.domain

   # convert type to enum
   type = Binning_Types[type.upper()]

   # if type is clustered, datasource is required
   if type == Binning_Types.CLUSTERED and datasource is None:
      raise click.UsageError("Datasource is required for clustered binning.")

   # if spread is not given
   if spread is None:
      binning = BinningGenerator.generate(type, amount, domain, source)
   else:
      binning = BinningGenerator.generate(type, amount, domain, source, spread)

   with open(output + ".yaml", "w") as f:
      yaml.dump(binning.to_dict(), f)
      click.echo("Saved binning to %s.yaml" % output)


@generate.command(short_help='derive model', name='model')
def g_model():
    click.echo('Not implemented')
    pass


@generate.command(short_help='generate bundles', name='bundles')
def g_bundles():
    click.echo('Not implemented')
    pass


class G_DATASOURCE():

    @staticmethod
    @g_datasource.command(short_help='generate a dataset derived from the Google cloud traces')
    @click.option("--name", default="", help="Logical name of the dataset.")
    @click.argument("output", type=click.Path())
    @click.argument("input", type=click.Path(), nargs=-1, required=True)
    def google(name, output, input):
        """Generates a dataset that is derived from the Google Cluster Data workload
           traces[1] (ClusterData2011_2) found in the INPUT files
           (note: multiple input files can be given).

           The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".

           [1] https://github.com/google/cluster-data
        """
        GoogleDatasetProcessor(name=name,
                               output_filename=output,
                               source_filenames=input).process()

    @staticmethod
    @g_datasource.command(short_help='generate a dataset derived from the Bitbrains log format')
    @click.option("--name", default="", help="Logical name of the dataset.")
    @click.argument("output", type=click.Path())
    @click.argument("input", type=click.Path())
    def bitbrains(name, output, input):
        """Generates a dataset that is derived from the BitBrains fastStorage trace
           data[1] found in folder INPUT.

           The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".

           [1] http://gwa.ewi.tudelft.nl/datasets/gwa-t-12-bitbrains
        """
        BitbrainsDatasetProcessor(name=name,
                                  output_filename=output,
                                  source_folder=input).process()

    @staticmethod
    @g_datasource.command(short_help='generate a uniform dataset')
    @click.option("--name", default="", help="Logical name of the dataset.")
    @click.argument("output", type=click.Path())
    @click.argument("dimensions", type=int)
    def uniform(name, output, dimensions):
        """Generates a DIMENSIONS-dimensional dataset consisting of uniformly
           distributed datapoints.

           The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".
        """
        UniformDatasetProcessor(name=name,
                                output_filename=output,
                                dimensions=dimensions).process()

    @staticmethod
    @g_datasource.command(short_help='generate a dataset based on hotspots')
    @click.option("--name", default="", help="Logical name of the dataset.")
    @click.argument("output", type=click.Path())
    @click.argument("dimensions", type=int)
    @click.argument("hotspots", type=int)
    def hotspots(name, output, dimensions, hotspots):
        """Generates a DIMENSIONS-dimensional dataset consisting
           of HOTSPOTS amount of hotspots.

           The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".
        """
        HotspotsDatasetProcessor(name=name,
                                 output_filename=output,
                                 dimensions=dimensions,
                                 hotspot_count=hotspots).process()


if __name__ == '__main__':
    cli()
