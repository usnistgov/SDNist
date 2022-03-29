# Change Log

## v1.3.1 - 2022-03-29

### Added
* Support for providing k-marginal number of permutations through command-line parameter --n-permutations
* Stand-alone script for scoring datasets using apparent match distribution metric


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