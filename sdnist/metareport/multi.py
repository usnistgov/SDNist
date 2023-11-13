import datetime
import os
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import argparse
import json
import shutil

import pandas as pd

from sdnist.metareport import \
    CorrelationComparison, UniqueExactMatchesComparison, \
    PCAHighlightComparison, LinearRegressionComparison
from sdnist.metareport.generate import generate
from sdnist.metareport.index import reports_from_index
from sdnist.metareport.__main__ import run
from sdnist.metareport.data_dict import add_data_dict
from sdnist.metareport.motivation import add_motivation
from sdnist.metareport.observation import add_observation

from sdnist.report.report_data import DataDescriptionPacket, DatasetType
from sdnist.report import ReportUIData
from sdnist.report.dataset.binning import get_density_bins_description

import sdnist.strs as strs
import sdnist.utils as u


if __name__ == "__main__":
    reports_dir = Path("crc_acceleration_bundle_1.0",
                       "data_and_metric_archive",
                       "deid_data")
    metareports_dir = Path("crc_acceleration_bundle_1.0",
                            "metric_report")
    reports_dir = reports_dir

    data_dict_path = Path(Path.cwd(), 'diverse_communities_data_excerpts', 'data_dictionary.json')

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

    if not reports_dir.exists():
        raise FileNotFoundError(str(reports_dir))

    index_path = Path("crc_acceleration_bundle_1.0",
                       "data_and_metric_archive",
                      "index.csv")
    # load index csv file
    index_df = pd.read_csv(index_path)

    # config_paths = ["geneticsd.json", "lostinthenoise.json", "mostlyai.json",
    #                 "rsynthpop.json", "sarussdg.json", "sdcmicro.json",
    #                 "sdv.json", "smartnoise.json", "subsample.json",
    #                 "synthcity.json", "tumult.json"]
    config_paths = ["subsample.json"]
    runs = []
    for cname in config_paths:
        config_path = Path(Path.cwd(), 'sdnist', 'metareport',
                           'configs', 'libraries',
                           cname)
        this_m_report_dir = Path(metareports_dir, f'{cname[:-5]}')
        if not this_m_report_dir.exists():
            this_m_report_dir.mkdir(parents=True)
        config_name = str(config_path.stem)
        # load config file
        config = u.read_json(config_path)

        filters = config['filters']
        sort_by = config['sort_by']

        title = ""
        if "title" in config:
            title = config["title"]
        filter_keys = ['epsilon']
        reports_path = reports_from_index(index_df, filters, sort_by)
        reports_path = [Path(p) for p in reports_path]
        # reports_path = [p for p in reports_dir.iterdir() if p.is_dir()]
        print(reports_path)

        report_title = title
        runs.append({"reports_path": reports_path,
                "metareport_out_dir": this_m_report_dir,
                "filters": filters,
                "filter_keys": filter_keys,
                "data_dict": data_dict,
                "config_name": config_name,
                "density_bins_description": density_bins_description,
                "report_title": report_title})
        run(**runs[-1])


