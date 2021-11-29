import random
from pathlib import Path

import pandas as pd
import numpy as np

from tqdm import tqdm

from sdnist.challenge.submission import Model, run

class BaselineModel(Model):
    def train(self, private_dataset: pd.DataFrame, schema: dict, eps: float):
        self.schema = schema
        self.data = private_dataset

    def simulate_row(self):
        """ Naively create a valid row by picking random but valid values using schema. """
        row = {}
        for column, conditions in self.schema.items():
            value = 0
            if "values" in conditions:
                value = random.choice(conditions["values"])
            elif "min" in conditions:
                value = random.randint(conditions["min"], conditions["max"])
            elif column in {"INCTOT", "INCWAGE", "INCEARN"}:
                value = random.randint(0, 60_000)
            row[column] = value

        return row

    def generate(self, n: int, eps: float):
        n = 20000

        dtype = [(name, self.schema[name]["dtype"]) for name in self.schema]
        data = np.empty(shape=n, dtype=dtype)
        df = pd.DataFrame(data)

        for i in tqdm(range(n), desc="Generation"):
            df.loc[i] = self.simulate_row()

        return df


if __name__ == "__main__":
    model = BaselineModel()
    run(model, challenge="census")