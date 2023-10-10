#  Get From Resources Here
from typing import Optional, Union, Dict
from pathlib import Path
import json

RES_DIR_PATH = Path(__file__).parent
lbl_dfn_path = Path(RES_DIR_PATH, 'index_definition.json')
algorithms_path = Path(RES_DIR_PATH, 'algorithms.json')
libraries_path = Path(RES_DIR_PATH, 'libraries.json')


def get_index_definition(label_name: Optional[str] = None) -> \
        Optional[Union[Dict, str]]:
    """
    Get index definition from resources. If label_name is None
    return all index definition. Otherwise, return string definition of
    label_name.
    :param label_name: name of the label in index file

    :return: All index definition or string definition of given label_name
    """

    if not lbl_dfn_path.exists():
        return None

    with open(lbl_dfn_path, 'r') as f:
        lbl_dfn = json.load(f)

    if label_name is None:
        return lbl_dfn
    else:
        dfn = lbl_dfn[label_name]
        if isinstance(dfn, list):
            return '\n'.join(dfn)
        return dfn


def load_algorithm_names() -> Dict:
    with open(algorithms_path, 'r') as f:
        return json.load(f)


def load_library_names() -> Dict:
    with open(libraries_path, 'r') as f:
        return json.load(f)


