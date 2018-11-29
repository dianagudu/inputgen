#!/usr/bin/env python3
import click

@click.group()
def cli():
    pass


@cli.command(short_help='generate a dataset derived from the Google cloud traces')
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
    pass


@cli.command(short_help='generate a dataset derived from the Bitbrains log format')
@click.option("--name", default="", help="Logical name of the dataset.")
@click.argument("output", type=click.Path())
@click.argument("input", type=click.Path())
def bitbrains(name, output, input):
    """Generates a dataset that is derived from the BitBrains fastStorage trace
       data[1] found in folder INPUT.

       The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".

       [1] http://gwa.ewi.tudelft.nl/datasets/gwa-t-12-bitbrains
    """
    pass


@cli.command(short_help='generate a uniform dataset')
@click.option("--name", default="", help="Logical name of the dataset.")
@click.argument("output", type=click.Path())
@click.argument("dimensions", type=int)
def uniform(name, output, dimensions):
    """Generates a DIMENSIONS-dimensional dataset consisting of uniformly
       distributed datapoints.

       The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".
    """
    pass


@cli.command(short_help='generate a dataset based on hotspots')
@click.option("--name", default="", help="Logical name of the dataset.")
@click.argument("output", type=click.Path())
@click.argument("dimensions", type=int)
@click.argument("hotspots", type=int)
def hotspots(name, output, dimensions, hotspots):
    """Generates a DIMENSIONS-dimensional dataset consisting
       of HOTSPOTS amount of hotspots.

       The data is written to "OUTPUT.csv", the metadata to "OUTPUT.yaml".
    """
    pass

if __name__ == '__main__':
    cli()
