#!/usr/bin/env python3
import click
import yaml
import os.path
import numpy as np

from ingen.preprocessors import GoogleDatasetProcessor
from ingen.preprocessors import BitbrainsDatasetProcessor
from ingen.preprocessors import UniformDatasetProcessor
from ingen.preprocessors import HotspotsDatasetProcessor
from ingen.preprocessors import DataReader

from ingen.binning import Binning
from ingen.binning import Binning_Types
from ingen.binning import BinningGenerator
from ingen.binning import Pad_Modes

from ingen.histogram import Pad_Values

from ingen.model import Interpolation_Modes
from ingen.model import ModelParams
from ingen.model import Model


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


def validate_binning(ctx, param, value):
    # if filename exists, load from file
    if os.path.isfile(value):
        try:
            with open(value, "r") as f:
                bobj = yaml.load(f)
                return Binning.from_dict(bobj)
        except Exception:
            # raise this if file exists but does not contan a binning
            raise click.FileError(value, 'malformed binning file.')
    else:
        # else, treat value as edges
        click.echo("File %s does not exist, treating it as bin edges..." % value)
        try:
            # split string into edges per dimension, then sort and remove duplicates
            edges = [np.unique(np.array(x.split(","), dtype=float))
                     for x in value.split(":")]
            # all edges must be positive
            if any((edges_along_dim < 0).any() for edges_along_dim in edges):
                raise ValueError(None)
            # create binning
            return Binning(Binning_Types.USER, edges)
        except ValueError:
            raise click.BadParameter('%s should be either a path to file where binning is stored, \n\
or a colon-separated list of edges per dimensions, with a comma-separated list of floats > 0\n\
as bin edges in each dimension, not \'%s\'.'
            % (param.name, value))


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
    The binning is written to "OUTPUT" in yaml format.

    AMOUNT can be an integer or a comma-separated list of integers, representing
    the number of bins per dimension.

    When not specified, the binning domain is inferred from datasource.
    """
    # datasource = None and domain == None --> Error
    # datasource = None and domain != None --> OK
    # datasource != None and domain = None --> derive domain from datasource
    # datasource != None and domain != None --> dim. should match, use domain
    source = None
    if domain is None and datasource is None:
        raise click.UsageError("Either a datasource or a domain is required.")
    elif not datasource is None:
        try:
            source = DataReader(datasource).read()
        except:
            raise click.FileError(datasource, "does not exist or is not readable.")
        if not domain is None:
            if len(source.domain) != len(domain):
                    raise click.BadOptionUsage("domain",
                                               "Dimensions of of datasource domain (%d) and given domain (%d) mismatch."
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

    with open(output, "w") as f:
        yaml.dump(binning.to_dict(), f)
        click.echo("Saved binning to %s" % output)


@generate.command(short_help='derive model', name='model')
@click.option("--padmode", type=click.Choice([
   'epsilon', 'mirror']), default='mirror')
@click.option("--padvalue", type=click.Choice([
   'zero', 'neg_one', 'copy', 'neg_copy']), default='neg_copy')
@click.option("--interpolation", type=click.Choice([
   'linear', 'rbf_linear', 'rbf_multiquad']), default='linear')
@click.option("--resources", help='comma-separated list of resource names')
@click.argument("datasource", type=click.Path())
@click.argument("binning", callback=validate_binning)
@click.argument("output", type=click.Path())
def g_model(padmode, padvalue, interpolation, resources,
            datasource, binning, output):
    """Derives a model from DATASOURCE with given BINNING.
    The model is written to "OUTPUT".

    BINNING can be a path to a previously created binning, or custom bin edges
    in all dimension: dimensions are separated by colons, edge values in
    each dimension are separated by commas.
    """
    # datasource checks
    try:
        source = DataReader(datasource).read()
    except:
        raise click.FileError(datasource, "does not exist or is not readable.")

    # validate dimensionality match between binning and source
    if binning.dimensions != len(source.domain):
        raise click.UsageError(
            "Dimensions of binning (%d) and datasource (%d) mismatch."
            % (binning.dimensions, len(source.domain)))

    # resources checks: split list and verifYies dim match with source
    if not resources is None:
        resources = resources.split(",")
        if len(resources) != len(source.column_names):
            raise click.BadOptionUsage("resources",
            "Dimensions of resources (%d) and datasource (%d) mismatch."
            % (len(resources), len(source.column_names)))

    # convert model params to enums and create ModelParams object
    model_params = ModelParams(
        Pad_Modes[padmode.upper()],
        Pad_Values[padvalue.upper()],
        Interpolation_Modes[interpolation.upper()]
    )

    # histogram the data with given binning
    histogram = source.get_histogram(binning)

    model = Model.from_histogram(model_params, histogram, resources)
    model.to_file(output)


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
