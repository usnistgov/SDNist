import argparse
import pathlib

import pandas as pd

import sdnist


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Compute the k-marginal score of a given .csv dataset")
    parser.add_argument("dataset", type=argparse.FileType("r"), help="location of synthetic dataset to score (.csv file)")
    parser.add_argument("--challenge", choices=["census", "taxi"], default="census")
    parser.add_argument("--root", type=pathlib.Path, help="root of target dataset", default=pathlib.Path("data"))
    parser.add_argument("--download", type=bool, default=True, help="download target dataset in 'root' if not present")
    parser.add_argument("--public", type=bool, default=True, help="score on the public or private dataset")
    parser.add_argument("--html", type=bool, default=True, help="output the result to an html page (only available on the ACS public dataset). ")

    args = parser.parse_args()

    # Load target dataset
    target, schema = sdnist.load.load_dataset(
        challenge=args.challenge,
        root=args.root,
        download=args.download,
        public=args.public
    )

    # Load actual dataset
    dtypes = {feature: desc["dtype"] for feature, desc in schema.items()}
    synthetic = pd.read_csv(args.dataset, dtype=dtypes)

    # Compute and print score
    score = sdnist.score(target, synthetic, 
        schema = schema, 
        challenge=args.challenge)

    if args.html:
        score.html(browser=True)