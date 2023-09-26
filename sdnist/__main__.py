import argparse
import pathlib

import pandas as pd

import sdnist
import sdnist.strs as strs
from sdnist.report.__main__ import run, setup
from sdnist.gui import sdnist_gui

if __name__ == "__main__":
    sdnist_gui()
    # input_cnf = setup()
    # run(**input_cnf)
