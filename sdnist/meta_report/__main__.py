import datetime
import os
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import argparse
import json
import shutil

import pandas as pd

from sdnist.meta_report import \
    CorrelationComparison, UniqueExactMatchesComparison, \
    PCAHighlightComparison, LinearRegressionComparison
from sdnist.meta_report.generate import generate
from sdnist.meta_report.index import reports_from_index
from sdnist.meta_report.data_dict import add_data_dict
from sdnist.meta_report.motivation import add_motivation
from sdnist.meta_report.observation import add_observation

from sdnist.report.report_data import DataDescriptionPacket, DatasetType
from sdnist.report import ReportUIData
from sdnist.report.dataset.binning import get_density_bins_description

import sdnist.strs as strs
import sdnist.utils as u


def update_reports_data(reports_data: Dict[str, Tuple]):
    for r_name in reports_data.keys():
        report, report_path = reports_data[r_name]
        data_feats = report[strs.DATA_DESCRIPTION]['features']
        report[strs.DATA_DESCRIPTION]['features'] = [c['Feature Name'] for c in data_feats]
        report[strs.DATA_DESCRIPTION]['columns'] = report[strs.DATA_DESCRIPTION]['deid']['features']
    return reports_data


def add_data_description(reports_data: Dict[str, Tuple], m_ui_data: ReportUIData):
    for r_name, (report, report_path) in reports_data.items():
        data_desc = report[strs.DATA_DESCRIPTION]['deid']
        data_desc['columns'] = data_desc['features']
        data_desc.pop('features')
        desc_pck = DataDescriptionPacket(**data_desc)
        m_ui_data.add_data_description(DatasetType.Synthetic,
                                       desc_pck)


def run(reports_path: List[Path], meta_report_out_dir:
        Path, filters: Dict, filter_keys: List[str],
        data_dict: Dict,
        config_name: str,
        density_bins_description: Dict,
        report_title: str):
    # meta report ui data
    m_ui_data = ReportUIData(output_directory=meta_report_out_dir)
    m_ui_data.add_key_val('title', report_title)
    reports_data = dict()

    CWD = Path.cwd()
    # Store path to the target dataset base directory which is
    # diverse_communities_data_excerpts.
    TARGET_DATA_DIR = Path(CWD, 'diverse_communities_data_excerpts')
    # Store path to all the three datasets: ma2019, tx2019, and national2019
    MA_PATH = Path(TARGET_DATA_DIR, 'massachusetts', 'ma2019.csv')
    TX_PATH = Path(TARGET_DATA_DIR, 'texas', 'tx2019.csv')
    NAT_PATH = Path(TARGET_DATA_DIR, 'national', 'national2019.csv')

    # Set name of the target datasets as constants. We use these
    # later in the notebooks
    MA2019 = 'ma2019'
    TX2019 = 'tx2019'
    NATIONAL2019 = 'national2019'

    # load ma2019 csv into massachusetts dataframe
    ma_df = pd.read_csv(MA_PATH)
    # load tx2019 csv into texas dataframe
    tx_df = pd.read_csv(TX_PATH)
    # load national2019 csv into national dataframe
    nat_df = pd.read_csv(NAT_PATH)

    target_datasets = {
        "ma2019": ma_df,
        "tx2019": tx_df,
        "national2019": nat_df
    }

    for report_path in reports_path:
        rjson = Path(report_path, "report.json")
        if not rjson.exists():
            print('No report.json found in {}'.format(report_path))
            continue
        with open(rjson, 'r') as f:
            report: Dict = json.load(f)
        reports_data[report_path] = (report, report_path)
    label_keys = ['team', 'algorithm name', 'epsilon', 'variant label', 'submission number']
    # print(reports_data.keys())
    report_copies_path = Path(meta_report_out_dir, 'detailed_data_reports')

    for report_path in reports_path:
        print(report_path)
        state = report_path.parts[-2]
        dest = Path(report_copies_path, state, report_path.stem)
        dest = shutil.copytree(report_path, dest)
    shutil.make_archive(str(report_copies_path), 'zip', str(report_copies_path))
    shutil.rmtree(str(report_copies_path))
    # update reports data
    reports_data = update_reports_data(reports_data)

    # retain only filters that are in filter keys
    # filters = {k: v for k, v in filters.items() if k in filter_keys}
    filters = dict()
    add_data_description(reports_data, m_ui_data)

    # Add Report Motivation section
    add_motivation(m_ui_data, config_name)

    args: List[any] = [reports_data, meta_report_out_dir, label_keys,
                       filters, data_dict, target_datasets]
    # correlation comparison
    corr = CorrelationComparison(*args)
    corr.ui_data(m_ui_data)
    # unique exact matches comparison
    uem = UniqueExactMatchesComparison(*args)
    uem.ui_data(m_ui_data)

    # pca msp_n highlights
    pca_h = PCAHighlightComparison(*args)
    pca_h.ui_data(m_ui_data)

    # Linear regression white men
    lr_wm = LinearRegressionComparison('white_men', *args)
    lr_wm.ui_data(m_ui_data)

    # Linear regression black women
    lr_bw = LinearRegressionComparison('black_women', *args)
    lr_bw.ui_data(m_ui_data)

    # add observation
    add_observation(m_ui_data, config_name)

    # add data dictionary
    add_data_dict(data_dict, m_ui_data, density_bins_description)

    m_ui_data.save()

    generate(m_ui_data.data, meta_report_out_dir, False)


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("sdnist_reports_dir",
                        metavar="SDNIST_REPORTS_DIRECTORY",
                        help="Location of sdnist data evaluation reports.")
    args = parser.parse_args()

    meta_reports_dir = Path(Path.cwd(), 'meta_reports')
    reports_dir = Path(args.sdnist_reports_dir)
    data_dict_path = Path(Path.cwd(), 'diverse_communities_data_excerpts', 'data_dictionary.json')
    config_path = Path(Path.cwd(), 'sdnist', 'meta_report', 'configs', 'libraries',
                       'sdv.json')
    config_name = str(config_path.stem)
    time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')

    data_path = Path(Path.cwd(), 'diverse_communities_data_excerpts')

    data_dict = u.read_json(data_dict_path)
    mappings = u.read_json(Path(data_path, 'mappings.json'))
    na_path = Path(data_path, 'national', 'national2019.csv')
    ma_path = Path(data_path, 'massachusetts', 'ma2019.csv')
    tx_path = Path(data_path, 'texas', 'tx2019.csv')

    na_df = pd.read_csv(na_path)
    ma_df = pd.read_csv(ma_path)
    tx_df = pd.read_csv(tx_path)

    df = pd.concat([na_df, ma_df, tx_df])

    density_bins_description = get_density_bins_description(df, data_dict, mappings)
    # path where the meta report of this evaluation instance is stored.
    this_m_report_dir = Path(meta_reports_dir, f'{config_name}')
    # this_m_report_dir = Path(meta_reports_dir, f'meta_report_{time_now}')

    if not this_m_report_dir.exists():
        this_m_report_dir.mkdir(parents=True)

    if not reports_dir.exists():
        raise FileNotFoundError(str(reports_dir))

    # load index csv file
    index_path = Path("crc_acceleration_bundle_1.0",
                       "crc_data_and_metric_bundle_1.1",
                      "index.csv")
    index_df = pd.read_csv(index_path)

    # load config file
    config = u.read_json(config_path)

    filters = config['filters']
    sort_by = config['sort_by']

    title = ""
    if "title" in config:
        title = config["title"]
    filter_keys = ['epsilon']
    reports_path = reports_from_index(index_df, filters, sort_by)
    reports_path = [Path("crc_acceleration_bundle_1.0", "crc_data_and_metric_bundle_1.1", p) for p in reports_path]
    # reports_path = [p for p in reports_dir.iterdir() if p.is_dir()]

    report_title = title
    return {"reports_path": reports_path,
            "meta_report_out_dir": this_m_report_dir,
            "filters": filters,
            "filter_keys": filter_keys,
            "data_dict": data_dict,
            "config_name": config_name,
            "density_bins_description": density_bins_description,
            "report_title": report_title}


if __name__ == "__main__":
    input_cnf = setup()
    run(**input_cnf)
