from typing import Dict
import json
from pathlib import Path

import sdnist.gui.strs as strs

file_path = Path(__file__).parent
cfg_path = Path(file_path, 'res', 'config.json')

algorithms_path = Path(file_path, 'res', 'algorithms.json')
libraries_path = Path(file_path, 'res', 'libraries.json')

if not cfg_path.exists():
    cfg = {
       strs.TEAM_NAME: '',
       strs.MAX_PROCESSES: 1,
       strs.NUMERICAL_METRIC_RESULTS: False,
    }

    with open(cfg_path, 'w') as f:
        json.dump(cfg, f, indent=4)


def load_cfg() -> Dict:
    with open(cfg_path, 'r') as f:
        return json.load(f)


def load_algorithm_names() -> Dict:
    with open(algorithms_path, 'r') as f:
        return json.load(f)


def load_library_names() -> Dict:
    with open(libraries_path, 'r') as f:
        return json.load(f)
