import copy
import multiprocessing as mp
from typing import List, Tuple, Dict, KeysView

import numpy as np
import pandas as pd
from loguru import logger
from numpy import linalg as LA

from lib_dpsyn.consistent import Consistenter
from lib_dpsyn.record_synthesizer import RecordSynthesizer
from lib_dpsyn.view import View
from method.synthesizer import Synthesizer


class DPSyn(Synthesizer):
    synthesized_df = None
    update_iterations = 60

    attrs_view_dict = {}
    onehot_view_dict = {}

    attr_list = []
    domain_list = []
    attr_index_map = {}

    Attrs = List[str]
    Domains = np.ndarray
    Marginals = Dict[Tuple[str], np.array]
    Clusters = Dict[Tuple[str], List[Tuple[str]]]

    d = None

    def obtain_consistent_marginals(self, priv_marginal_config, priv_split_method):
        # marginals are specified by a dict from attribute tuples to frequency (pandas) tables
        pub_marginals = self.data.generate_all_pub_marginals()
        noisy_marginals = self.get_noisy_marginals(priv_marginal_config, priv_split_method)

        num_synthesize_records = np.mean([np.sum(x.values) for _, x in noisy_marginals.items()]).round().astype(np.int)
        noisy_puma_year = noisy_marginals[frozenset(['PUMA', 'YEAR'])]
        del noisy_marginals[frozenset(['PUMA', 'YEAR'])]

        self.attr_list = self.data.obtain_attrs()
        self.domain_list = np.array([len(self.data.encode_schema[att]) for att in self.attr_list])
        self.attr_index_map = {att: att_i for att_i, att in enumerate(self.attr_list)}

        # views are wrappers of marginals with additional functions for consistency
        pub_onehot_view_dict, pub_attr_view_dict = self.construct_views(pub_marginals)
        noisy_onehot_view_dict, noisy_attr_view_dict = self.construct_views(noisy_marginals)

        # all_views is one-hot to view dict, views_dict is attribute to view dict
        # they have different format to satisfy the needs of consistenter and synthesiser
        self.onehot_view_dict, self.attrs_view_dict = self.normalize_views(
            pub_onehot_view_dict,
            pub_attr_view_dict,
            noisy_attr_view_dict,
            self.attr_index_map,
            num_synthesize_records)

        consistenter = Consistenter(self.onehot_view_dict, self.domain_list)
        consistenter.consist_views()

        # consistenter uses unnormalized counts; after consistency, synthesizer uses normalized counts
        for _, view in self.onehot_view_dict.items():
            view.count /= sum(view.count)

        return noisy_puma_year, noisy_marginals


    def synthesize(self, fixed_n=0) -> pd.DataFrame:
        noisy_puma_year = self.obtain_consistent_marginals()

        # find clusters for synthesize; a cluster is a set of marginals closely connected
        # here we do not cluster and use all marginals as a single cluster
        clusters = self.cluster(self.attrs_view_dict)

        # target_marginals = self.data.generate_all_two_way_marginals_except_PUMA_YEAR(self.data.private_data)
        # pub_marginals = self.data.generate_all_pub_marginals()
        # self.calculate_l1_errors_v2(pub_marginals, self.attrs_view_dict, target_marginals, self.data.private_data)

        self.synthesize_records_PUMA_YEAR(noisy_puma_year, clusters, fixed_n)
        # self.synthesize_records_numbers(noisy_puma_year, clusters, fixed_n)

        return self.synthesized_df

    # synthesize for each possible number
    # then for each puma-year, we just duplicate the appropriate synthesized data
    def synthesize_records_numbers(self, puma_year: pd.DataFrame, clusters: Clusters, fixed_n: int):
        interval = 100
        puma_year = puma_year.round(interval).astype(np.int)
        details = False
        cell_count_max = puma_year.max().max()
        cell_count_min = puma_year.min().min()
        cell_count_min = cell_count_max - 100

        singleton_views = self.obtain_singleton_views(self.attrs_view_dict)

        for cluster_attrs, list_marginal_attrs in clusters.items():
            attrs_index_map = {attrs: index for index, attrs in enumerate(list_marginal_attrs)}

            pool = mp.Pool(mp.cpu_count())
            # pool = mp.Pool(1)
            manager = mp.Manager()
            self.d = manager.list([])

            counts = range(cell_count_min, cell_count_max, interval)
            for count_i, cell_count in enumerate(counts):
                logger.info(f"working on puma-year: {count_i + 1}/{len(counts)}")
                pool.apply_async(self.syn_puma_year, args=(
                count_i, 0, cell_count, attrs_index_map, singleton_views, list_marginal_attrs, details),
                                 callback=self.log_result)
            pool.close()
            pool.join()

        syn_df_list = []
        for puma, puma_row in puma_year.iterrows():
            for year_i, cell_count in enumerate(puma_row):
                for df in self.d:
                    if df.shape[0] == cell_count:
                        tmp = copy.deepcopy(df)
                        tmp['PUMA'] = puma
                        tmp['YEAR'] = year_i
                        syn_df_list.append(tmp)
        self.synthesized_df = pd.concat(syn_df_list, ignore_index=True)

    # synthesize for each combination of puma-year because the final scoring is on puma-year
    def synthesize_records_PUMA_YEAR(self, puma_year: pd.DataFrame, clusters: Clusters, fixed_n: int):
        if fixed_n:
            puma_year = pd.DataFrame([[fixed_n]])
            details = True
        else:
            puma_year = puma_year.round().astype(np.int)
            details = False

        for cluster_attrs, list_marginal_attrs in clusters.items():
            logger.info("synthesizing for %s" % (cluster_attrs,))

            attrs_index_map = {attrs: index for index, attrs in enumerate(list_marginal_attrs)}

            singleton_views = self.obtain_singleton_views(self.attrs_view_dict)

            if fixed_n:
                for puma, puma_row in puma_year.iterrows():
                    for year_i, cell_count in enumerate(puma_row):
                        self.synthesized_df = self.syn_puma_year(puma, year_i, cell_count, attrs_index_map,
                                                                 singleton_views, list_marginal_attrs, details)
            else:
                pool = mp.Pool(mp.cpu_count())
                # pool = mp.Pool(1)
                manager = mp.Manager()
                self.d = manager.list([])
                for puma, puma_row in puma_year.iterrows():
                    for year_i, cell_count in enumerate(puma_row):
                        logger.info(f"working on puma-year: {puma + 1}/{len(puma_year)}-{year_i + 1}/{len(puma_row)}")
                        pool.apply_async(self.syn_puma_year, args=(
                            puma, puma_year, year_i, puma_row, cell_count, attrs_index_map, singleton_views,
                            list_marginal_attrs, details), callback=self.log_result)
                pool.close()
                pool.join()
                self.synthesized_df = pd.concat(self.d, ignore_index=True)
                logger.info(f'finished with a list of {len(self.d)} dataframes')
            logger.info(f'the final dataframe size is {self.synthesized_df.shape}')

    def syn_puma_year(self, puma, year, cell_count, attrs_index_map, singleton_views, list_marginal_attrs, details):
        cur_syn_df = None
        synthesizer = RecordSynthesizer(self.attr_list, self.domain_list, cell_count)
        synthesizer.initialize_records(list_marginal_attrs, singleton_views=singleton_views)

        for update_iteration in range(self.update_iterations + 1):

            synthesizer.alpha = 1.0 * 0.84 ** (update_iteration // 20)
            error_sorted_attrs_list = synthesizer.update_order(update_iteration, self.attrs_view_dict,
                                                               list_marginal_attrs)

            for cur_attrs in error_sorted_attrs_list:
                attrs_i = attrs_index_map[cur_attrs]
                view = self.attrs_view_dict[cur_attrs]

                synthesizer.track_error(view, attrs_i)
                synthesizer.update_records_prepare(view)
                synthesizer.determine_throw_indices()
                synthesizer.handle_zero_cells(view)
                synthesizer.update_records(view, update_iteration)
                synthesizer.track_error(view, attrs_i)

            if update_iteration % 20 == 0 and details:
                tmp_df = synthesizer.df.copy()
                tmp_df['iteration'] = update_iteration
                if cur_syn_df is None:
                    cur_syn_df = tmp_df
                else:
                    cur_syn_df = cur_syn_df.append(tmp_df, ignore_index=True)
                logger.info(update_iteration)

                if update_iteration == self.update_iterations:
                    # target_marginals = self.data.generate_all_two_way_marginals_except_PUMA_YEAR(self.data.private_data)
                    # T_M, T_S, M_S = self.calculate_l1_errors(synthesizer.records, target_marginals, self.attrs_view_dict)
                    # logger.success(f'L1 errors of 2-way: T_M = {T_M}, T_S = {T_S}, M_S = {M_S}')

                    # target_marginals = self.data.generate_all_one_way_marginals_except_PUMA_YEAR(self.data.private_data)
                    # T_M, T_S, M_S = self.calculate_l1_errors(synthesizer.records, target_marginals, self.attrs_view_dict)
                    # logger.success(f'L1 errors of 1-way: T_M = {T_M}, T_S = {T_S}, M_S = {M_S}')
                    pass
        if cur_syn_df is None:
            cur_syn_df = synthesizer.df
        else:
            cur_syn_df.append(synthesizer.df)
        cur_syn_df.loc[:, 'PUMA'] = puma
        cur_syn_df.loc[:, 'YEAR'] = year
        return cur_syn_df

    @staticmethod
    def calculate_l1_errors(records, target_marginals, attrs_view_dict):
        l1_T_Ms = []
        l1_T_Ss = []
        l1_M_Ss = []

        for cur_attrs, target_marginal_pd in target_marginals.items():
            view = attrs_view_dict[cur_attrs]
            syn_marginal = view.count_records_general(records)
            target_marginal = target_marginal_pd.values.flatten()

            T = target_marginal / np.sum(target_marginal)
            M = view.count
            S = syn_marginal / np.sum(syn_marginal)

            l1_T_Ms.append(LA.norm(T - M, 1))
            l1_T_Ss.append(LA.norm(T - S, 1))
            l1_M_Ss.append(LA.norm(M - S, 1))

        return np.mean(l1_T_Ms), np.mean(l1_T_Ss), np.mean(l1_M_Ss)

    @staticmethod
    def normalize_views(pub_onehot_view_dict: Dict, pub_attr_view_dict, noisy_view_dict, attr_index_map, num_synthesize_records) -> Tuple[Dict, Dict]:
        pub_weight = 0.00
        noisy_weight = 1 - pub_weight

        for key, view in pub_onehot_view_dict.items():
            if noisy_view_dict:
                view.weight_coeff = 0.01
                # need to first calculate (num_synthesize_records / np.sum(view.count)), otherwise have numerical problems
                view.count = view.count * (num_synthesize_records / np.sum(view.count))
            else:
                if not np.sum(view.count) == np.sum(list(pub_onehot_view_dict.values())[0].count):
                    raise ValueError(
                        f'view sizes do not match; maybe a data reading problem (current key: {key}, sum: {np.sum(view.count)}')
                view.count = view.count.astype(np.float)

        views_dict = pub_attr_view_dict
        onehot_view_dict = pub_onehot_view_dict
        for view_att, view in noisy_view_dict.items():
            if view_att in views_dict:
                views_dict[view_att].count = pub_weight * pub_attr_view_dict[view_att].count + noisy_weight * view.count
                views_dict[view_att].weight_coeff = pub_weight * pub_attr_view_dict[
                    view_att].weight_coeff + noisy_weight * view.weight_coeff
            else:
                views_dict[view_att] = view
                view_onehot = DPSyn.one_hot(view_att, attr_index_map)
                onehot_view_dict[tuple(view_onehot)] = view
        return onehot_view_dict, views_dict

    @staticmethod
    def obtain_singleton_views(attrs_view_dict):
        singleton_views = {}
        for cur_attrs, view in attrs_view_dict.items():
            # puma and year won't be there because they only appear together (size=2)
            if len(cur_attrs) == 1:
                singleton_views[cur_attrs] = view
        return singleton_views

    def construct_views(self, marginals: Marginals) -> Tuple[Dict, Dict]:
        onehot_view_dict = {}
        attr_view_dict = {}

        for marginal_att, marginal_value in marginals.items():
            view_onehot = DPSyn.one_hot(marginal_att, self.attr_index_map)
            view = View(view_onehot, self.domain_list)
            view.count = marginal_value.values.flatten()

            onehot_view_dict[tuple(view_onehot)] = view
            attr_view_dict[marginal_att] = view

            if not len(view.count) == view.domain_size:
                raise Exception('no match')

        return onehot_view_dict, attr_view_dict

    def log_result(self, result):
        self.d.append(result)

    @staticmethod
    def build_attr_set(attrs: KeysView[Tuple[str]]) -> Tuple[str]:
        attrs_set = set()

        for attr in attrs:
            attrs_set.update(attr)

        return tuple(attrs_set)

    # simple clustering: just build the data structure; not doing any clustering
    def cluster(self, marginals: Marginals) -> Clusters:
        clusters = {}
        keys = []
        for marginal_attrs, _ in marginals.items():
            keys.append(marginal_attrs)

        clusters[DPSyn.build_attr_set(marginals.keys())] = keys
        return clusters

    @staticmethod
    def one_hot(cur_att, attr_index_map):
        cur_view_key = [0] * len(attr_index_map)
        for attr in cur_att:
            cur_view_key[attr_index_map[attr]] = 1
        return cur_view_key

    # synthesize cluster by cluster: the general function, not used for now
    # (we have a graph where nodes represent attributes and edges represent marginals,
    #  it helps in terms of running time and accuracy if we do it cluster by cluster)
    def synthesize_records(self, attrs: Attrs, domains: Domains, clusters: Clusters, num_synthesize_records: int):
        for cluster_attrs, list_marginal_attrs in clusters.items():
            logger.info("synthesizing for %s" % (cluster_attrs,))

            # singleton_views = {attr: self.attr_view_dict[frozenset([attr])] for attr in attrs}
            singleton_views = {}
            for cur_attrs, view in self.attrs_view_dict.items():
                if len(cur_attrs) == 1:
                    singleton_views[cur_attrs] = view

            synthesizer = RecordSynthesizer(attrs, domains, num_synthesize_records)
            synthesizer.initialize_records(list_marginal_attrs, singleton_views=singleton_views)

            attrs_index_map = {attrs: index for index, attrs in enumerate(list_marginal_attrs)}

            for update_iteration in range(self.update_iterations):
                logger.info("update round: %d" % (update_iteration,))

                synthesizer.update_alpha(update_iteration)
                sorted_error_attrs = synthesizer.update_order(update_iteration, self.attrs_view_dict,
                                                              list_marginal_attrs)

                for attrs in sorted_error_attrs:
                    attrs_i = attrs_index_map[attrs]
                    synthesizer.update_records_prepare(self.attrs_view_dict[attrs])
                    synthesizer.update_records(self.attrs_view_dict[attrs], attrs_i)

            self.synthesized_df.loc[:, cluster_attrs] = synthesizer.df.loc[:, cluster_attrs]

    def calculate_l1_errors_v2(self, M0, M1, M2, Te):

        l1_0_1 = []
        l1_1_2 = []
        l1_0_2 = []
        l1_t_0 = []
        l1_t_1 = []
        l1_t_2 = []

        count = 0
        total = len(M1)
        for cur_attrs, m1 in M1.items():
            if len(cur_attrs) == 1:
                continue

            count += 1
            # logger.info(f'working on {count}/{total}: {cur_attrs}')

            m0 = M0[cur_attrs].values.flatten()
            m1 = m1.count
            m2 = M2[cur_attrs].values.flatten()

            m0 = m0 / np.sum(m0)
            m1 = m1 / np.sum(m1)
            m2 = m2 / np.sum(m2)

            l1_0_1.append(LA.norm(m0 - m1, 1))
            l1_1_2.append(LA.norm(m1 - m2, 1))
            l1_0_2.append(LA.norm(m0 - m2, 1))

            tmp_l1_t_0 = []
            tmp_l1_t_1 = []
            tmp_l1_t_2 = []

            cur_attrs_list = [M0[cur_attrs].index.name, M0[cur_attrs].columns.name]
            indices = sorted([i for i in self.data.encode_mapping[cur_attrs_list[0]].values()])
            columns = sorted([i for i in self.data.encode_mapping[cur_attrs_list[1]].values()])
            att_list = ['PUMA', 'YEAR', ] + cur_attrs_list
            cur_Te = Te[att_list]
            puma_year_cur_Te = cur_Te.groupby(['PUMA', 'YEAR'])
            for puma_year, one_Te in puma_year_cur_Te:
                tmp = one_Te.assign(n=1).pivot_table(values='n', index=cur_attrs_list[0], columns=cur_attrs_list[1], aggfunc=np.sum, fill_value=0)
                marginal = tmp.reindex(index=indices, columns=columns).fillna(0).astype(np.int32).values.flatten()
                marginal = marginal / np.sum(marginal)

                tmp_l1_t_0.append(LA.norm(marginal - m0, 1))
                tmp_l1_t_1.append(LA.norm(marginal - m1, 1))
                tmp_l1_t_2.append(LA.norm(marginal - m2, 1))

            # print(tmp_l1_t_0)
            # print(tmp_l1_t_1)
            # print(tmp_l1_t_2)
            l1_t_0.append(np.mean(tmp_l1_t_0))
            l1_t_1.append(np.mean(tmp_l1_t_1))
            l1_t_2.append(np.mean(tmp_l1_t_2))

            # logger.success(f't_0 = {np.mean(tmp_l1_t_0)}, t_1 = {np.mean(tmp_l1_t_1)}, t_2 = {np.mean(tmp_l1_t_2)}')
        logger.success(f'0_1 = {np.mean(l1_0_1)}, 0_2 = {np.mean(l1_0_2)}, 1_2 = {np.mean(l1_1_2)}, t_0 = {np.mean(l1_t_0)}, t_1 = {np.mean(l1_t_1)}, t_2 = {np.mean(l1_t_2)}')
        exit()
        return

    def internal_synthesize(self, noisy_puma_year, fixed_n=0) -> pd.DataFrame:
        # find clusters for synthesize; a cluster is a set of marginals closely connected
        # here we do not cluster and use all marginals as a single cluster
        clusters = self.cluster(self.attrs_view_dict)

        # target_marginals = self.data.generate_all_two_way_marginals_except_PUMA_YEAR(self.data.private_data)
        # pub_marginals = self.data.generate_all_pub_marginals()
        # self.calculate_l1_errors_v2(pub_marginals, self.attrs_view_dict, target_marginals, self.data.private_data)

        self.synthesize_records_PUMA_YEAR(noisy_puma_year, clusters, fixed_n)
        # self.synthesize_records_numbers(noisy_puma_year, clusters, fixed_n)

        return self.synthesized_df