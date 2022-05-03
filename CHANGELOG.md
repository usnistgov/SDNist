# Change Log

## v1.3.2 - 2022-05-03

### Added
* html and public, commandline parameters to `sdnist.challenge.submission` module to allow using this
module for scoring with public data sets.

### Changed


### Fixed
* `sdnist.challenge.submission` to read epsilon from dataset's parameters json file 
instead of using hard-coded values.
* Generating collective html visualization of all synthetic datasets scored using `sdnist.challenge.submission`
module.
* Jinja template to render drop-down selection of year and puma for census challenge visualization.

## v1.3.1 - 2022-04-05

### Added
* Graph Map Edge scoring for taxi challenge.
* Apparent Match Distribution privacy metric.
* Support for running `sdnist.challenge.submission` module
for commandline. `sdnist.challenge.submission` module generates
final score which can be compared to leaderboard scores

### Changed

* Score function computes aggregate score over all scoring metrics
available for a challenge.
  * k-marginal for census challenge.
  * k-marginal, hoc and graph-edge-map for taxi challenge

### Fixed
* Higher Order Conjunction Metric

## v1.3.0 - 2022-03-23

### Added
* Support for visualizing k-marginal scores of each puma with openstreet map for all available census datasets in SDNist. Support available for datasets:
  * IL_OH_10Y_PUMS.[csv, json, parquet] tabular supported with IL_OH_10Y_PUMS.geojson.
  * GA_NC_SC_10Y_PUMS.[csv, json, parquet] tabular (csv, json, parquet) supported with GA_NC_SC_10Y_PUMS.geojson.
  * NY_PA_10Y_PUMS.[csv, json, parquet] tabular supported with NY_PA_10Y_PUMS.geojson.

### Changed
* No more support for downloading a specific missing dataset instead SDNist downloads all the available datasets from the [sdnist github releases](https://github.com/usnistgov/SDNist/releases).

### Fixed
* problem with importing `importlib_resources` in python >= 3.7
* broken download links for fetching data.