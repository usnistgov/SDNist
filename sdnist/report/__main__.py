import json
import os

from sdnist.report import \
    generate, Path, score, REPORTS_DIR, ReportData
from sdnist.load import TestDatasetName

from sdnist.report.strs import *


def run(challenge: str,
        synthetic_filepath: Path,
        public: bool = True,
        test: TestDatasetName = TestDatasetName.NONE,
        data_root: Path = 'data'):
    outfile = Path(REPORTS_DIR, 'report.json')

    if not outfile.exists():
        # Create scores
        report_data = score(challenge, synthetic_filepath, public, test, data_root, outfile)
        report_data.save()
        report_data = report_data.data
    else:
        with open(outfile, 'r') as f:
            report_data = json.load(f)

    # Generate Report
    generate(report_data)


if __name__ == "__main__":
    input_cnf = {
        CENSUS: {
            PUBLIC: False,
            TEST: TestDatasetName.GA_NC_SC_10Y_PUMS,
            SYNTHETIC_FILEPATH: Path('myfile_ga.csv'),
            DATA_ROOT: Path('data')
        },
        TAXI: {
            PUBLIC: False,
            TEST: TestDatasetName.taxi2016,
            SYNTHETIC_FILEPATH: Path('taxi_syn.csv'),
            DATA_ROOT: Path('data')
        }
    }

    if not REPORTS_DIR.exists():
        os.mkdir(REPORTS_DIR)

    _challenge = CENSUS

    s_file_path = Path('myfile_ga.csv')
    run(_challenge, **input_cnf[_challenge])
