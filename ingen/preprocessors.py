import pandas as pd
import numpy as np
import datetime
import os
import json
import yaml

from .helper import objectview
from .histogram import Histogram


class DatasetProcessor():
    def __init__(self, name, output_filename, domain):
        self.__name = name
        self.__output_filename = output_filename
        self.__domain = domain

    @property
    def domain(self):
        return self.__domain

    @property
    def name(self):
        return self.__name

    def output_filename(self, extension):
        return "%s.%s" % (self.__output_filename, extension)


class GoogleDatasetProcessor(DatasetProcessor):
    __schema = {'start_time': np.int_,
                'end_time': np.int_,
                'job_id': np.int_,
                'task_index': np.int_,
                'machine_id': np.int_,
                'cpu_rate': np.float_,
                'canonical_mem_usage': np.float_,
                'assigned_mem_usage': np.float_,
                'unmapped_page_cache': np.float_,
                'total_page_cache': np.float_,
                'max_mem': np.float_,
                'disk_io_time': np.float_,
                'local_disk_space': np.float_,
                'max_cpu_rate': np.float_,
                'max_disk_io_time': np.float_,
                'cycles_per_instr': np.float_,
                'mem_accesses_per_instr': np.float_,
                'sample_portions': np.float_,
                'aggregation_type': np.bool_,
                'sampled_cpu_usage': np.float_}

    __domain = [0.3, 0.3, 0.003]

    @property
    def schema(self):
        return self.__schema

    @property
    def source_filenames(self):
        return self.__source_filenames

    def __init__(self, name, output_filename, source_filenames):
        super().__init__(name=name,
                         output_filename=output_filename, domain=self.__domain)
        self.__source_filenames = [os.path.abspath(x)
                                   for x in source_filenames]

    def process(self):
        col = ['cps', 'max_mem', 'local_disk_space']

        data = []
        for file_name in self.source_filenames:
            raw = pd.read_csv(file_name, header=None,
                              names=self.schema.keys(), dtype=self.schema)
            raw.query('cpu_rate > 0.0', inplace=True)
            raw.eval('duration = end_time - start_time', inplace=True)
            raw.eval('cycles = cpu_rate * duration', inplace=True)
            raw = raw.groupby(["job_id", "task_index"])
            raw = raw.agg({'cycles': 'sum', 'max_mem': 'max',
                           'duration': 'sum', 'local_disk_space': 'max'})
            raw.eval('cps = cycles / duration', inplace=True)

            raw.query('cps > 0.001 and cps < @self.domain[0] \
                       and max_mem > 0.001 and max_mem < @self.domain[1] \
                       and local_disk_space < @self.domain[2]',
                      inplace=True)
            raw = raw[col]
            data.append(raw)

        data = pd.concat(data)
        data.to_csv(self.output_filename("csv"), header=False,
                    index=False, mode="w")

        mobj = {
            "source_info":
            {
                "name": self.name,
                "type": "Google",
                "creation_date": datetime.datetime.now().isoformat(),
                "source_filenames": self.source_filenames,
            },
            "dataset": {
                "domain": self.domain,
                "column_names": col
            }
        }

        # with open(self.output_filename("json"), "w") as f:
        #    json.dump(mobj, f, indent=4)

        with open(self.output_filename("yaml"), "w") as f:
            yaml.dump(mobj, f)

        src = DataSource(
            info=objectview(mobj["source_info"]),
            domain=mobj["dataset"]["domain"],
            column_names=mobj["dataset"]["column_names"],
            data=data
        )

        return src


class DataSource():
    def __init__(self, info, domain, column_names, data):
        self.__info = info
        self.__domain = domain
        self.__column_names = column_names
        self.__data = data

    @property
    def data(self):
        return self.__data

    @property
    def info(self):
        return self.__info

    @property
    def domain(self):
        return self.__domain

    @property
    def column_names(self):
        return self.__column_names

    def __call__(self):
        return self.data

    def get_histogram(self, binning):
        values, _ = np.histogramdd(
            self.data, bins=binning.edges, normed=True)
        return Histogram(binning, values)


class DataReader():
    def __init__(self, filename):
        self.__datafile = "%s.csv" % filename
        self.__metafile = "%s.yaml" % filename

    def read(self):
        with open(self.__metafile, "r") as mf:
            mobj = yaml.load(mf)

        with open(self.__datafile, "r") as df:
            data = np.loadtxt(df, delimiter=",")

        src = DataSource(
            info=objectview(mobj["source_info"]),
            domain=mobj["dataset"]["domain"],
            column_names=mobj["dataset"]["column_names"],
            data=data
        )

        return src
