from typing import Dict, Any, Union
import numpy as np

import sdnist.strs as strs

def get_feature_type(data_dict: Dict, feature: str) -> str:
    f_dict = data_dict[feature]
    if 'min' in f_dict[strs.VALUES] and 'max' in f_dict[strs.VALUES]:
        return strs.CONTINUOUS
    else:
        return strs.CATEGORICAL

def dtype_to_python_type(dtype: str) -> type:
    if dtype in ['int64', 'int32']:
        return int
    elif dtype == 'float64':
        return float
    else:
        return str

def safe_isnan(value: Any):
    try:
        return np.isnan(value)
    except TypeError:
        return False

def is_numeric(s: str) -> bool:
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    if not s:
        return False

    try:
        float(s)  # If this succeeds, s is numeric (int or float, positive or negative)
        return True
    except ValueError:
        return False


def parse_numeric_value(value) -> Union[int, float, str]:
    try:
        float_value = float(value)
        if float_value.is_integer():
            return int(float_value)
        else:
            return float_value
    except (ValueError, TypeError):
        return value

def deduce_code_type(feature: str, data_dict: Dict[str, any]) -> any:
    """
    Deduce code type based on the values.
    """
    values = data_dict[feature].get(strs.VALUES, [])
    code_type = data_dict[feature].get(strs.DTYPE, None)
    is_continuous = 'min' in values and 'max' in values

    # if code_type in ['int64', 'int32', 'float64']:
    #     return dtype_to_python_type(code_type)
    if is_continuous:
        all_types = [type(parse_numeric_value(v)) for v in values.values()]
    else:
        all_types = [type(parse_numeric_value(v)) for v in values
                     if str(v).isnumeric()]

    if len(all_types) == 0:
        return str
    if float in all_types:
        return float
    elif int in all_types:
        return int
    else:
        # since all values are string these
        # all will be converted to ints
        return int

def string_to_numeric(s, ctype: type):
    if ctype not in (int, float):
        raise ValueError("ctype must be either 'int' or 'float'")
    try:
        if ctype == int:
            if '.' not in s:
                return int(s)
            else:
                return int(float(s))
        elif ctype == float:
            return float(s)
    except ValueError:
        pass

    # Return the original string if conversion fails
    return s