"""
Author: Damon Streat
Implementation of DiSCO Metric with slight adjustments for our use case.
Reference: https://arxiv.org/abs/2406.16826
"""

import argparse
import itertools
import cProfile
import pstats
import time

from functools import cache
from pprint import pprint
from typing import Dict, List, Tuple

import pandas as pd


# CONSTANTS
DATASET_SIZE_THRESHOLD = 10000

def compute_quasi_identifiers(df: pd.DataFrame, q_identifiers: List[str]) -> pd.Series:
    """
    Computes the quasi-identifiers for a given dataframe.
    :param df: The dataframe to compute the quasi-identifiers for.
    :param q_identifiers: The list of quasi-identifiers.
    :return: A pandas Series with the quasi-identifiers.
    """
    return df[q_identifiers].apply(lambda row: '-'.join(row.values.astype(str)), axis=1)


class KDiscoEvaluator:
    """
    DiSCO Metric
    """

    def __init__(self, gt_df: pd.DataFrame, syn_df: pd.DataFrame, stable_identifiers: List[str], k: int = 2) -> None:
        """
        Initializes the DiSCO metric.
        """
        self.gt_df = gt_df
        self.syn_df = syn_df
        self.stable_identifiers = stable_identifiers
        self.k = k

        # Get the column names
        self.gt_columns = gt_df.columns.tolist()
        self.syn_columns = syn_df.columns.tolist()

        # Initialize the results dictionary
        self.metric_results: Dict[str, Dict[Tuple[str, ...], float]] = {}

    def compute_disco(self, quasi_identifiers: List[str], target: str) -> float:
        """
        Computes the DiSCO metric.
        :param target: The target column.
        :param quasi_identifiers: The quasi-identifiers.
        :returns: The calculated DiSCO score for the target column.
        """
        # Compute the quasi-identifiers for the synthetic and ground truth dataframes
        # gt_qid = compute_quasi_identifiers(self.gt_df, quasi_identifiers)
        qid_colname = '-'.join(sorted(quasi_identifiers))

        # Check if the quasi-identifier column already exists in syn_df
        if qid_colname not in self.syn_df.columns:
            # Compute the quasi-identifiers and add them as a new column
            self.syn_df[qid_colname] = compute_quasi_identifiers(self.syn_df, quasi_identifiers)

        # Check if the quasi-identifier column already exists in gt_df
        if qid_colname not in self.gt_df.columns:
            # Compute the quasi-identifiers and add them as a new column
            self.gt_df[qid_colname] = compute_quasi_identifiers(self.gt_df, quasi_identifiers)

        # syn_qid_series = self.syn_df[qid_colname]
        syn_qid_values = set(self.syn_df[qid_colname].values)  # Convert to set to remove duplicates

        # Calculate DiSCO (Disclosive in Synthetic Correct Original)
        disco_count = 0
        for i, gt_record in self.gt_df.iterrows():
            # Get quasi-identifiers in ground truth
            # qid = '-'.join(gt_record[quasi_identifiers].astype(str).values)
            qid = gt_record[qid_colname]
            if qid in syn_qid_values:
                # Get quasi-identifiers in synthetic
                syn_subset = self.syn_df[self.syn_df[qid_colname] == qid]
                # Check if all targets are the same
                if len(syn_subset) > 0 and len(syn_subset[target].unique()) == 1:
                    # If so, check if target is the same
                    if syn_subset[target].iloc[0] == gt_record[target]:
                        disco_count += 1
        return disco_count / self.gt_df.shape[0] if self.gt_df.shape[0] > 0 else 0

    def compute_disco_optimized(self, quasi_identifiers: List[str], target: str) -> float:
        """
        Computes the DiSCO metric.
        :param target: The target column.
        :param quasi_identifiers: The quasi-identifiers.
        :returns: The calculated DiSCO score for the target column.
        """
        qid_colname = '-'.join(sorted(quasi_identifiers))

        if qid_colname not in self.syn_df.columns:
            self.syn_df[qid_colname] = compute_quasi_identifiers(self.syn_df, quasi_identifiers)

        if qid_colname not in self.gt_df.columns:
            self.gt_df[qid_colname] = compute_quasi_identifiers(self.gt_df, quasi_identifiers)

        # Group by qid and target, then count unique targets
        syn_grouped = self.syn_df.groupby([qid_colname, target]).size().reset_index(name='count')

        # Filter for groups where count is unique (all targets are the same within the qid group)
        syn_unique_targets = syn_grouped.groupby(qid_colname)['count'].nunique() == 1
        syn_unique_targets_qid = syn_unique_targets[syn_unique_targets].index

        # Merge to get the corresponding target values for these unique qids
        syn_valid_targets = syn_grouped[syn_grouped[qid_colname].isin(syn_unique_targets_qid)][[qid_colname, target]]

        # Merge with ground truth to find matches
        merged_df = pd.merge(self.gt_df[[qid_colname, target]], syn_valid_targets, on=[qid_colname, target], how='inner')

        disco_count = len(merged_df)
        return disco_count / self.gt_df.shape[0] if self.gt_df.shape[0] > 0 else 0

    def compute_k_disco(self) -> None:
        """
        Computes the k-DiSCO metric.
        :returns: The calculated k-DiSCO score for the selected dataframes.
        """
        # with cProfile.Profile() as pr:
        # Check that the columns in the synthetic and ground truth dataframes are the same
        all_cols = set(self.gt_df.columns)
        syn_cols = set(self.syn_df.columns)

        stable_ids = [] if self.stable_identifiers is None else self.stable_identifiers  # Initialize stable ids if not provided

        # Check that the columns of the ground truth are at least in the synthetic data
        if not all(x in syn_cols for x in all_cols):
            raise ValueError(f"Ground truth columns {list(all_cols)} not found in synthetic data")

        # Check that our stable identifiers are in the ground truth and synthetic columns
        if not set(stable_ids).issubset(all_cols):
            raise ValueError(f"Stable identifiers {stable_ids} not found in ground truth or synthetic data")

        # Compute the potential targets
        potential_targets = all_cols - set(stable_ids)

        # Check that our stable identifiers are not in the potential targets
        if not set(stable_ids).isdisjoint(potential_targets):
            raise ValueError(f"Stable identifiers {stable_ids} overlap with potential targets {potential_targets}")

        # Check that the potential targets are not empty
        if not potential_targets:
            raise ValueError(f"No potential targets found")

        discos_computed = 0
        total_combos_calculated = 0

        # --- Precompute QID columns ---
        for target_col in potential_targets:
            other_cols = list(potential_targets - {target_col} - set(stable_ids))
            for qid_combo in itertools.combinations(list(other_cols), self.k):
                qids = tuple(sorted(stable_ids + list(qid_combo)))
                qid_str = '-'.join(qids)
                if f'qid_{qid_str}' not in self.gt_df.columns:
                    self.gt_df[f'qid_{qid_str}'] = compute_quasi_identifiers(self.gt_df, list(qids))
                if f'qid_{qid_str}' not in self.syn_df.columns:
                    self.syn_df[f'qid_{qid_str}'] = compute_quasi_identifiers(self.syn_df, list(qids))

        # --- Compute DiSCO scores ---
        for target_col in potential_targets:
            self.metric_results[target_col] = {}
            other_cols = list(potential_targets - {target_col} - set(stable_ids))
            qid_combinations = itertools.combinations(list(other_cols), self.k)
            total_combinations = sum(
                1 for _ in itertools.combinations(list(other_cols) + list(stable_ids), self.k + len(stable_ids)))

            print(f"Computing disco scores for target: {target_col}")
            for i, qid_combo in enumerate(qid_combinations):
                qids = list(stable_ids) + list(qid_combo)
                print(f"\t{qids}: ({i + 1} / {total_combinations})")
                compute_start_time = time.time()
                if self.gt_df.shape[0] > DATASET_SIZE_THRESHOLD:
                    risk_metric = self.compute_disco_optimized(quasi_identifiers=qids, target=target_col)
                else:
                    risk_metric = self.compute_disco(quasi_identifiers=qids, target=target_col)
                print(f"\t\tTook {time.time() - compute_start_time} seconds")
                self.metric_results[target_col][tuple(qids)] = risk_metric
        # for target_col in potential_targets:
        #     self.metric_results[target_col] = {}
        #     other_cols = list(potential_targets - {target_col} - set(stable_ids))
        #
        #     # Generate all combinations of quasi-identifiers
        #     qid_combinations = itertools.combinations(list(other_cols), self.k)
        #
        #     # Compute total number combinations
        #     total_combinations = sum(
        #         1 for _ in itertools.combinations(list(other_cols) + list(stable_ids), self.k + len(
        #             stable_ids)))
        #
        #     # Compute the disco for each combination and save them to results.
        #     print(f"Computing disco scores for target: {target_col}")
        #     for i, qid_combo in enumerate(qid_combinations):
        #         discos_computed += 1
        #         qids = list(stable_ids) + list(qid_combo)  # Set the quasi-identifiers for this combination
        #         print(f"\t{qids}: ({i + 1} / {total_combinations})")
        #         risk_metric = self.compute_disco(quasi_identifiers=qids, target=target_col)
        #         self.metric_results[target_col][tuple(qids)] = risk_metric

        # stats = pstats.Stats(pr)
        # stats.sort_stats('cumtime').print_stats("disco")

    def compute_k_disco_optimize(self) -> None:
        """
        Computes the k-DiSCO metric.
        :returns: The calculated k-DiSCO score for the selected dataframes.
        """
        # Check that the columns in the synthetic and ground truth dataframes are the same
        all_cols = set(self.gt_df.columns)
        syn_cols = set(self.syn_df.columns)

        # Set to save all the combinations of quasi-identifiers we use since they'll be cached.
        all_qid_combos = set()


        stable_ids = [] if self.stable_identifiers is None else self.stable_identifiers  # Initialize stable ids if not provided

        # Check that the columns of the ground truth are at least in the synthetic data
        if not all(x in syn_cols for x in all_cols):
            raise ValueError(f"Ground truth columns {list(all_cols)} not found in synthetic data")

        # Check that our stable identifiers are in the ground truth and synthetic columns
        if not set(stable_ids).issubset(all_cols):
            raise ValueError(f"Stable identifiers {stable_ids} not found in ground truth or synthetic data")

        # Compute the potential targets
        potential_targets = all_cols - set(stable_ids)

        # --- Pre-compute and Store qid ---
        all_qids_combinations = set()
        for target_col in potential_targets:
            other_cols = list(potential_targets - {target_col} - set(stable_ids))
            for qid_combo in itertools.combinations(list(other_cols), self.k):
                qids = tuple(sorted(stable_ids + list(qid_combo)))  # Sort for consistent order
                all_qids_combinations.add(qids)

        # Add qid columns to the original DataFrames
        for qids in all_qids_combinations:
            qid_str = '-'.join(qids)
            self.gt_df[f'qid_{qid_str}'] = compute_quasi_identifiers(self.gt_df, list(qids))
            self.syn_df[f'qid_{qid_str}'] = compute_quasi_identifiers(self.syn_df, list(qids))

        # Check that our stable identifiers are not in the potential targets
        if not set(stable_ids).isdisjoint(potential_targets):
            raise ValueError(f"Stable identifiers {stable_ids} overlap with potential targets {potential_targets}")

        # Check that the potential targets are not empty
        if not potential_targets:
            raise ValueError(f"No potential targets found")

        total_combos_calculated = 0

        for target_col in potential_targets:
            self.metric_results[target_col] = {}
            other_cols = sorted(list(potential_targets - {target_col} - set(stable_ids)))

            # Generate all combinations of quasi-identifiers
            qid_combinations = [combo for combo in itertools.combinations(list(other_cols), self.k)]
            all_qid_combos.add(qid_combinations)
            total_combinations = len(qid_combinations)  # total number combinations
            total_combos_calculated += total_combinations

            # Compute the disco for each combination and save them to results.
            print(f"Computing disco scores for target: {target_col}")
            for i, qid_combo in enumerate(qid_combinations):
                qids = list(stable_ids) + list(qid_combo)  # Set the quasi-identifiers for this combination
                print(f"\t{qids}: ({i + 1} / {total_combinations})")
                risk_metric = self.compute_disco(quasi_identifiers=qids, target=target_col)
                self.metric_results[target_col][tuple(qids)] = risk_metric

    def average_disco(self) -> float:
        """
        Computes the average disco score for all disco metrics run on the data.
        :return: The average disco score.
        """
        if len(self.metric_results) == 0:
            raise ValueError("No disco metrics have been run.")

        print(f"Sum of disco metrics: {sum(disco_val for qid_combo_results in self.metric_results.values()
                   for disco_val in qid_combo_results.values())}")
        print(f"Total number of disco metrics: {sum(len(target) for _, target in self.metric_results.items())}")

        # Sum the disco scores for each target column and divide by number of results
        return sum(disco_val for qid_combo_results in self.metric_results.values()
                   for disco_val in qid_combo_results.values()) / len(self.metric_results)

    @property
    def metric_results(self):
        """
        Returns the metric results.
        """
        return self._metric_results

    @metric_results.setter
    def metric_results(self, value):
        """
        Sets the metric results.
        """
        self._metric_results = value




if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-gt", "--ground-truth", type=str, required=True, help="Ground truth file"
    )
    parser.add_argument(
        "-syn", "--synthetic-data", type=str, required=True, help="Synthetic Data file"
    )
    parser.add_argument(
        "-k", type=int, required=True,
        help="Count of Features to be considered (aside from stable quasi-identifiers)"
    )
    parser.add_argument(
        "-sqi", "--stable-quasi-identifiers", type=str, required=False, nargs='+',
        help="List of Stable Quasi-identifiers"
    )
    args = parser.parse_args()

    start_time = time.time()

    # Read data
    gt = pd.read_csv(args.ground_truth)
    syn = pd.read_csv(args.synthetic_data)

    # Get stable quasi-identifiers
    stables = args.stable_quasi_identifiers if args.stable_quasi_identifiers else []

    # Initialize DiSCO Evaluator
    disco = KDiscoEvaluator(gt, syn, stables, k=args.k)

    # Compute DiSCO
    disco.compute_k_disco()

    # Compute DiSCO
    # avg_DiSCO, DiSCO_scores = compute_k_disco(gt, syn, args.k, stables)

    # Print results
    print("-" * 20)
    print(f"Average DiSCO Score: {disco.average_disco()}")
    pprint(disco.metric_results, indent=4)

    print(f"Total Time: {time.time() - start_time}")

    # print(f"Average DiSCO Score: {avg_DiSCO}")
    # for target, per_qid_score in DiSCO_scores.items():
    #     print(f"Feature: {target}")
    #     for qid, score in per_qid_score.items():
    #         print(f"\t{qid}: {score}")
