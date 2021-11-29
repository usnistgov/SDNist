from loguru import logger
from numpy import linalg as LA
import copy

import numpy as np
import pandas as pd


class RecordSynthesizer:
    records = None
    df = None
    error_tracker = None

    rounding_method = 'deterministic'

    under_cell_indices = None
    zero_cell_indices = None
    over_cell_indices = None
    records_throw_indices = None

    add_amount = 0
    add_amount_zero = 0
    reduce_amount = 0

    actual_marginal = None
    synthesize_marginal = None
    alpha = 1.0

    encode_records = None
    encode_records_sort_index = None

    def __init__(self, attrs, domains, num_records):
        self.attrs = attrs
        self.domains = domains
        self.num_records = num_records

    def update_alpha(self, iteration):
        self.alpha = 1.0 * 0.84 ** (iteration // 20)

    def update_order(self, iteration, views, iterate_keys):

        self.error_tracker.insert(loc=0, column=f"{iteration}-before", value=0)

        for key_i, key in enumerate(iterate_keys):
            self.track_error(views[key], key_i)

        sort_error_tracker = self.error_tracker.sort_values(by=f"{iteration}-before", ascending=False)

        self.error_tracker.insert(loc=0, column=f"{iteration}-after", value=0)
        return list(sort_error_tracker.index)

    def update_records(self, original_view, iteration):
        view = copy.deepcopy(original_view)

        if iteration % 2 == 0:
            self.complete_partial_ratio(view, 0.5)
        else:
            self.complete_partial_ratio(view, 1.0)

    def initialize_records(self, iterate_keys, method="random", singleton_views=None):
        self.records = np.empty([self.num_records, len(self.attrs)], dtype=np.uint32)

        for attr_i, attr in enumerate(self.attrs):
            if method == "random":
                self.records[:, attr_i] = np.random.randint(0, self.domains[attr_i], size=self.num_records)

            elif method == "singleton":
                self.records[:, attr_i] = self.generate_singleton_records(singleton_views[attr])

        self.df = pd.DataFrame(self.records, columns=self.attrs)
        self.error_tracker = pd.DataFrame(index=iterate_keys)

    def generate_singleton_records(self, singleton):
        record = np.empty(self.num_records, dtype=np.uint32)
        dist_cumsum = np.cumsum(singleton.count)
        start = 0

        for index, value in enumerate(dist_cumsum):
            end = int(round(value * self.num_records))
            record[start: end] = index
            start = end

        np.random.shuffle(record)

        return record

    def update_records_prepare(self, view):
        alpha = self.alpha

        # deal with under cells (synthesize_marginal < actual_marginal) where synthesize_marginal != 0
        self.under_cell_indices = np.where((self.synthesize_marginal < self.actual_marginal) & (self.synthesize_marginal != 0))[0]

        under_rate = (self.actual_marginal[self.under_cell_indices] - self.synthesize_marginal[self.under_cell_indices]) / self.synthesize_marginal[self.under_cell_indices]
        ratio_add = np.minimum(under_rate, np.full(self.under_cell_indices.shape[0], alpha))
        self.add_amount = self._rounding(ratio_add * self.synthesize_marginal[self.under_cell_indices] * self.num_records)

        # deal with the case synthesize_marginal == 0 and actual_marginal != 0
        self.zero_cell_indices = np.where((self.synthesize_marginal == 0) & (self.actual_marginal != 0))[0]
        self.add_amount_zero = self._rounding(alpha * self.actual_marginal[self.zero_cell_indices] * self.num_records)

        # determine the number of records to be removed
        self.over_cell_indices = np.where(self.synthesize_marginal > self.actual_marginal)[0]
        num_add_total = np.sum(self.add_amount) + np.sum(self.add_amount_zero)

        beta = self.find_optimal_beta(num_add_total, self.over_cell_indices)
        over_rate = (self.synthesize_marginal[self.over_cell_indices] - self.actual_marginal[self.over_cell_indices]) / self.synthesize_marginal[self.over_cell_indices]
        ratio_reduce = np.minimum(over_rate, np.full(self.over_cell_indices.shape[0], beta))
        self.reduce_amount = self._rounding(ratio_reduce * self.synthesize_marginal[self.over_cell_indices] * self.num_records).astype(int)

        # logger.debug("alpha: %s | beta: %s" % (alpha, beta))
        # logger.debug("num_boost: %s | num_reduce: %s" % (num_add_total, np.sum(self.reduce_amount)))

        # convert each record from multiple attributes to one attribute
        self.encode_records = np.matmul(self.records[:, view.attributes_index], view.encode_num)
        self.encode_records_sort_index = np.argsort(self.encode_records)
        self.encode_records = self.encode_records[self.encode_records_sort_index]

    def determine_throw_indices(self):
        valid_indices = np.nonzero(self.reduce_amount)[0]
        valid_cell_over_indices = self.over_cell_indices[valid_indices]
        valid_cell_num_reduce = self.reduce_amount[valid_indices]
        valid_data_over_index_left = np.searchsorted(self.encode_records, valid_cell_over_indices, side="left")
        valid_data_over_index_right = np.searchsorted(self.encode_records, valid_cell_over_indices, side="right")

        valid_num_reduce = np.sum(valid_cell_num_reduce)
        self.records_throw_indices = np.zeros(valid_num_reduce, dtype=np.uint32)
        throw_pointer = 0

        for i, cell_index in enumerate(valid_cell_over_indices):
            match_records_indices = self.encode_records_sort_index[valid_data_over_index_left[i]: valid_data_over_index_right[i]]
            throw_indices = np.random.choice(match_records_indices, valid_cell_num_reduce[i], replace=False)

            self.records_throw_indices[throw_pointer: throw_pointer + throw_indices.size] = throw_indices
            throw_pointer += throw_indices.size

        np.random.shuffle(self.records_throw_indices)

    def handle_zero_cells(self, view):
        # overwrite / partial when synthesize_marginal == 0
        if self.zero_cell_indices.size != 0:
            for index, cell_index in enumerate(self.zero_cell_indices):
                num_partial = int(self.add_amount_zero[index])

                if num_partial != 0:
                    for i in range(view.view_num_attr):
                        self.records[self.records_throw_indices[: num_partial], view.attributes_index[i]] = \
                            view.tuple_key[cell_index, i]

                self.records_throw_indices = self.records_throw_indices[num_partial:]

    def complete_partial_ratio(self, view, complete_ratio):
        num_complete = np.rint(complete_ratio * self.add_amount).astype(int)
        num_partial = np.rint((1 - complete_ratio) * self.add_amount).astype(int)

        valid_indices = np.nonzero(num_complete + num_partial)
        num_complete = num_complete[valid_indices]
        num_partial = num_partial[valid_indices]

        valid_cell_under_indices = self.under_cell_indices[valid_indices]
        valid_data_under_index_left = np.searchsorted(self.encode_records, valid_cell_under_indices, side="left")
        valid_data_under_index_right = np.searchsorted(self.encode_records, valid_cell_under_indices, side="right")
        
        for valid_index, cell_index in enumerate(valid_cell_under_indices):
            match_records_indices = self.encode_records_sort_index[valid_data_under_index_left[valid_index]: valid_data_under_index_right[valid_index]]

            np.random.shuffle(match_records_indices)
            
            if self.records_throw_indices.shape[0] >= (num_complete[valid_index] + num_partial[valid_index]):
                # complete update code
                if num_complete[valid_index] != 0:
                    self.records[self.records_throw_indices[: num_complete[valid_index]]] = self.records[
                        match_records_indices[: num_complete[valid_index]]]
                
                # partial update code
                if num_partial[valid_index] != 0:
                    self.records[np.ix_(
                        self.records_throw_indices[num_complete[valid_index]: (num_complete[valid_index] + num_partial[valid_index])],
                        view.attributes_index)] = view.tuple_key[cell_index]
                
                # update records_throw_indices
                self.records_throw_indices = self.records_throw_indices[num_complete[valid_index] + num_partial[valid_index]:]
            
            else:
                # todo: simply apply complete operation here, do not know whether it is make sense
                self.records[self.records_throw_indices] = self.records[match_records_indices[: self.records_throw_indices.size]]

    def find_optimal_beta(self, num_add_total, cell_over_indices):
        actual_marginal_under = self.actual_marginal[cell_over_indices]
        synthesize_marginal_under = self.synthesize_marginal[cell_over_indices]
        
        lower_bound = 0.0
        upper_bound = 1.0
        beta = 0.0
        current_num = 0.0
        iteration = 0
        
        while abs(num_add_total - current_num) >= 1.0:
            beta = (upper_bound + lower_bound) / 2.0
            current_num = np.sum(
                np.minimum((synthesize_marginal_under - actual_marginal_under) / synthesize_marginal_under,
                np.full(cell_over_indices.shape[0], beta)) * synthesize_marginal_under * self.records.shape[0])
            
            if current_num < num_add_total:
                lower_bound = beta
            elif current_num > num_add_total:
                upper_bound = beta
            else:
                return beta

            iteration += 1
            if iteration > 50:
                # logger.warning("cannot find the optimal beta")
                break
        
        return beta

    def track_error(self, view, key_i):
        self.actual_marginal = view.count
        count = view.count_records_general(self.records)
        self.synthesize_marginal = count / np.sum(count)

        l1_error = LA.norm(self.actual_marginal - self.synthesize_marginal, 1)
        self.error_tracker.iloc[key_i, 0] = l1_error

        # logger.info("the l1 error before updating is %s" % (l1_error,))

    def _rounding(self, vector):
        if self.rounding_method == 'stochastic':
            ret_vector = np.zeros(vector.size)
            rand = np.random.rand(vector.size)

            integer = np.floor(vector)
            decimal = vector - integer

            ret_vector[rand > decimal] = np.floor(decimal[rand > decimal])
            ret_vector[rand < decimal] = np.ceil(decimal[rand < decimal])
            ret_vector += integer
            return ret_vector
        elif self.rounding_method == 'deterministic':
            return np.round(vector)
        else:
            raise NotImplementedError(self.rounding_method)
