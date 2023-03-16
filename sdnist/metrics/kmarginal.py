from typing import List, Optional
import pandas as pd
from pathlib import Path

from sdnist.report.dataset import Dataset
import sdnist.load as load
import sdnist.utils as utils

def compute_marginal_densities(data, marginals):
    counts = data.groupby(marginals).size()
    return counts / data.shape[0]


class KMarginal:
    """
    [t1, t2, t3, t4] are target densities.   t1 = count / tN
    [s1, s2, s3, s4] are synthetic densities. s1 = count /sN
    Sum(ti) = 1.   Sum (si) = 1
     |(t1 - s1)| + |(t2 - s2)| + |(t3-s3)| + |(t4-s4)|  \in range [0, 2]

    Puma A = (1,2),  Puma B = (3,4)
    total pop of Puma A is: (t1 + t2)*N
    total pop of Puma B is: (t3 + t4)*N

    (|(t1 - s1)| + |(t2 - s2)|) ) * N/pop(A)
    (|(t1 - s1)| + |(t2 - s2)|) ) * N/((t1 + t2)*N).  = scaled PUMA A score
    (|(t1 - s1)| + |(t2 - s2|)  ) * 1/(t1 + t2).
    (|(t1 - s1)| / (t1 + t2)) +  (|(t2 - s2)| / (t1 + t2))


    (|(t3 - s3)| + |(t4 - s4)|) ) * N/pop(B)
    (|(t3 - s3)| + |(t4 - s4)|) ) * N/((t3 + t4)*N).  = scaled PUMA B score
    (|(t3 - s3)| + |(t4 - s4|)  ) * 1/(t3 + t4).
    (|(t3 - s3)| / (t3 + t4)) +  (|(t4 - s4)| / (t3 + t4))
    Problem if s4 giant and t3+t4 tiny

    replace the (|(t3 - s3)| + |(t4 - s4|)) numerator sum with:
    min((t3 + t4), (|(t3 - s3)| + |(t4 - s4| ) )

    Then change the converstion to the 0-1000 score to work as follows
    (1 - avg-density-differences(PUMA A))* 1000

    Instead of what it used to be:
    (2- avg-density-differences(PUMA A))* 1000)

    Because now the max will let you differ is by the size of the whole target data,
    and that means you max out at 1 (note, we should only do this for PUMA,
    because the target population size for every PUMA is reasonable)
    """
    NAME = 'K-Marginal'
    def __init__(self,
                 target_data: pd.DataFrame,
                 deidentified_data: pd.DataFrame,
                 group_features: Optional[List[str]] = None):
        self.td = target_data
        self.deid = deidentified_data
        self.group_features = group_features or []
        self.features = self.td.columns.tolist()
        marg_cols = list(set(self.features).difference(['PUMA', 'INDP']))
        marg_cols = sorted(marg_cols)
        self.marginals = [(f1, f2)
                           for i, f1 in enumerate(marg_cols)
                           for j, f2 in enumerate(marg_cols)
                           if i < j]

    def marginal_pairs(self):
        for _ in self.marginals:
            yield list(_)

    def compute_score(self):
        if len(self.group_features):
            return self._compute_score_grouped()
        else:
            return self._compute_score()

    def marginal_densities(self, data: pd.DataFrame, marginal: List[str]):
        # target data marginal densities
        t_den = compute_marginal_densities(self.td, marginal)
        # deidentified data marginal densities
        s_den = compute_marginal_densities(self.deid, marginal)
        # target and deidentified densities absolute differences
        abs_den_diff = t_den.subtract(s_den, fill_value=0).abs()
        return t_den, s_den, abs_den_diff

    def _compute_score(self):
        # sum total of densities absolute differences over all marginals
        tdds = 0

        # For each 2-marginal find sum of absolute density differences
        for marg in self.marginal_pairs():
            # t_den: target data marginal densities
            # s_den: deidentified data marginal densities
            # abs_den_diff: target and deidentified densities absolute differences
            t_den, s_den, abs_den_diff = self.marginal_densities(self.td, marg)
            # sum of target and deidentified densities absolute differences
            den_diff_sum = abs_den_diff.sum()
            tdds += den_diff_sum

        # find average of overall score and each group feature score
        mean_tdds = tdds/len(self.marginals)
        # convert to NIST 0 - 1000 score range
        self.score = (2 - mean_tdds) * 500
        return self.score

    def _compute_score_grouped(self):
        # sum total of densities absolute differences over all marginals
        tdds = 0
        gf = self.group_features
        group_N = self.td.groupby(gf).size()
        group_tdds = group_N * 0

        # For each 2-marginal find sum of absolute density differences, and
        # for group feature find sum of absolute density differences for each
        # feature value
        for marg in self.marginal_pairs():
            marg = gf + marg
            # t_den: target data marginal densities
            # s_den: deidentified data marginal densities
            # abs_den_diff: target and deidentified densities absolute differences
            t_den, s_den, abs_den_diff = self.marginal_densities(self.td, marg)

            # get sum of abs densities differences for group feature
            group_t_den_sum = t_den.groupby(gf).sum()
            # sum density differences in each group
            group_den_sum = abs_den_diff.groupby(gf).sum()
            # take minimum of target density difference sum and group density difference sum
            group_den_sum = group_t_den_sum.where(group_t_den_sum <= group_den_sum).fillna(group_den_sum)
            # scale back group feature density different sums
            group_den_scaled = (group_den_sum * len(self.td)) / group_N
            # add this marginal's scaled density differences to other marginals aggregate
            group_tdds = group_tdds + group_den_scaled

            # sum of target and deidentified densities absolute differences
            den_diff_sum = abs_den_diff.sum()
            tdds += den_diff_sum

        # find average of overall score and each group feature score
        mean_tdds = tdds/len(self.marginals)
        mean_group_tdds = group_tdds / len(self.marginals)

        # convert to NIST 0 - 1000 score range
        self.scores = (1 - mean_group_tdds) * 1000
        self.score = (2 - mean_tdds) * 500

        return self.score

if __name__ == "__main__":
    THIS_DIR = Path(__file__).parent
    SCH_P = Path(THIS_DIR, '../../diverse_community_excerpts_data/national/na2019.csv')
    S_P = Path(THIS_DIR,
               '../../toy_synthetic_data/syn/teams/LostInTheNoise/national/MWEM_PGM-GirishKumar.csv')

    log = utils.SimpleLogger()
    dataset_name = load.TestDatasetName.national2019
    d = Dataset(S_P, log, dataset_name)

    km = KMarginal(d.d_target_data, d.d_synthetic_data, ['PUMA'])
    km.compute_score()

