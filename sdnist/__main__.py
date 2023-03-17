import argparse
import pathlib

import pandas as pd

import sdnist
import sdnist.strs as strs
from sdnist.report.__main__ import run, setup

if __name__ == "__main__":
    input_cnf = setup()
    run(**input_cnf)
