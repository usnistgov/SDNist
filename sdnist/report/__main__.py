import json
import os
import datetime

from sdnist.report import \
    generate, Path, utility_score, privacy_score,\
    REPORTS_DIR, ReportData, Dataset
from sdnist.report.dataset import data_description
from sdnist.load import TestDatasetName

from sdnist.report.strs import *


def run(challenge: str,
        synthetic_filepath: Path,
        output_directory: Path = REPORTS_DIR,
        public: bool = True,
        test: TestDatasetName = TestDatasetName.NONE,
        data_root: Path = 'data'):
    outfile = Path(output_directory, 'report.json')
    report_data = ReportData(output_directory=output_directory)

    if not outfile.exists():
        dataset = Dataset(synthetic_filepath, challenge, public, test, data_root)
        report_data = data_description(dataset, report_data)
        # Create scores
        report_data = utility_score(dataset, report_data)
        report_data = privacy_score(dataset, report_data)
        report_data.save()
        report_data = report_data.data
    else:
        with open(outfile, 'r') as f:
            report_data = json.load(f)

    # Generate Report
    generate(report_data, output_directory)


if __name__ == "__main__":
    if not REPORTS_DIR.exists():
        os.mkdir(REPORTS_DIR)

    _challenge = CENSUS

    # create directory for current report run
    time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')
    testing = False
    if testing:
        this_report_dir = Path(REPORTS_DIR, f'{_challenge}')
    else:
        this_report_dir = Path(REPORTS_DIR, f'{_challenge}_{time_now}')

    if not this_report_dir.exists():
        os.mkdir(this_report_dir)

    input_cnf = {
        CENSUS: {
            PUBLIC: False,
            TEST: TestDatasetName.GA_NC_SC_10Y_PUMS,
            SYNTHETIC_FILEPATH: Path('myfile_ga.csv'),
            DATA_ROOT: Path('data'),
            OUTPUT_DIRECTORY: this_report_dir
        },
        TAXI: {
            PUBLIC: False,
            TEST: TestDatasetName.taxi2016,
            SYNTHETIC_FILEPATH: Path('taxi_syn.csv'),
            DATA_ROOT: Path('data'),
            OUTPUT_DIRECTORY: this_report_dir
        }
    }

    run(_challenge, **input_cnf[_challenge])
