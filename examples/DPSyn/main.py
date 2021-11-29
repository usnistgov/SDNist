import argparse
import numpy as np
import yaml
from loguru import logger

from dataloader.DataLoader import *
from dataloader.RecordPostprocessor import RecordPostprocessor
from method.sample_parallel import Sample
from config.path import *

import sdnist


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

    private_data, schema = sdnist.census(public=False)
    print(sdnist.score(private_data, synthetic_data))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", type=str, default="./config/data.yaml",
                        help="specify the path of config file in yaml")

    args = parser.parse_args()
    main()

