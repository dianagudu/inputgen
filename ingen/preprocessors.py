import pandas as pd
import numpy as np
import datetime
from time import time
import os
import json
import yaml
import glob

from .helper import objectview
from .histogram import Histogram


class DatasetProcessor():
    def __init__(self, name, output_filename, domain, column_names=None):
        self.__name = name
        self.__output_filename = output_filename
        self.__domain = domain
        if column_names:
            self.__column_names = column_names
        else:
            self.__column_names = ["Resource%s" % i
                                   for i, _ in enumerate(self.__domain)]

    @property
    def domain(self):
        return self.__domain

    @property
    def name(self):
        return self.__name

    @property
    def column_names(self):
        return self.__column_names

    def output_filename(self, extension):
        return "%s.%s" % (self.__output_filename, extension)

    def save_datasource(self, data, info_dict):
        # write data to output files and create DataSource object
        data.to_csv(self.output_filename("csv"), header=False,
                    index=False, mode="w")
        mobj = {
            "source_info": info_dict,
            "dataset": {
                "domain": self.domain,
                "column_names": self.column_names
            }
        }

        # with open(self.output_filename("json"), "w") as f:
        #    json.dump(mobj, f, indent=4)

        with open(self.output_filename("yaml"), "w") as f:
            yaml.dump(mobj, f, default_flow_style=False)

        src = DataSource(
            info=objectview(mobj["source_info"]),
            domain=mobj["dataset"]["domain"],
            column_names=mobj["dataset"]["column_names"],
            data=data.values
        )

        return src


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
    __column_names = ['cps', 'max_mem', 'local_disk_space']

    @property
    def schema(self):
        return self.__schema

    @property
    def source_filenames(self):
        return self.__source_filenames

    def __init__(self, name, output_filename, source_filenames):
        super().__init__(name=name,
                         output_filename=output_filename,
                         domain=self.__domain,
                         column_names=self.__column_names)
        self.__source_filenames = [os.path.abspath(x)
                                   for x in source_filenames]

    def process(self):
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
            raw = raw[self.column_names]
            data.append(raw)

        data = pd.concat(data)

        info_dict = {
                "name": self.name,
                "type": "Google",
                "creation_date": datetime.datetime.now().isoformat(),
                "source_filenames": self.source_filenames,
            }

        return super().save_datasource(data, info_dict)


class BitbrainsDatasetProcessor(DatasetProcessor):
    __domain = [0.35, 0.1, 0.02, 0.005]
    __column_names = ['cpu_usage', 'mem_usage', 'disk_io', 'net_io']

    @property
    def source_folder(self):
        return self.__source_folder

    def __init__(self, name, output_filename, source_folder):
        super().__init__(name=name,
                         output_filename=output_filename,
                         domain=self.__domain,
                         column_names=self.__column_names)
        self.__source_folder = os.path.abspath(source_folder)

    def __get_vm_stats(self, filename):
        columns = ['CPU usage [MHZ]',
                   'Memory usage [KB]',
                   'Disk read throughput [KB/s]',
                   'Disk write throughput [KB/s]',
                   'Network received throughput [KB/s]',
                   'Network transmitted throughput [KB/s]'
                   ]
        vm = pd.read_csv(filename, sep=';\t', engine='python')
        vm = vm[columns]    # select only useful columns and then rename them
        vm.columns = ['cpu_usage', 'mem_usage',
                      'disk_read', 'disk_write',
                      'network_received', 'network_transmitted']

        vm.eval("disk_io = disk_read + disk_write", inplace=True)
        vm.eval("net_io = network_received + network_transmitted", inplace=True)
        return vm[self.column_names].max()

    def process(self):
        data = pd.concat([self.__get_vm_stats(f)
                          for f in glob.glob(self.source_folder + "/*.csv")],
                         axis=1)
        data = data.T

        # scale data
        data = (data - data.min()) / (data.max() - data.min())
        # filter data
        data = data.query("cpu_usage < @self.domain[0] and \
                           mem_usage < @self.domain[1] and \
                           disk_io < @self.domain[2] and \
                           net_io < @self.domain[3]")

        info_dict = {
                "name": self.name,
                "type": "Bitbrains",
                "creation_date": datetime.datetime.now().isoformat(),
                "source_folder": self.source_folder,
            }

        return super().save_datasource(data, info_dict)


class UniformDatasetProcessor(DatasetProcessor):
    def __init__(self, name, output_filename, dimensions):
        super().__init__(name=name,
                         output_filename=output_filename,
                         domain=[1.0] * dimensions)
        self.__dimensions = dimensions

    def process(self):
        random_seed = np.random.randint(2**32-1)
        np.random.seed(random_seed)
        data = pd.DataFrame(np.random.rand(10000, self.__dimensions))
        info_dict = {
                "name": self.name,
                "type": "Uniform",
                "creation_date": datetime.datetime.now().isoformat(),
                "random_seed": random_seed,
            }

        return super().save_datasource(data, info_dict)


class HotspotsDatasetProcessor(DatasetProcessor):
    def __init__(self, name, output_filename, dimensions, hotspot_count):
        super().__init__(name=name,
                         output_filename=output_filename,
                         domain=[1.0] * dimensions)
        self.__dimensions = dimensions
        self.__hotspot_count = hotspot_count

    def process(self):
        random_seed = np.random.randint(2**32-1)
        np.random.seed(random_seed)
        data = []
        for _ in range(self.__hotspot_count):
            hs = np.random.rand(self.__dimensions)
            data += [hs] * int(
                (10000 / self.__hotspot_count) * 0.1 * np.random.rand() +
                (10000 / self.__hotspot_count) * 0.9
            )
        data = pd.DataFrame(np.array(data))

        info_dict = {
                "name": self.name,
                "type": "Hotspots",
                "creation_date": datetime.datetime.now().isoformat(),
                "random_seed": random_seed,
                "hotspot_count": self.__hotspot_count,
            }
        return super().save_datasource(data, info_dict)


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


class DataSourceIO():
    @staticmethod
    def read(filename):
        datafile = "%s.csv" % filename
        metafile = "%s.yaml" % filename
        with open(metafile, "r") as mf:
            mobj = yaml.load(mf)

        data = np.loadtxt(datafile, delimiter=",")

        src = DataSource(
            info=objectview(mobj["source_info"]),
            domain=mobj["dataset"]["domain"],
            column_names=mobj["dataset"]["column_names"],
            data=data
        )

        return src

    @staticmethod
    def write(datasource, filename):
        datafile = "%s.csv" % filename
        metafile = "%s.yaml" % filename

        np.savetxt(datafile, datasource.data, delimiter=",")

        mobj = {
            "source_info": datasource.info.__dict__,
            "dataset": {
                "domain": [float(x) for x in datasource.domain],
                "column_names": datasource.column_names
            }
        }

        # with open(filename_goes_here, "w") as f:
        #    json.dump(mobj, f, indent=4)

        with open(metafile, "w") as f:
            yaml.dump(mobj, f, default_flow_style=False)

        return
