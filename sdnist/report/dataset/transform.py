from typing import Dict
import pandas as pd

def transform(data: pd.DataFrame, schema: Dict):
    # replace categories with codes
    # replace N: NA with -1 for categoricals
    # replace N: NA with mean for numericals
    data = data.copy()
    for c in data.columns.tolist():
        desc = schema[c]
        if "values" in desc:
            if "has_null" in desc:
                null_val = desc["null_value"]
                data[c] = data[c].replace(null_val, -1)
        elif "min" in desc:
            if "has_null" in desc:
                null_val = desc["null_value"]
                nna_mask = data[~data[c].isin(['N'])].index  # not na mask
                if c == 'PINCP':
                    data[c] = data[c].replace(null_val, 9999999)
                    data[c] = pd.to_numeric(data[c]).astype(float)
                elif c == 'POVPIP':
                    data[c] = data[c].replace(null_val, 999)
                    data[c] = pd.to_numeric(data[c]).astype(int)
                else:
                    data[c] = pd.to_numeric(data[c]).astype(int)
        if c == 'PUMA':
            data[c] = data[c].astype(pd.CategoricalDtype(desc["values"])).cat.codes
            if "N" in desc['values']:
                data[c] = data[c].replace(0, -1)
        else:
            data[c] = pd.to_numeric(data[c]).astype(int)

    return data