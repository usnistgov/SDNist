import json
import os
import datetime
import argparse
from pathlib import Path
from sdnist.report.spinner import Spinner

from sdnist.report.common import REPORTS_DIR
import sdnist.load
from sdnist.load import data_challenge_map
from sdnist.report import \
    generate, Path, utility_score, privacy_score,\
    ReportData, Dataset
from sdnist.report.dataset import data_description
from sdnist.load import TestDatasetName

from sdnist.strs import *


def run(synthetic_filepath: Path,
        output_directory: Path = REPORTS_DIR,
        test: TestDatasetName = TestDatasetName.NONE,
        data_root: Path = 'sdnist_toy_data',
        download: bool = False):
    outfile = Path(output_directory, 'report.json')
    report_data = ReportData(output_directory=output_directory)

    if not outfile.exists():
        print('Loading Dataset...')
        dataset = Dataset(synthetic_filepath, test, data_root, download)
        report_data = data_description(dataset, report_data)
        # Create scores
        print('Computing Utility Scores...')
        report_data = utility_score(dataset, report_data)
        print('Computing Privacy Scores...')
        report_data = privacy_score(dataset, report_data)
        report_data.save()
        report_data = report_data.data
    else:
        with open(outfile, 'r') as f:
            report_data = json.load(f)

    # Generate Report
    generate(report_data, output_directory)


class NoAction(argparse.Action):
    def __init__(self, **kwargs):
        kwargs.setdefault('default', argparse.SUPPRESS)
        kwargs.setdefault('nargs', 0)
        super(NoAction, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pass


if __name__ == "__main__":
    bundled_datasets = [TestDatasetName.MA_ACS_EXCERPT_2019,
                        TestDatasetName.TX_ACS_EXCERPT_2019,
                        TestDatasetName.OUTLIER_ACS_EXCERPT_2019]
    parser = argparse.ArgumentParser()
    parser.register('action', 'none', NoAction)
    parser.add_argument("synthetic_dataset", type=argparse.FileType("r"),
                        metavar="PATH_SYNTHETIC_DATASET",
                        help="Location of synthetic dataset (csv or parquet file)")
    parser.add_argument("target_dataset_name",
                        metavar="TARGET_DATASET_NAME",
                        choices=bundled_datasets,
                        help="Select name of the target dataset "
                             "that was used to generated given synthetic dataset")
    parser.add_argument("--data-root", type=Path,
                        default=Path("sdnist_toy_data"),
                        help="Path of the directory "
                             "to be used as the root for the target datasets")
    parser.add_argument("--download", type=bool, default=True,
                        help="Download toy datasets if not present locally")

    group = parser.add_argument_group(title='Choices for Target Dataset Name:')
    for e in bundled_datasets:
        group.add_argument(str(e.name), help="", action='none')

    args = parser.parse_args()

    target_name = args.target_dataset_name

    if not REPORTS_DIR.exists():
        os.mkdir(REPORTS_DIR)
    TARGET_DATA = TestDatasetName[target_name]

    # create directory for current report run
    time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')

    this_report_dir = Path(REPORTS_DIR, f'{target_name}_{time_now}')

    if not this_report_dir.exists():
        os.mkdir(this_report_dir)

    input_cnf = {
        TEST: TARGET_DATA,
        SYNTHETIC_FILEPATH: Path(args.synthetic_dataset.name),
        DATA_ROOT: Path(args.data_root),
        OUTPUT_DIRECTORY: this_report_dir,
        DOWNLOAD: args.download
    }

    run(**input_cnf)
