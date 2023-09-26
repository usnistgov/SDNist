import json
import os
import datetime
import argparse
from pathlib import Path
from typing import Dict

from sdnist.report.common import REPORTS_DIR
import sdnist.load
from sdnist.load import data_challenge_map
from sdnist.report import \
    generate, utility_score, privacy_score,\
    ReportUIData, Dataset, ReportData
from sdnist.report.dataset import data_description
from sdnist.load import TestDatasetName

from sdnist.strs import *
from sdnist.utils import *

from sdnist.load import DEFAULT_DATASET


def run(synthetic_filepath: Path,
        output_directory: Path = REPORTS_DIR,
        dataset_name: TestDatasetName = TestDatasetName.NONE,
        data_root: Path = Path(DEFAULT_DATASET),
        labels_dict: Optional[Dict] = None,
        download: bool = False,
        show_report: bool = True):
    if not output_directory.exists():
        os.mkdir(output_directory)

    outfile = Path(output_directory, 'report.json')
    ui_data = ReportUIData(output_directory=output_directory)
    report_data = ReportData(output_directory=output_directory)
    log = SimpleLogger()
    log.msg('SDNist: Deidentified Data Report Tool', level=0, timed=False)
    log.msg(f'Creating Evaluation Report for Deidentified Data at path: {synthetic_filepath}',
            level=1)

    if not outfile.exists():
        log.msg('Loading Datasets', level=2)
        dataset = Dataset(synthetic_filepath, log, dataset_name, data_root, download)
        ui_data = data_description(dataset, ui_data, report_data, labels_dict)
        log.end_msg()

        # Create scores
        log.msg('Computing Utility Scores', level=2)
        ui_data, report_data = utility_score(dataset, ui_data, report_data, log)
        log.end_msg()

        log.msg('Computing Privacy Scores', level=2)
        ui_data, report_data = privacy_score(dataset, ui_data, report_data, log)
        log.end_msg()

        log.msg('Saving Report Data')
        ui_data.save()
        ui_data = ui_data.data
        report_data.data['created_on'] = ui_data['Created on']
        report_data.save()
        log.end_msg()
    else:
        with open(outfile, 'r') as f:
            ui_data = json.load(f)
    log.end_msg()
    # Generate Report
    generate(ui_data, output_directory, show_report)
    log.msg(f'Reports available at path: {output_directory}', level=0, timed=False,
            msg_type='important')


def setup(deid_files: Optional[List[Path]] = None):
    bundled_datasets = {"MA": TestDatasetName.ma2019,
                        "TX": TestDatasetName.tx2019,
                        "NATIONAL": TestDatasetName.national2019}
    input_cnfs = []
    if deid_files is None:
        parser = argparse.ArgumentParser()
        parser.register('action', 'none', NoAction)
        parser.add_argument("deidentified_dataset", type=argparse.FileType("r"),
                            metavar="PATH_DEIDENTIFIED_DATASET",
                            help="Location of deidentified dataset (csv or parquet file).")
        parser.add_argument("target_dataset_name",
                            metavar="TARGET_DATASET_NAME",
                            choices=[b for b in bundled_datasets.keys()],
                            help="Select name of the target dataset "
                                 "that was used to generated given deidentified dataset.")
        parser.add_argument("--labels",
                            default="",
                            help="This argument is used to add meta-data to help identify which "
                                 "deidentified data was was evaluated in the report. The argument "
                                 "can be a string that is a plain text label for the file, or it "
                                 "can be a file path to a json file containing [label, value] pairs. "
                                 "This labels will be included in the printed report.")
        parser.add_argument("--data-root", type=Path,
                            default=Path(DEFAULT_DATASET),
                            help="Path of the directory "
                                 "to be used as the root for the target datasets.")

        group = parser.add_argument_group(title='Choices for Target Dataset Name')
        group.add_argument('[DATASET NAME]', help='[FILENAME]', action='none')
        for k, v in bundled_datasets.items():
            group.add_argument(str(k), help=f"{v.name}", action='none')

        args = parser.parse_args()
        TARGET_DATA = bundled_datasets[args.target_dataset_name]
        target_name = TARGET_DATA.name

        # check if labels are given by the user
        labels = args.labels

        # if labels are input by the user
        if len(labels):
            # if labels is a path to a json file then load it as dictionary
            if str(labels).endswith('.json'):
                with open(labels, 'r') as fp:
                    labels = json.load(fp)
            # if labels is a string then add label as a value to key named label
            # in a dictionary
            else:
                labels = {'label': labels}
        else:
            labels = None
        # create directory for current report run
        time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')

        this_report_dir = Path(REPORTS_DIR, f'{target_name}_{time_now}')

        input_cnfs.append({
            DATASET_NAME: TARGET_DATA,
            SYNTHETIC_FILEPATH: Path(args.deidentified_dataset.name),
            DATA_ROOT: Path(args.data_root),
            OUTPUT_DIRECTORY: this_report_dir,
            LABELS_DICT: labels,
            DOWNLOAD: True,
        })
    else:
        bundled_datasets = {"ma2019": TestDatasetName.ma2019,
                            "tx2019": TestDatasetName.tx2019,
                            "national2019": TestDatasetName.national2019}
        for deid_file in deid_files:
            # check if labels file exist
            labels_file = Path(deid_file).parent.joinpath(Path(deid_file)
                                                          .name.split('.')[0])
            labels_file = str(labels_file) + '.json'
            if not Path(labels_file).exists():
                continue
            with open(labels_file, 'r') as fp:
                labels = json.load(fp)
            labels = labels['labels']
            time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')
            report_file_name = 'SDNIST_DER_' + Path(deid_file).stem
            TARGET_DATA = bundled_datasets[labels['target dataset']]
            target = bundled_datasets[labels['target dataset']].name
            this_report_dir = Path(Path(deid_file).parent, f'{report_file_name}_{target}_{time_now}')

            input_cnfs.append({
                DATASET_NAME: TARGET_DATA,
                SYNTHETIC_FILEPATH: Path(deid_file),
                DATA_ROOT: Path(DEFAULT_DATASET),
                OUTPUT_DIRECTORY: this_report_dir,
                LABELS_DICT: labels,
                DOWNLOAD: False,
            })

    return input_cnfs


class NoAction(argparse.Action):
    def __init__(self, **kwargs):
        kwargs.setdefault('default', argparse.SUPPRESS)
        kwargs.setdefault('nargs', 0)
        super(NoAction, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pass


if __name__ == "__main__":
    input_cnf = setup()
    run(**input_cnf[0])
