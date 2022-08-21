import math
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn import tree
from scipy.stats import ks_2samp


class PropensityMSE:
    NAME = 'Propensity Mean Square Error'
    bins = 100

    def __init__(self,
                 target: pd.DataFrame,
                 synthetic: pd.DataFrame,
                 features: Optional[List[str]] = None):
        self.features = features if features \
            else target.columns.tolist()
        self.target = target[self.features]
        self.synthetic = synthetic[self.features]

        # probability of classifying a sample as belong
        # to the synthetic data set
        self.syn_prob: List[int] = []
        self.pmse_score: float = 0  # propensity mean square error score
        self.ks_score: float = 0  # kolmogorov-smirnov test score
        self.prob_dist = pd.DataFrame()  # sample distribution over propensity bins

    def compute_score(self):
        t, s = self.target, self.synthetic

        # compute for all features
        score = self.pmse(t, s)
        self.score = score
        return self.score

    def pmse(self, t: pd.DataFrame, s: pd.DataFrame):
        t, s = t.copy(), s.copy()
        f = t.columns.tolist()
        # 'i' is an indicator column to indicate either a row
        # is sample from target data (marked with 0) or synthetic data
        # with indicator value of 1.
        t['i'], s['i'] = [0] * t.shape[0], [1] * s.shape[0]

        # Concatenate target and synthetic dataset rows to
        # form one single training dataset
        N = pd.concat([t, s]).reset_index(drop=True)

        clf = tree.DecisionTreeClassifier(max_depth=5)
        clf.fit(N[f].values, N['i'].values)

        pprob = clf.predict_proba(N[f].values)  # prediction probabilities
        syn_prob = np.transpose(pprob)[1]  # probability of being a synthetic sample

        oc = [[0, 0] for _ in range(self.bins)]
        sc = [[0, 0] for _ in range(self.bins)]

        for ir, r in N.iterrows():
            p = round(syn_prob[ir], 2)
            pi = math.floor(p * self.bins)
            pi = pi - 1 if pi == self.bins else pi
            # print(pi)
            if N.iloc[ir]['i'] == 0:
                oc[pi][0] += 1
            else:
                sc[pi][0] += 1
        self.prob_dist = pd.DataFrame([[o[0], s[0]]
                                      for o, s in zip(oc, sc)],
                                      columns=['target samples', 'synthetic samples'],
                                      index=range(self.bins))

        N_size = N.shape[0]
        s_size = s.shape[0]  # size of synthetic data

        c = s_size / N_size

        self.pmse_score = 1 / N_size * sum([(_pi - c) ** 2
                                            for _pi in syn_prob])
        orig_syn_prob = syn_prob[:t.shape[0]]
        syn_syn_prob = syn_prob[t.shape[0]:]
        self.ks_score = ks_2samp(orig_syn_prob, syn_syn_prob)

        return self.pmse_score
