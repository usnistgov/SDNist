"""
Author: Mary Ann Wall
"""
import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def cellchange(df1, df2, quasi, exclude_cols):
    uniques1 = df1.drop_duplicates(subset=quasi, keep=False)
    uniques2 = df2.drop_duplicates(subset=quasi, keep=False)
    matcheduniq = uniques1.merge(uniques2, how='inner', on=quasi)
    allcols = set(df1.columns).intersection(set(df2.columns))
    cols = allcols - set(quasi) - set(exclude_cols)
    return match(matcheduniq, cols), uniques1, uniques2, matcheduniq


def match(df, cols):
    S = pd.Series(data=0, index=df.index)
    for c in cols:
        c_x = c + "_x"
        c_y = c + "_y"
        S = S + (df[c_x] == df[c_y]).astype(int)
    S = (S/len(cols)) * 100
    return S


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=argparse.FileType("r"),
                        help="this is the synthetic dataset (.csv file)")
    parser.add_argument("--groundtruth", type=argparse.FileType("r"),
                        help="this is the original dataset (.csv file)")
    parser.add_argument("--privacy-metric", dest="privacy_metric", type=bool,
                        help="compute the privacy metric")
    parser.add_argument("-x", "--exclude-columns", dest="x", help="list of columns to exclude")
    parser.add_argument("-q", "--quasi", dest="q", help="list of quasi columns ")

    args = parser.parse_args()

    # Load datasets
    dataset = pd.read_csv(args.dataset)
    # groundtruth = pd.read_csv(args.groundtruth, dtypye=dtypes)
    groundtruth = pd.read_csv(args.groundtruth)

    q = args.q
    Qs = q.split(",")
    Qs = [s.strip(" ") for s in Qs]
    x = args.x
    Xs = x.split(",")
    Xs = [s.strip(" ") for s in Xs]
    percents, uniques1, uniques2, matched = cellchange(groundtruth, dataset, Qs, Xs)

    # Histogram
    plt.figure(figsize=(10, 10))
    plt.title(
        'Percentage of raw synthetic records that had an apparent match with groundtruth dataset')
    percents.hist()
    plt.xlim(0, 100)
    plt.show()
