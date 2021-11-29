from collections import defaultdict
from os import error

import pandas as pd


def check_compliance(dataset: pd.DataFrame, schema: dict, raise_error: bool = True):
    errors = defaultdict(list)

    for column, conditions in schema.items():
        if column not in dataset.columns:
            errors[column].append(f"Expected column {column} in data but it was not present")

        if "values" in conditions:
            invalid_values = list(set(dataset[column]) - set(conditions["values"]))

            if invalid_values:
                errors[column].append(f"invalid values '{invalid_values}' (accepted values '{conditions['values']}')")

        if "min" in conditions:
            if dataset[column].min() < conditions["min"]:
                errors[column].append(f"contains values less than minimum ({conditions['min']})")

        if "max" in conditions:
            if dataset[column].max() > conditions["max"]:
                errors[column].append(f"contains values greater than maximum ({conditions['max']})")

    if errors:
        if raise_error:
            message = ";\n ".join(
                f"{column} - {', '.join(column_errors)}" 
                for column, column_errors in errors.items()
            )

            raise ValueError("Dataset does not comply with the schema:\n " + message)

        return False, errors
    
    return True
