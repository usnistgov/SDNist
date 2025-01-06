"""
Author: Damon Streat
Implementation of DiSCO Metric with slight adjustments for our use case.
Reference: https://arxiv.org/abs/2406.16826
"""

import argparse
import itertools
import matplotlib
import matplotlib.pyplot as plt
import time

from pprint import pprint
from typing import Dict, List, Tuple

import numpy as np
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


def quasi_identifier_column_name(q_identifiers: List[str]) -> str:
    return '|'.join(q_identifiers)


class KDiscoEvaluator:
    """
    DiSCO Metric
    """

    def __init__(self, gt_df: pd.DataFrame, syn_df: pd.DataFrame, stable_identifiers: List[str] = None, k: int = 2) \
            -> None:
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

        # Initialize the results dictionaries
        self.disco_metric_results: Dict[str, Dict[Tuple[str, ...], float]] = {}
        self.dio_metric_results: Dict[str, Dict[Tuple[str, ...], float]] = {}
        self.disco_minus_dio_metric_results: Dict[str, Dict[Tuple[str, ...], float]] = {}

    def compute_disco_OLD(self, quasi_identifiers: List[str], target: str) -> float:
        """
        Computes the DiSCO metric.
        :param target: The target column.
        :param quasi_identifiers: The quasi-identifiers.
        :returns: The calculated DiSCO score for the target column.
        """
        # Compute the quasi-identifiers for the synthetic and ground truth dataframes
        # gt_qid = compute_quasi_identifiers(self.gt_df, quasi_identifiers)
        # qid_colname = f"qid-{'-'.join(sorted(quasi_identifiers))}"
        qid_colname = quasi_identifier_column_name(sorted(quasi_identifiers))

        # Check if the quasi-identifier column already exists in syn_df
        if qid_colname not in self.syn_df.columns:
            # Compute the quasi-identifiers and add them as a new column
            self.syn_df[qid_colname] = compute_quasi_identifiers(self.syn_df, quasi_identifiers)

        # Check if the quasi-identifier column already exists in gt_df
        if qid_colname not in self.gt_df.columns:
            # Compute the quasi-identifiers and add them as a new column
            self.gt_df[qid_colname] = compute_quasi_identifiers(self.gt_df, quasi_identifiers)

        syn_qid_values = set(self.syn_df[qid_colname].values)  # Convert to set to remove duplicates

        # Calculate DiSCO (Disclosive in Synthetic Correct Original)
        disco_count = 0
        for i, gt_record in self.gt_df.iterrows():
            # Get quasi-identifiers in ground truth
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

    def compute_disco(self, quasi_identifiers: List[str], target: str) -> float:
        """
        Computes the DiSCO metric.
        :param target: The target column.
        :param quasi_identifiers: The quasi-identifiers.
        :returns: The calculated DiSCO score for the target column.
        """
        qid_colname = quasi_identifier_column_name(sorted(quasi_identifiers))

        if qid_colname not in self.syn_df.columns:
            self.syn_df[qid_colname] = compute_quasi_identifiers(self.syn_df, quasi_identifiers)

        if qid_colname not in self.gt_df.columns:
            self.gt_df[qid_colname] = compute_quasi_identifiers(self.gt_df, quasi_identifiers)

        # unique_target_colname = f"UTARGET@{target}~{qid_colname}"

        # Group by quasi-identifier, then find the number of unique targets within those groups in the synthetic data.
        syn_unique = self.syn_df.groupby(qid_colname)[target].transform('nunique') == 1
        # self.syn_df[unique_target_colname] = self.syn_df.groupby(qid_colname)[target].transform('nunique')
        # syn_unique_qids = (self.syn_df[[qid_colname, target]]
        #                    .groupby(qid_colname)
        #                    .filter(lambda x: (x.nunique() == 1).all()))

        # Find records where their Quasi-Identifier combination has only one unique target value
        # syn_disclosive_records = self.syn_df[self.syn_df[unique_target_colname] == 1]

        # Filter synthetic data to keep only potentially disclosive records.
        disclosive_in_synthetic = self.syn_df[syn_unique]
        # disclosive_in_synthetic = self.syn_df[self.syn_df[qid_colname] in syn_disclosive_groups[qid_colname]]

        # Get a mapping of quasi-identifiers to values for our disclosive(unique) combinations
        dis_mapping = disclosive_in_synthetic.groupby(qid_colname)[target].unique().to_dict()

        # Filter the ground truth data on disclosive quasi-identifiers found in the synthetic data.
        potential_disclosive_in_gt = self.gt_df[self.gt_df[qid_colname].isin(disclosive_in_synthetic[qid_colname])]

        gt_target_match = potential_disclosive_in_gt.apply(
            lambda x: x[target] == dis_mapping[x[qid_colname]][0], axis=1
        )
        disco_count = gt_target_match[gt_target_match == True].count() if gt_target_match.shape[0] > 0 else 0

        # Merge with ground truth data on their quasi-identifier-target combination to find DiSCO matches.
        # merged_df = pd.merge(self.gt_df[[qid_colname, target]], disclosive_in_synthetic, on=[qid_colname, target],
        #                      how='inner')
        # merged_df = pd.merge(self.gt_df[[qid_colname, target]], syn_disclosive_records, on=[qid_colname, target],
        #                      how='inner')
        # merged_df = pd.merge(self.gt_df[[qid_colname, target]], syn_unique_qids, on=[qid_colname, target],
        #                      how='inner')

        # disco_records = self.gt_df.filter(lambda x: (x[qid_colname] == syn_unique_qids).any())

        # disco_count = merged_df.shape[0]
        # self.syn_df.drop(columns=unique_target_colname)
        return disco_count / self.gt_df.shape[0] if self.gt_df.shape[0] > 0 else 0

    def compute_dio(self, quasi_identifiers: List[str], target: str) -> float:
        """
        Computes the DiO metric.
        :param quasi_identifiers: The quasi-identifiers to use for the calculation.
        :param target: The target column to use for the calculation.
        :returns: The calculated DiO score for the selected dataframes.
        """
        qid_colname = quasi_identifier_column_name(sorted(quasi_identifiers))

        if qid_colname not in self.syn_df.columns:
            self.syn_df[qid_colname] = compute_quasi_identifiers(self.syn_df, quasi_identifiers)

        if qid_colname not in self.gt_df.columns:
            self.gt_df[qid_colname] = compute_quasi_identifiers(self.gt_df, quasi_identifiers)

        # Base case: no data
        if self.gt_df.shape[0] == 0:
            return 0

        # unique_target_colname = f"UTARGET@{target}~{qid_colname}"

        # filter groups where target only has one value (groups that are potentially disclosive)
        disclosive_groups = self.gt_df.groupby(qid_colname)[target].transform('nunique') == 1
        # self.gt_df[unique_target_colname] = self.gt_df.groupby(qid_colname)[target].transform('nunique')

        # filter records on potentially disclosive groups
        disclosive_records = self.gt_df[disclosive_groups]
        # disclosive_records = self.gt_df[self.gt_df[unique_target_colname] == 1]

        # NOTE: This is just giving me the `disclosive_records` again.
        # merge back to original data to identify disclosive records
        # merged_df = pd.merge(self.gt_df[[qid_colname, target]], disclosive_records, on=[qid_colname, target], how='inner')

        # disclosive_count = merged_df.shape[0]
        disclosive_count = disclosive_records.shape[0]

        return disclosive_count / self.gt_df.shape[0]

    def compute_k_disco(self) -> None:
        """
        Computes the k-DiSCO metric.
        :returns: The calculated k-DiSCO score for the selected dataframes.
        """
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

        # --- Precompute QID columns ---
        for target_col in potential_targets:
            other_cols = list(potential_targets - {target_col} - set(stable_ids))
            for qid_combo in itertools.combinations(list(other_cols), self.k):
                qids = tuple(sorted(stable_ids + list(qid_combo)))
                # qid_str = f"qid-{'-'.join(sorted(list(qids)))}"
                qid_str = quasi_identifier_column_name(sorted(list(qids)))
                if qid_str not in self.gt_df.columns:
                    self.gt_df[qid_str] = compute_quasi_identifiers(self.gt_df, list(qids))
                if qid_str not in self.syn_df.columns:
                    self.syn_df[qid_str] = compute_quasi_identifiers(self.syn_df, list(qids))

        total_combinations = len([col for col in self.gt_df.columns if col.startswith('qid')])
        total_computed = 0

        # --- Compute DiSCO, DiO scores ---
        for target_col in potential_targets:
            # Initialize
            self.disco_metric_results[target_col] = {}
            self.dio_metric_results[target_col] = {}
            self.disco_minus_dio_metric_results[target_col] = {}
            other_cols = list(potential_targets - {target_col} - set(stable_ids))
            qid_combinations = itertools.combinations(list(other_cols), self.k)

            if __name__ == '__main__':
                print(f"Computing disco scores for target: {target_col}")
            for i, qid_combo in enumerate(qid_combinations):
                qids = list(stable_ids) + list(qid_combo)
                if __name__ == '__main__':
                    print(f"\t{qids}: ({total_computed} / {total_combinations})")
                    total_computed += 1
                compute_start_time = time.time()
                disco_risk_metric = self.compute_disco(quasi_identifiers=qids, target=target_col)
                dio_risk_metric = self.compute_dio(quasi_identifiers=qids, target=target_col)

                if __name__ == '__main__':
                    print(f"\t\tTook {time.time() - compute_start_time} seconds")
                self.disco_metric_results[target_col][tuple(sorted(qids))] = disco_risk_metric
                self.dio_metric_results[target_col][tuple(sorted(qids))] = dio_risk_metric
                self.disco_minus_dio_metric_results[target_col][tuple(sorted(qids))] = disco_risk_metric - dio_risk_metric

    def average_disco(self) -> float:
        """
        Computes the average disco score for all disco metrics run on the data.
        :return: The average disco score.
        """
        if len(self.disco_metric_results) == 0:
            raise ValueError("No disco metrics have been run.")

        print(
            f"Sum of disco metrics: {sum(disco_val for qid_combo_results in self.disco_metric_results.values() for disco_val in qid_combo_results.values())}")
        print(f"Total number of disco metrics: {sum(len(target) for _, target in self.disco_metric_results.items())}")

        # Sum the disco scores for each target column and divide by number of results
        return sum(disco_val for qid_combo_results in self.disco_metric_results.values()
                   for disco_val in qid_combo_results.values()) / sum(
            len(target) for _, target in self.disco_metric_results.items())

    def average_dio(self) -> float:
        """
        Calculates the average DIO score for the metric results.
        :return: The average DIO score.
        """
        if len(self.dio_metric_results) == 0:
            raise ValueError("No disco metrics have been run.")
        print(
            f"Sum of dio metrics: {sum(dio_val for qid_combo_results in self.dio_metric_results.values() for dio_val in qid_combo_results.values())}")
        print(f"Total number of disco metrics: {sum(len(target) for _, target in self.dio_metric_results.items())}")

        # Sum the disco scores for each target column and divide by number of results
        return sum(dio_val for qid_combo_results in self.dio_metric_results.values()
                   for dio_val in qid_combo_results.values()) / sum(
            len(target) for _, target in self.dio_metric_results.items())

    def compute_disco_minus_dio(self):
        """
        Computes the DiSCO minus DIO score.
        :return: The DiSCO minus DIO score.
        """
        if not self.disco_metric_results:
            raise ValueError("No DiSCO results have been computed.")

        disco_minus_dio_results = {}

        for target, qid_combo_results in self.disco_metric_results.items():
            disco_minus_dio_results[target] = {}
            for qid_combo, disco_val in qid_combo_results.items():
                disco_minus_dio_results[target][qid_combo] = disco_val - self.dio_metric_results[target][qid_combo]
        return disco_minus_dio_results

    def compute_disco_dio_qid_avg(self) -> Dict[str, Dict[str, float]]:
        """
        Computes the average DiSCO minus DIO score for each target.
        :return: A dictionary mapping each target to its average DiSCO minus DIO score.
        """
        # disco_minus_dio_results = self.compute_disco_minus_dio()
        qid_avg_results: Dict[str, Dict[str, float]] = {col: {} for col in self.disco_minus_dio_metric_results.keys()}

        # Compute the average DiSCO minus DIO score for each single quasi-identifier
        for qid in qid_avg_results.keys():
            for target, qid_combo_results in self.disco_minus_dio_metric_results.items():
                if target == qid:
                    continue
                qid_scores = [score for Q, score in qid_combo_results.items() if qid in Q]
                qid_avg_results[qid][target] = sum(qid_scores) / len(qid_scores)
        return qid_avg_results

    def plot_disco_results(self, output_path: str) -> None:
        """
        Plots the DiSCO results as a bar plot.
        :param output_path: The path to save the plot to.
        :param plot_height: The height of the plot.
        :param plot_width: The width of the plot.
        :return:
        """
        data = [{'Target': target, 'QID Combination': str(qid), 'DiSCO Score': score}
                for target, qid_scores in self.disco_metric_results.items() for qid, score in qid_scores.items()]
        df = pd.DataFrame(data)

        avg_disco_per_target = df.groupby("Target")["DiSCO Score"].mean().sort_values(ascending=False)

        plt.figure(figsize=(12, 5), dpi=100)
        plt.bar(x=avg_disco_per_target.index, height=avg_disco_per_target.values, color='orange')
        plt.ylim(top=1)
        plt.title('Average DiSCO Scores for Each Target')
        plt.ylabel('Average DiSCO Score')
        plt.xlabel('Target')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

    def plot_disco_minus_dio_heatmap(self, output_path: str) -> None:
        """
        Creates a 2D heatmap plot of the DiSCO - DiO results for each combination of quasi-identifiers.
        :param output_path: The path to save the heatmap to.
        """
        # Get average of each qid's DiSCO - DiO score per target
        disco_dio_qid_avg = self.compute_disco_dio_qid_avg()
        heatmap_data = pd.DataFrame.from_dict(disco_dio_qid_avg).sort_index(axis=0).sort_index(axis=1)
        heatmap_data.fillna(0, inplace=True)

        # Plot heatmap
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["blue", "orange"])
        plt.figure(figsize=(8, 8), dpi=100)
        heatmap = plt.imshow(heatmap_data.T, cmap=cmap, interpolation='nearest', vmin=-1, vmax=1)
        # heatmap = plt.imshow(heatmap_data.T, cmap=cmap, interpolation='nearest')
        plt.xlabel("Target Feature")
        plt.xticks(range(heatmap_data.shape[1]), heatmap_data.columns)
        plt.ylabel("Quasi-Identifier Feature")
        plt.yticks(range(heatmap_data.shape[0]), heatmap_data.index)
        plt.colorbar(heatmap)
        plt.hlines(y=np.arange(0, heatmap_data.shape[1]) + 0.5, xmin=np.full(heatmap_data.shape[1], 0) - 0.5,
                   xmax=np.full(heatmap_data.shape[1], heatmap_data.shape[0]) - 0.5, lw=0.3, color="black")
        plt.title('Average Quasi-Identifier DiSCO - DiO Score per Target Feature')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()


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
    parser.add_argument(
        "-pn", "--plot-name", type=str, required=False, default='test', help="Name of the graph plot"
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

    # Print results
    print("-" * 20)
    print(f"Average DiSCO Score: {disco.average_disco()}")
    print("---- DiSCO Results ----")
    pprint(disco.disco_metric_results, indent=4)
    print("---- DiO Results ----")
    pprint(disco.dio_metric_results, indent=4)
    print("---- DiSCO - DiO Results ----")
    pprint(disco.disco_minus_dio_metric_results, indent=4)

    disco.plot_disco_minus_dio_heatmap(f"{args.plot_name}-heatmap.png")
    disco.plot_disco_results(f"{args.plot_name}.png")

    # Print differences in plots
    # for target, qid_scores in disco.disco_metric_results.items():
    #     for qid, disco_score in qid_scores.items():
    #         dio_score = disco.dio_metric_results[target][qid]
    #         if dio_score != disco_score:
    #             print(f"DIFFERENCE: {target}-[{qid}]: {disco_score}, {dio_score}")

    print(f"Total Time: {time.time() - start_time}")
