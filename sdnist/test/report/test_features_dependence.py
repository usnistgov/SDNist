from pathlib import Path

import pandas as pd
import datetime

from sdnist.report.__main__ import run
from sdnist.load import TestDatasetName
from sdnist.utils import *


def test_feature_dependence(synth_data_path: Path,
                            out_test_dir: Path,
                            out_reports_dir: Path):
    d = pd.read_csv(synth_data_path, index_col=0)
    columns = d.columns.tolist()
    for f in columns:
        print(f'----------TESTING DEPENDENCY FOR {f}------------')
        time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')

        this_report_dir = Path(out_reports_dir, f'{f}_na_{time_now}')

        if not this_report_dir.exists():
            os.mkdir(this_report_dir)

        dc = d.copy()
        if f in dc.columns:
            dc = dc.drop([f], axis=1)
        new_synth_path = Path(this_report_dir, 's_test.csv')

        dc.to_csv(new_synth_path)

        # try:
        run(new_synth_path,
            this_report_dir,
            TestDatasetName.national2019,
            test_mode=True)
        # except Exception as e:
        #     print(e)


if __name__ == "__main__":
    DATA_DIR = Path(Path(__file__).parent, 'data')
    synth_data_path = Path(DATA_DIR, 'na2019_1000.csv')

    # create intermediate test data directory
    OUT_TEST_DIR = Path('test_out_data')
    OUT_REPORTS_DIR = Path(OUT_TEST_DIR, 'reports')

    if not OUT_TEST_DIR.exists():
        create_path(OUT_TEST_DIR)

    if not OUT_REPORTS_DIR.exists():
        create_path(OUT_REPORTS_DIR)

    test_feature_dependence(synth_data_path,
                            OUT_TEST_DIR,
                            OUT_REPORTS_DIR)

