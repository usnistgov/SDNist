import pandas as pd
import numpy as np
from loguru import logger
import multiprocessing

from method.dpsyn import DPSyn
from lib_dpsyn.view import View


class Sample(DPSyn):

    def synthesize(self) -> pd.DataFrame:
        '''
            decide budget distribution strategy
        '''
        eps_0 = self.sensitivity / 1400
        eps_1 = self.sensitivity / 50
        eps_2 = self.sensitivity / 35
        eps_3 = self.sensitivity / 25

        priv_marginal_config = {}
        priv_split_method = {}
        if self.eps < eps_2:
            # get only PUMA-YEAR(lap)
            logger.info("get only PUMA-YEAR(lap), no total count estimate")
            priv_marginal_config['priv_PUMA_YEAR'] = {'total_eps': self.eps, 'attributes': ['PUMA', 'YEAR']}
            priv_split_method['priv_PUMA_YEAR'] = 'lap'
            sample_data, scoring = 'pub', 'pub'
        else:
            # first try to use eps_0 to get total count of samples
            noisy_total_count = self.data.private_data.shape[0] + np.random.laplace(scale=self.sensitivity / eps_0)
            tau_1 = 1500 * self.sensitivity / noisy_total_count
            tau_2 = 6 * tau_1
            if self.eps < eps_0 + eps_1 + tau_1:
                # get only PUMA-YEAR(lap)
                logger.info(
                    f"get only PUMA-YEAR(lap), total count estimate {noisy_total_count}, tau_1 {tau_1}, tau_2 {tau_2}")
                priv_marginal_config['priv_PUMA_YEAR'] = {'total_eps': self.eps - eps_0, 'attributes': ['PUMA', 'YEAR']}
                priv_split_method['priv_PUMA_YEAR'] = 'lap'
                sample_data, scoring = 'pub', 'pub'
            elif self.eps < eps_0 + eps_1 + tau_2:
                # get PUMA_YEAR(lap) + one way (lap)
                logger.info(
                    f"get only PUMA-YEAR(lap)+ one way (lap), total count estimate {noisy_total_count}, tau_1 {tau_1}, tau_2 {tau_2}")
                x = self.eps - eps_0 - eps_1 - tau_1
                y = np.min([eps_3, eps_1 + x / 2])
                priv_marginal_config['priv_PUMA_YEAR'] = {'total_eps': y,
                                                          'attributes': ['PUMA', 'YEAR']}
                priv_marginal_config['priv_all_one_way'] = {'total_eps': self.eps - eps_0 - y}
                priv_split_method['priv_PUMA_YEAR'] = 'lap'
                priv_split_method['priv_all_one_way'] = 'lap'
                sample_data, scoring = 'dpsyn', '1way'
            else:
                # get PUMA_YEAR(lap) + two way (zcdp)
                logger.info(
                    f"get only PUMA-YEAR(lap)+ two way (zcdp), total count estimate {noisy_total_count}, tau_1 {tau_1}, tau_2 {tau_2}")
                x = self.eps - eps_0 - eps_1 - tau_1
                y = np.min([eps_3, eps_1 + x / 2])
                priv_marginal_config['priv_PUMA_YEAR'] = {'total_eps': y,
                                                          'attributes': ['PUMA', 'YEAR']}
                priv_marginal_config['priv_all_two_way'] = {'total_eps': self.eps - eps_0 - y}
                priv_split_method['priv_PUMA_YEAR'] = 'lap'
                priv_split_method['priv_all_two_way'] = 'gauss'
                sample_data, scoring = 'dpsyn', '2way'

        num_processes = 5
        ''' obtain DP marginals (only place that access priv data other than noisy_total_count) '''
        noisy_puma_year, noisy_marginals = self.obtain_consistent_marginals(priv_marginal_config, priv_split_method)

        '''
            generate data
            1. when eps is sufficiently large (eps>=0.2), call the parent class (DPSyn)'s method with fixed_n=10000
            2. when eps is small (e.g. eps<0.2), sample from pub
            self.obtain_consistent_marginals() already got the noisy marginals and stored them in self.attrs_view_dict
            self.obtain_consistent_marginals() also built other data structures
        '''
        if sample_data == 'dpsyn':
            logger.info("DPsyn generate candidate samples")
            init_data = super().internal_synthesize(noisy_puma_year, fixed_n=10000)
            init_data = init_data.drop('iteration', axis=1)
            init_data = init_data.values
        else:
            logger.info(f'eps {self.eps}, sampling from pub data')
            init_data = self.data.public_data.sample(n=int(10000)).values

        attrs = self.data.obtain_attrs()

        '''
            calculate weights based on number of attributes in marginals
        '''
        weights = {}
        # generate weights for marginals
        for cur_attrs in self.attrs_view_dict.keys():
            attrs_info = self.data.get_marginal_grouping_info(cur_attrs)
            weight = 1
            for attr, sub_attrs in attrs_info.items():
                weight *= len(sub_attrs)
            weights[cur_attrs] = weight

        '''
            decide which marginals will be used in scoring in sampling
        '''
        if scoring is None or scoring == 'pub':
            logger.info("using pub 2-way as scoring marginals for sampling...")
            scoring_marginals = self.data.generate_all_two_way_marginals_except_PUMA_YEAR(self.data.public_data)
        elif scoring == '1way':
            # 1 way marginals are not consistent
            logger.info("using noisy 1-way as scoring marginals for sampling...")
            # noisy_marginals has only 1-ways
            scoring_marginals = {}
            for key, view in self.attrs_view_dict.items():
                if key in noisy_marginals:
                    scoring_marginals[key] = view
        elif scoring == '2way':
            # 2-way marginals are consistent
            logger.info("using consistent 2-way as scoring marginals for sampling...")
            # noisy_marginals has only 2-ways
            scoring_marginals = {}
            for key, view in self.attrs_view_dict.items():
                if key in noisy_marginals:
                    scoring_marginals[key] = view
        else:
            raise NotImplementedError

        '''
            only generate datasets for PUMA-YEAR with different size in 100s
        '''
        if self.eps < self.sensitivity / 35:
            # if eps is too small, round puma year to cloest 50
            rounded_puma_year = (np.round(noisy_puma_year / 10) * 10).astype(int)
        else:
            rounded_puma_year = noisy_puma_year.round(-2).astype(np.int)
        rounded_puma_year[rounded_puma_year < 300] = 300
        logger.info(f'sampling for sizes {np.unique(rounded_puma_year)}')

        ''' sample for the largest PUMA-YEAR size'''
        n = np.max(np.unique(rounded_puma_year))
        splited_data = np.split(init_data, num_processes)
        grouped_params = zip(splited_data, [scoring_marginals] * num_processes, [weights] * num_processes,
                             [int(n / num_processes)] * num_processes, [int(n / num_processes / 3)] * num_processes,
                             [self.attrs_view_dict] * num_processes)
        with multiprocessing.Pool(processes=num_processes) as pool:
            sub_set = pool.imap(self.map_sample, grouped_params)
            sample_data = list(sub_set)
        total_data = np.concatenate(sample_data, axis=0)
        logger.info("largest PUMA-YEAR sampling finish")

        ''' parallel sampling for each unique PUMA-YEAR sizes'''
        syn_data_count = {}
        num_sizes = len(np.unique(rounded_puma_year))
        grouped_params = zip([np.copy(total_data)] * num_sizes, [scoring_marginals] * num_sizes, [weights] * num_sizes,
                             np.unique(rounded_puma_year), [int(n / 20)] * num_sizes,
                             [self.attrs_view_dict] * num_sizes)
        with multiprocessing.Pool(processes=num_processes) as pool:
            sub_set = pool.imap(self.map_sample, grouped_params)
            sample_data = list(sub_set)
        for d in sample_data:
            syn_data_count[d.shape[0]] = d

        ''' assign samples to each PUMA-YEAR '''
        syn_df_list = []
        for puma, puma_row in rounded_puma_year.iterrows():
            for year_i, cell_count in enumerate(puma_row):
                # logger.info(f'=========== PUMA: {puma} YEAR: {year_i}, size:{cell_count} =================')
                tmp = np.copy(syn_data_count[cell_count])
                tmp = pd.DataFrame(tmp, columns=attrs)
                tmp['PUMA'] = puma
                tmp['YEAR'] = year_i
                syn_df_list.append(tmp)
        syn_pd = pd.concat(syn_df_list, ignore_index=True)
        return syn_pd

    '''
        parallel version of sampling
    '''
    @staticmethod
    def map_sample(grounped) -> np.ndarray:
        assert len(grounped) == 6
        init_data, target_marginals, weights, n, T, attrs_view_dict= grounped
        if n == init_data.shape[0]:
            return init_data
        ''' split candidate records into two parts, keep replacing records in D with R '''
        D = np.copy(init_data[:n, :])
        R = np.copy(init_data[n:, :])
        early_stopping_threshold = 0.0001

        pre_l1_error = len(target_marginals) * 2
        for i in range(T):
            D_scores = np.zeros(D.shape[0])
            R_scores = np.zeros(R.shape[0])
            l1_error = 0
            for cur_attrs, target_marginal in target_marginals.items():
                view = attrs_view_dict[cur_attrs]
                syn_marginal = view.count_records_general(D)
                if isinstance(target_marginal, pd.DataFrame):
                    target_marginal = np.copy(target_marginal.values.flatten())
                elif isinstance(target_marginal, View):
                    target_marginal = target_marginal.count
                target_marginal = target_marginal / np.sum(target_marginal) * np.sum(syn_marginal)
                l1_error += Sample._simple_l1(syn_marginal, target_marginal)

                under_cell_indices = np.where(syn_marginal < target_marginal - 1)[0]
                over_cell_indices = np.where(syn_marginal > target_marginal + 1)[0]

                # compute D_score and R_score
                for data, scores in zip([D, R], [D_scores, R_scores]):
                    # for cell_indices in [over_cell_indices, under_cell_indices]:
                    encode_records = np.matmul(data[:, view.attributes_index], view.encode_num)

                    scores[np.in1d(encode_records, over_cell_indices)] += weights[cur_attrs]
                    scores[np.in1d(encode_records, under_cell_indices)] -= weights[cur_attrs]

            # reverse R_score
            R_scores = -1 * R_scores

            D_scores_sort_index = np.argsort(D_scores)
            R_scores_sort_index = np.argsort(R_scores)
            ''' add randomness if multiple highest'''
            d_i = Sample._sampled_largest_if_tie(D_scores, D_scores_sort_index)
            r_i = Sample._sampled_largest_if_tie(R_scores, R_scores_sort_index)

            tmp = np.copy(R[R_scores_sort_index[-r_i], :])
            R[R_scores_sort_index[-r_i], :] = np.copy(D[D_scores_sort_index[-d_i], :])
            D[D_scores_sort_index[-d_i], :] = tmp

            ''' check early stop '''
            if pre_l1_error - l1_error < early_stopping_threshold:
                logger.info(f' ==== EARLY STOP at round {i + 1}/{T}, threshold: {early_stopping_threshold} ')
                break
            else:
                pre_l1_error = l1_error
        return D

    @staticmethod
    def _simple_l1(m1, m2):
        normalize_m1 = m1 / np.sum(m1)
        normalize_m2 = m2 / np.sum(m2)
        return np.sum(np.abs(normalize_m1 - normalize_m2))

    @staticmethod
    def _sampled_largest_if_tie(scores, scores_sort_index):
        i = 1
        while i < len(scores) and scores[scores_sort_index[-i]] == scores[scores_sort_index[-i - 1]]:
            i += 1
        # logger.info(f"i {i}")
        i = np.random.randint(low=1, high=i + 1)
        return i