import math
from typing import List, Optional
from enum import Enum
import itertools

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn import tree


class ModelType(Enum):
    LogisticRegression = 'logistic_regression'
    DecisionTree = "decision_tree"


class PropensityMSE:
    NAME = 'Propensity Mean Square Error'

    def __init__(self,
                 target: pd.DataFrame,
                 synthetic: pd.DataFrame,
                 model: ModelType = ModelType.LogisticRegression,
                 features: Optional[List[str]] = None,
                 complete: bool = True):
        self.model = model
        self.features = features if features \
            else target.columns.tolist()
        self.target = target[self.features]
        self.synthetic = synthetic[self.features]
        self.complete = complete
        # probability of classifying a sample as belong
        # to the synthetic data set
        self.syn_prob: List[int] = []
        self.score: float = 0  # propensity mean square error score
        # self.one_way_scores: pd.DataFrame = pd.DataFrame()
        self.two_way_scores: pd.DataFrame = pd.DataFrame()

        self.std_score: float = 0  # standardized propensity mean square error score
        # self.std_one_way_scores: pd.DataFrame = pd.DataFrame()
        self.std_two_way_scores: pd.DataFrame = pd.DataFrame()

    def compute_score(self):
        t, s = self.target, self.synthetic

        # compute for all features
        score, std_score = self._pmse(t, s)
        self.score = score
        self.std_score = std_score

        if self.complete:
            # compute for each feature separately
            # f_scores = []  # final scores
            # fs_scores = []  # final standardized scores
            # for f in self.features:
            #     score, std_score = self._pmse(t[[f]], s[[f]])
            #     f_scores.append([f, score])
            #     fs_scores.append([f, std_score])
            # self.one_way_scores = pd.DataFrame(f_scores, columns=["feature", "pmse"])
            # self.std_one_way_scores = pd.DataFrame(fs_scores, columns=['feature', 'spmse'])

            # compute for each combination of two from features
            fim = {f: i for i, f in enumerate(self.features)}  # feature index map
            f_scores = [[0 for _ in self.features]
                        for _ in self.features]
            fs_scores = [[0 for _ in self.features]
                         for _ in self.features]
            for fc in itertools.combinations(self.features, 2):
                f1, f2 = fc
                score, std_score = self._pmse(t[[f1, f2]], s[[f1, f2]])
                i1, i2 = fim[f1], fim[f2]
                f_scores[i1][i2] = score
                fs_scores[i1][i2] = std_score
                if f1 != f2:
                    f_scores[i2][i1] = score
                    fs_scores[i2][i1] = std_score
            self.two_way_scores = pd.DataFrame(f_scores, columns=self.features, index=self.features)
            self.std_two_way_scores = pd.DataFrame(fs_scores, columns=self.features, index=self.features)

    def _pmse(self, t: pd.DataFrame, s: pd.DataFrame):
        t, s = t.copy(), s.copy()
        f = t.columns.tolist()
        # 'i' is an indicator column to indicate either a row
        # is sample from target data (marked with 0) or synthetic data
        # with indicator value of 1.
        t['i'], s['i'] = [0] * t.shape[0], [1] * s.shape[0]

        # Concatenate target and synthetic dataset rows to
        # form one single training dataset
        N = pd.concat([t, s]).reset_index(drop=True)

        if self.model == ModelType.LogisticRegression:
            clf = LogisticRegression(random_state=0)
        else:
            clf = tree.DecisionTreeClassifier()
        print(N.shape, t.shape, s.shape)
        clf.fit(N[f].values, N['i'].values)
        print('fitted')
        pprob = clf.predict_proba(N[f].values)  # prediction probabilities
        syn_prob = np.transpose(pprob)[1]

        # propensity
        N_size = N.shape[0]
        s_size = s.shape[0]  # size of synthetic data

        c = s_size/N_size
        print(syn_prob)
        score = 1/N_size * sum([(_pi - c)**2
                                for _pi in syn_prob])
        print(score, c)
        k = len(t.columns) - 1
        mean = np.mean(syn_prob)

        exp_mean = (k - 1) * ((1 - c)**2) * c / N_size
        stdev_score = math.sqrt(2 * (k - 1)) * ((1 - c) ** 2) * c / N_size

        std_score = (mean - exp_mean) / stdev_score
        print(f"Mean: {mean}", k, exp_mean, stdev_score, std_score)
        return score, std_score
