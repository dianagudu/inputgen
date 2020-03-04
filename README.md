# inputgen
Input Generator of realistic bundles for cloud resources


* Real cloud traces included so far:
  * [Google Cluster data](https://github.com/google/cluster-data)
  * [Bitbrains fastStorage data](http://gwa.ewi.tudelft.nl/datasets/gwa-t-12-bitbrains)

### prerequisites

* All libs in requirements.txt

### usage

* Full description by consulting the help option for each command:

      $ python ingencli.py --help
      
      Usage: ingencli.py [OPTIONS] COMMAND [ARGS]...
      
      Options:
        --help  Show this message and exit.
      
      Commands:
        compare  subcommand to calculate different KPIs
        create   subcommand to create things
        plot     subcommand to visualize things

* Example workflow:
  * create datasource from raw data (real cloud traces)
    * e.g. for google dataset, assume raw data is stored in a csv file ``google.csv``
    * save processed datasource to ``google.datasource``

          python ingencli.py create datasource google google.datasource google.csv

  * create model of the datasource with (previously created) binning
    * the binning expresses the model "resolution", e.g. with 8 regular bins per dimension

          python ingencli.py create binning --datasource google.datasource regular 8 google.binning
          python ingencli.py create model google.datasource google.binning google.model

  * create artificial cloud workload, parameterized by:
    * model, e.g. the model created above
    * binning (can be different from model binning), e.g. with 16 regular bins in each dimension
    * amount of bundles, e.g. 10000

          python ingencli.py create binning --datasource google.datasource regular 16 bundles.binning
          python ingencli.py create bundles google.model 10000 bundles.binning bundles.datasource

    * the generated workload is stored to ``bundles.datasource`` using the same format as the original datasource
