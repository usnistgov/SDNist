# SDNIST Synthetic Data Quality Report

This tool evaluates utility and privacy of a given synthetic data set, and 
generates a summary quality report with performance of a synthetic data
set enumerated and illustrated for each utility and privacy metric.

## Installation
Requirements:  [Python >=3.7](https://www.python.org/downloads/)

The SDNist source code is hosted on Github and all the data tables will be downloaded from the [SDNist Github Releases](https://github.com/usnistgov/SDNist/releases).
Alternatively, the data can be manually downloaded as part of the latest release [SDNist Release 1.4.0-a.1](https://github.com/usnistgov/SDNist/releases/tag/v1.4.0-a.1)

* Data Download Notes: 
  * SDNist does not just download specific dataset instead it downloads all the available datasets that are provided by the library.  
  * If data is manually downloaded, copy the contents inside the 'data' directory from the extracted zip file to your data root directory.
  * Default root data directory of SDNist is `<your-current-working-directory>/data`. Current working directory
  is the directory in which the user runs SDNist library through console/terminal, or the directory that contains your python or ipython files
  that imports SDNist library.
  

- Install `sdnist` Python module through git repository:
```
git clone https://github.com/usnistgov/SDNist && cd SDNist
pip install .
```

- Install `sdnist` Python module through git in a virtual environment:

MAC OS / Linux
```
git clone https://github.com/usnistgov/SDNist && cd SDNist
python3 -m venv venv
. venv/bin/activate
pip install .
```

Windows
```
git clone https://github.com/usnistgov/SDNist && cd SDNist
python3 -m venv venv
. venv/Scripts/activate
pip install .
```

## Generating Synthetic Data Quality Report

Usage:
```
% python -m sdnist.report PATH_SYNTHETIC_DATASET TARGET_DATASET_NAME --data-root
```
SDNIST provides `sdnist.report` package for generating synthetic data quality reports.
`sdnist.report` package takes three arguments:
* PATH_SYNTHETIC_DATASET: Absolute or relative path to synthetic data set csv or parquet file. 
If provided path is relative, it should be relative to the current working directory.
* TARGET_DATASET_NAME: It should be the name of one of the data sets packaged with sdnist 
library. This is the name of the data set from which input synthetic data set was generated, 
and it can be one of the following:
  * GA_NC_SC_10Y_PUMS
  * NY_PA_10Y_PUMS
  * IL_OH_10Y_PUMS
  * MA_ACS_EXCERPT_2019
  * TX_ACS_EXCERPT_2019
  * OUTLIER_ACS_EXCERPT_2019
  * taxi2016
  * taxi2020
* --data-root: Absolute or relative path to the directory containing target data, or the 
directory where the target data should be downloaded if is it not available locally. Default
directory is set to 'data'.

Examples:
```
% python -m sdnist.report synthetic_data/syn_ma_acs_excerpt_2019.csv MA_ACS_EXCERPT_2019
```
In above example, `PATH_SYNTHETIC_DATA` is `synthetic_data/syn_ma_acs_excerpt_2019.csv` and
`TARGET_DATA_NAME` is `MA_ACS_EXCERPT_2019`. `--data-root` is skipped which defaults to path
`data` which is assumed to be relative to the current working directory.

```
% python -m sdnist.report synthetic_data/syn_tx_acs_excerpt_2019.csv TX_ACS_EXCERPT_2019 --data-root 'mydata/data'
```
In above example, `--data-root` argument is provided with data directory other than the default
directory `data`. In this case either the data should be present at `mydata/data` directory or
it will be downloaded into this directory.
