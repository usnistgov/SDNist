
# SDNist: Benchmark Data and Evaluation Tools for Data Synthesizers

This package provides tools for standardized and reproducible comparison of synthetic generator models on real-world data and use cases. Both datasets and metrics were developed for and vetted through the [*NIST PSCR Differential Privacy Temporal Map Challenge*](https://www.nist.gov/ctl/pscr/open-innovation-prize-challenges/past-prize-challenges/2020-differential-privacy-temporal).

## Quick introduction

You have two possible workflows:
1) Manually manage the public and private datasets as `pandas.DataFrame` objects, directly generate your synthetic data, and directly compute the score.
2) Reproduce the setup of the challenge---i.e., create a synthesizer subclass of `challenge.submission.Model`, then call `run(model, challenge="census")`. This makes sure your synthesizer is scored against the same datasets as in the Challenge.

In all cases, the scoring does not numerically check whether your synthesizer is actually $\epsilon$-differentially private or not. You have to provide a formal proof yourself.

## Installation

Requirements:  [Python >=3.6](https://www.python.org/downloads/)

The SDNist source code is hosted on Github, and all the data tables should be downloaded from the [SDNist Github Releases](https://github.com/usnistgov/SDNist/releases).
Alternatively, the data can be manually downloaded as part of the latest release [SDNist Release 1.3.0](https://github.com/usnistgov/SDNist/releases/tag/v1.3.0).

* Data Download Notes: 
  * SDNist does not  download just a specific dataset; instead, it downloads all the available datasets in the library.  
  * If data is manually downloaded, copy the contents inside the 'data' directory from the extracted zip file to your data root directory.
  * The default root data directory of SDNist is `<your-current-working-directory>/data`. The current working directory
  is the directory in which you run the SDNist library through a console/terminal, or the directory that contains your Python or IPython files
  that imports the SDNist library.
<!--  last part of sentence above, referring to Python files and importing SDNist library: is it correctly worded?  seems confusing -->

- Install via `pip` from [PyPi](https://pypi.org/) directory:

```
pip install sdnist
```


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
## Contributions

This repository is being actively developed, and we welcome contributions.

If you encounter a bug, [please create an issue](https://github.com/usnistgov/SDNist/issues/new).

Feel free to create a Pull Request to help us correct bugs and other issues.

Please contact us if you wish to augment or expand existing features.  


## Examples

### 1) Option 1 (quickest)
#### Loading and scoring

```
>>> import sdnist

>>> dataset, schema = sdnist.census()  # Retrieve public dataset
>>> dataset.head()
      PUMA  YEAR   HHWT  GQ  ...  POVERTY  DEPARTS  ARRIVES  sim_individual_id
0  17-1001  2012   88.0   1  ...      118      902      909                 12
1  17-1001  2012   61.0   1  ...      262      732      744                 33
2  17-1001  2012   54.0   1  ...      118      642      654                401
3  17-1001  2012  106.0   1  ...      262        0        0                470
4  17-1001  2012   31.0   1  ...      501        0        0                702
[5 rows x 36 columns]

>>> synthetic_dataset = dataset.sample(n=20000)  # Build a fake synthetic dataset

# Compute the score of the synthetic dataset
>>> sdnist.score(dataset, synthetic_dataset, schema, challenge="census")  
100%|███████████████████████████████████████████| 50/50 [00:04<00:00, 12.11it/s]
CensusKMarginalScore(847)
```

#### Discretizing a dataset
Many synthesizers require working on categorical/discretized data, yet many features of `sdnist` datasets are actually
integer or floating point valued. `sdnist` provide a simple tool to discretize/undiscretize `sdnist` datasets.

First, note that the k-marginal score itself works on categorical data under the hood. For fairness, the bins that are used can be considered public. They are available as follows:

The ACS (American Community Survey) dataset:

```
>>> bins = sdnist.kmarginal.CensusKMarginalScore.BINS
```

The Chicago taxi dataset:
```
>>> bins = sdnist.kmarginal.TaxiKmarginalScore.BINS
```



The `pd.DataFrame` datasets can then be discretized using

```
>>> dataset_binned = sdnist.utils.discretize(dataset, schema, bins)
```

`sdnist.utils.discretize` returns a `pd.DataFrame` where each value is remapped to `(0, n-1)` where `n` is the number of distinct values. Note that the even though the `score` functions should be given *unbinned* datasets (i.e., if your synthesizer works on discretized dataset), you should first undiscretize your synthetic data. This can be done using

```
>>> synthetic_dataset_binned = ... # generate your synthetic data using your own method
>>> synthetic_dataset = sdnist.utils.undo_discretize(synthetic_dataset_binned, schema, bins)
```

### Directly computing the score on a given `.csv` file

You can directly run from a terminal:

```
% python -m sdnist your_file.csv
```

This will score against the public census (ACS) dataset and display the results on an html page:  

![](examples/score_example.png)

To score the synthetic dataset against one of the test datasets:
```
% python -m sdnist your_synthetic_ga_nc_sc.csv --test-dataset GA_NC_SC_10Y_PUMS
```
Other options are available by calling `--help`.

### Computing aggregate score for all synthetic files generated using different epsilon values
To generate a final aggregate score over all epsilon values for the Census Challenge: 

```
% python -m sdnist.challenge.submission 
```

To score synthetic data file for dataset GA_NC_SC_10Y_PUMS:
```
% python -m sdnist.challenge.submission --test-dataset GA_NC_SC_10Y_PUMS
```

To score synthetic data files and visualize scores on an interactive map-based html visualizer:
```
% python -m sdnist.challenge.submission --html
```

To score synthetic data files during algorithm development (uses public dataset IL_OH_10Y_PUMS):
```
python -m sdnist.challenge.submission --public --html
```

The above commands assume that the synthetic data is located in the following directory: 
`[current-working-directory]/results/census/`.  
Each synthetic output file should be named with respect to the epsilon value used for its synthesis. 
In its default settings, SDNist performs scoring for epsilons 0.1, 1.0, and 10.0, so the synthetic files would be named 
eps=0.1.csv, eps=1.0.csv and eps=10.0.csv, where eps=0.1.csv is synthesized using epsilon value 0.1 and so on.
 

To generate a final aggregate score over all epsilon values for the Taxi Challenge with a private dataset other
than the default:
```
% python -m sdnist.challenge.submission --challenge taxi --test-dataset taxi2016 
```

The above commands assume that the synthetic data is located in the following directory: 
`[current-working-directory]/results/taxi/`.  
Each synthetic output file should be named with respect to the epsilon value used for its synthesis. 
In its default settings, SDNist performs scoring for epsilons 1.0 and 10.0, so the synthetic files would be named 
eps=1.0.csv and eps=10.0.csv, where eps=1.0.csv is synthesized using epsilon value 1.0 and so on.

NOTE: The filename of the synthetic data should exactly match the epsilon value provided in the parameters.json file
of the public or private dataset. If an epsilon value mentioned in the parameters.json file is `1`, 
then the synthetic data filename should be `esp=1.csv`; if an epsilon value mentioned is 1.0, then the synthetic data filename should be `eps=1.0.csv`.

The `sdnist.challenge.submission` module is  used mainly for computing aggregate scores over different 
epsilon values, but it can also be used to inspect scores for each epsilon value separately.  
To visualize scores over different values of epsilon, year, or PUMA (available only for the Census Challenge):
```
% python -m sdnist.challenge.submission --html
```

Other options are available by calling `--help`.

### 2) Option 2 (slightly more advanced and time-consuming)
#### Reproducing the baselines from the Challenge by subclassing `challenge.submission.Model`

Some examples of subclassing `challenge.submission.Model` are available in the library.

#### Subsample

Build a synthetic dataset by randomly subsampling 10% of the private dataset:

```
python -m sdnist.challenge.subsample
```

Output :

```
python -m sdnist.challenge.subsample
2021-11-23 14:55:07.889 | INFO     | sdnist.challenge.submission:run:66 - Skipping scoring for eps=0.1.
2021-11-23 14:55:07.889 | INFO     | sdnist.challenge.submission:run:73 - Resuming scoring from results/census/eps=1.csv.
2021-11-23 14:55:08.007 | INFO     | sdnist.challenge.submission:run:88 - Computing scores for eps=1.
100%|███████████████████████████████████████████| 50/50 [00:05<00:00,  9.37it/s]
2021-11-23 14:55:14.969 | SUCCESS  | sdnist.challenge.submission:run:92 - eps=1score=842.68
2021-11-23 14:55:14.985 | INFO     | sdnist.challenge.submission:run:79 - Generating synthetic data for eps=10.
2021-11-23 14:55:15.565 | INFO     | sdnist.challenge.submission:run:85 - (saved to results/census/eps=10.csv)
2021-11-23 14:55:15.565 | INFO     | sdnist.challenge.submission:run:88 - Computing scores for eps=10.
100%|███████████████████████████████████████████| 50/50 [00:05<00:00,  9.39it/s]
2021-11-23 14:55:22.530 | SUCCESS  | sdnist.challenge.submission:run:92 - eps=1score=842.42

```

Note that the resulting synthetic dataset is not differentially private.

#### Random values

Build a synthetic dataset by chosing random valid values:

```
python -m sdnist.challenge.baseline
```

This corresponds to the baseline of Sprint 2 (the 2020 Challenge). The output can be considered 0-differentially private if the schema itself is public.

Output:
```
2021-11-23 14:59:58.975 | INFO     | sdnist.challenge.submission:run:79 - Generating synthetic data for eps=0.1.
Generation: 100%|█████████████████████████████████| 20000/20000 [00:32<00:00, 608.57it/s]
2021-11-23 15:00:31.939 | INFO     | sdnist.challenge.submission:run:85 - (saved to results/census/eps=0.1.csv)
2021-11-23 15:00:31.939 | INFO     | sdnist.challenge.submission:run:88 - Computing scores for eps=0.1.
100%|████████████████████████████████████████████████████| 50/50 [00:05<00:00,  9.64it/s]
2021-11-23 15:00:38.664 | SUCCESS  | sdnist.challenge.submission:run:92 - eps=0.1	score=186.73
2021-11-23 15:00:38.682 | INFO     | sdnist.challenge.submission:run:79 - Generating synthetic data for eps=1.
Generation: 100%|█████████████████████████████████| 20000/20000 [00:34<00:00, 584.78it/s]
2021-11-23 15:01:12.962 | INFO     | sdnist.challenge.submission:run:85 - (saved to results/census/eps=1.csv)
2021-11-23 15:01:12.962 | INFO     | sdnist.challenge.submission:run:88 - Computing scores for eps=1.
100%|████████████████████████████████████████████████████████████████| 50/50 [00:05<00:00,  9.50it/s]
2021-11-23 15:01:19.818 | SUCCESS  | sdnist.challenge.submission:run:92 - eps=1	score=187.32
2021-11-23 15:01:19.835 | INFO     | sdnist.challenge.submission:run:79 - Generating synthetic data for eps=10.
Generation: 100%|█████████████████████████████████████████████| 20000/20000 [00:33<00:00, 596.94it/s]
2021-11-23 15:01:53.417 | INFO     | sdnist.challenge.submission:run:85 - (saved to results/census/eps=10.csv)
2021-11-23 15:01:53.417 | INFO     | sdnist.challenge.submission:run:88 - Computing scores for eps=10.
100%|████████████████████████████████████████████████████████████████| 50/50 [00:05<00:00,  9.94it/s]
2021-11-23 15:02:00.076 | SUCCESS  | sdnist.challenge.submission:run:92 - eps=10	score=186.73

```

### Other examples
Other examples are available in the `examples/` folder.  DPSyn and Minutemen are directly adapted from the public repos of their authors:
- DPSyn : https://github.com/agl-c/deid2_dpsyn
- Minutemen : https://github.com/ryan112358/nist-synthetic-data-2021. This examples requires the `private-pgm` library (https://github.com/ryan112358/private-pgm)
