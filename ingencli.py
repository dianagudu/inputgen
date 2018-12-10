#!/usr/bin/env python3
import click

from ingen.preprocessors import GoogleDatasetProcessor
from ingen.preprocessors import BitbrainsDatasetProcessor
from ingen.preprocessors import UniformDatasetProcessor
from ingen.preprocessors import HotspotsDatasetProcessor

from ingen.binning import Binning_Types


def validate_binning_domain(ctx, param, value):
   # domain = None and datasource --> derive domain
   # domain = None and datasource is None --> Error
   # domain != None
   #     --> validate domain (dim. should match, list of floats>0)

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


@generate.command(short_help='generate binning', name ='binning')
@click.option("--datasource", type=click.Path(exists=True))
@click.option("--domain", callback=validate_binning_domain)
@click.argument("type", type=click.Choice(
   [name.lower() for name, value in Binning_Types.__members__.items()
      if value.value < 90]
))
@click.argument("amount", callback=validate_binning_amount)
@click.argument("output", type=click.Path())
def g_binning(datasource, domain, type, amount, output):
   if datasource is None and domain is None:
      raise click.UsageError("Either a datasource or a domain is required.")
   click.echo('Not implemented')
   pass


@generate.command(short_help='derive model', name='model')
def g_model():
   click.echo('Not implemented')
   pass


@generate.command(short_help='generate bundles', name ='bundles')
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
