import pandas as pd
from pathlib import Path

from sdnist.load import TestDatasetName

from sdnist.report.dataset import Dataset
import sdnist.utils as u


def unique_exact_matches(target_data: pd.DataFrame, deidentified_data: pd.DataFrame):
    td, dd = target_data, deidentified_data
    cols = td.columns.tolist()

    # select rows that are unique in the target data
    u_td = td.loc[td.groupby(by=cols)[cols[0]].transform('count') == 1, :]

    # target unique records
    t_unique_records = u_td.shape[0]
    perc_t_unique_records = round(t_unique_records/td.shape[0] * 100, 2)

    # Keep only one copy of each duplicate row in the deidentified data
    dd = dd.drop_duplicates(subset=cols)

    merged = u_td.merge(dd, how='inner', on=cols)

    # number of unique target records that exactly match in deidentified data
    t_rec_matched = merged.shape[0]

    # percent of unique target records that exactly match in deidentified data
    perc_t_rec_matched = t_rec_matched/t_unique_records * 100

    perc_t_rec_matched = round(perc_t_rec_matched, 2)

    return t_rec_matched, perc_t_rec_matched, t_unique_records, perc_t_unique_records


if __name__ == '__main__':
    THIS_DIR = Path(__file__).parent
    s_path = Path(THIS_DIR, '..', '..',
                  'toy_synthetic_data/syn/sdcmicro/k_ano_k_6.csv')
    log = u.SimpleLogger()
    dataset_name = TestDatasetName.national2019
    d = Dataset(s_path, log, dataset_name)

    unique_exact_matches(d.c_target_data, d.c_synthetic_data)