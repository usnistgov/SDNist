import json
import os
import datetime

from sdnist.report import \
    generate, Path, score, REPORTS_DIR, ReportData
from sdnist.load import TestDatasetName

from sdnist.report.strs import *


def run(challenge: str,
        synthetic_filepath: Path,
        output_directory: Path = REPORTS_DIR,
        public: bool = True,
        test: TestDatasetName = TestDatasetName.NONE,
        data_root: Path = 'data'):
    outfile = Path(output_directory, 'report.json')

    if not outfile.exists():
        # Create scores
        report_data = score(challenge, synthetic_filepath, output_directory, public, test, data_root)
        report_data.save(outfile)
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
