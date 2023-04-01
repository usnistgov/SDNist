import pandas as pd
from pathlib import Path

from sdnist.load import TestDatasetName

from sdnist.report.dataset import Dataset
import sdnist.utils as u

def unique_exact_matches(target_data: pd.DataFrame, deidentified_data: pd.DataFrame):
    td, dd = target_data, deidentified_data
    cols = td.columns.tolist()

    u_td = td.loc[td.groupby(by=cols)[cols[0]].transform('count') == 1, :]
    dd['count'] = dd.groupby(by=cols)[cols[0]].transform('count')

    merged = u_td.merge(dd, how='inner', on=cols, indicator=True)
    # number of unique target records that exactly match in deidentified data
    t_rec_matched = merged.shape[0]
    # number of deidentified records that exactly match in target data
    d_rec_matched = merged['count'].sum()
    # percent of unique target records that exactly match in deidentified data
    perc_t_rec_matched = t_rec_matched/td.shape[0]
    # percent of deidentified records that exactly match in target data
    perc_d_rec_matched = d_rec_matched/dd.shape[0]

    perc_t_rec_matched = u.adaptive_round(perc_t_rec_matched)
    perc_d_rec_matched = u.adaptive_round(perc_d_rec_matched)

    return t_rec_matched, d_rec_matched, perc_t_rec_matched, perc_d_rec_matched

if __name__ == '__main__':
    THIS_DIR = Path(__file__).parent
    s_path = Path(THIS_DIR, '..', '..',
                  'toy_synthetic_data/syn/sdcmicro/k_ano_k_6.csv')
    log = u.SimpleLogger()
    dataset_name = TestDatasetName.national2019
    d = Dataset(s_path, log, dataset_name)

    unique_exact_matches(d.c_target_data, d.c_synthetic_data)