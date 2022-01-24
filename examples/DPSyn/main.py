import argparse
import numpy as np
import yaml
from loguru import logger

from dataloader.DataLoader import *
from dataloader.RecordPostprocessor import RecordPostprocessor
from method.sample_parallel import Sample
from config.path import *

import sdnist


# Warning
# This version is modified so as to pretrain on the private data
# and train on the public data (unlike the original challenge)
# The goal is to use the visualization tools of the public dataset.


def main():
    with open(CONFIG_DATA, 'r') as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)

    # dataloader initialization
    dataloader = DataLoader()
    dataloader.load_data()

    # sample
    eps, delta, sensitivity = 1, 2.5e-4, 7
    logger.info(f'working on eps={eps}, delta={delta}, and sensitivity={sensitivity}')
    synthesizer = Sample(dataloader, eps, delta, sensitivity)
    synthetic_data = synthesizer.synthesize()

    # preprocess
    postprocessor = RecordPostprocessor()
    synthetic_data = postprocessor.post_process(synthetic_data, args.config, dataloader.decode_mapping)
    logger.info("post-processed synthetic data")
    synthetic_data.to_csv("DP_synth.csv") #output saved to working directory
    
    public_data, schema = sdnist.census(root="~/datasets", public=True)
    score = sdnist.score(public_data, synthetic_data, schema)
    print(score)
    score.html(browser=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", type=str, default="./config/data.yaml",
                        help="specify the path of config file in yaml")

    args = parser.parse_args()
    main()

