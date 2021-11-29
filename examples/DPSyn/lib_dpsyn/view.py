import numpy as np


class View:
    def __init__(self, attr_one_hot: np.array, domain_size_list: np.array):
        self.attr_one_hot = attr_one_hot
        self.domain_size_list = domain_size_list

        self.domain_size = np.product(self.domain_size_list[np.nonzero(self.attr_one_hot)[0]])
        self.total_num_attr = len(self.attr_one_hot)
        self.view_num_attr = np.count_nonzero(self.attr_one_hot)

        self.encode_num = np.zeros(self.view_num_attr, dtype=np.uint32)
        self.cum_mul = np.zeros(self.view_num_attr, dtype=np.uint32)
        self.attributes_index = np.nonzero(self.attr_one_hot)[0]

        self.count = np.zeros(self.domain_size)
        self.sum = 0
        self.calculate_encode_num(self.domain_size_list)

        self.attributes_set = set()
        self.tuple_key = np.array([0], dtype=np.uint32)

        self.count_matrix = None
        self.summations = None
        self.weights = []
        self.delta = 0
        self.weight_coeff = 1

    ########################################### general functions ####################################
    def calculate_encode_num(self, domain_size_list):
        if self.view_num_attr != 0:
            categories_index = self.attributes_index

            categories_num = domain_size_list[categories_index]
            categories_num = np.roll(categories_num, 1)
            categories_num[0] = 1
            self.cum_mul = np.cumprod(categories_num)

            categories_num = domain_size_list[categories_index]
            categories_num = np.roll(categories_num, self.view_num_attr - 1)
            categories_num[-1] = 1
            categories_num = np.flip(categories_num)
            self.encode_num = np.flip(np.cumprod(categories_num))

    def calculate_tuple_key(self):
        self.tuple_key = np.zeros([self.domain_size, self.view_num_attr], dtype=np.uint32)

        if self.view_num_attr != 0:
            for i in range(self.attributes_index.shape[0]):
                index = self.attributes_index[i]
                categories = np.arange(self.domain_size_list[index])
                column_key = np.tile(np.repeat(categories, self.encode_num[i]), self.cum_mul[i])

                self.tuple_key[:, i] = column_key
        else:
            self.tuple_key = np.array([0], dtype=np.uint32)
            self.domain_size = 1

    def count_records(self, records):
        encode_records = np.matmul(records[:, self.attributes_index], self.encode_num)
        encode_key, count = np.unique(encode_records, return_counts=True)

        indices = np.where(np.isin(np.arange(self.domain_size), encode_key))[0]
        self.count[indices] = count

    def calculate_count_matrix(self):
        shape = []

        for attri in self.attributes_index:
            shape.append(self.domain_size_list[attri])

        self.count_matrix = np.copy(self.count).reshape(tuple(shape))

        return self.count_matrix

    def generate_attributes_index_set(self):
        self.attributes_set = set(self.attributes_index)

    ################################### functions for outside invoke #########################
    def calculate_encode_num_general(self, attributes_index):
        categories_index = attributes_index

        categories_num = self.domain_size_list[categories_index]
        categories_num = np.roll(categories_num, attributes_index.size - 1)
        categories_num[-1] = 1
        categories_num = np.flip(categories_num)
        encode_num = np.flip(np.cumprod(categories_num))

        return encode_num

    def count_records_general(self, records):
        count = np.zeros(self.domain_size)

        encode_records = np.matmul(records[:, self.attributes_index], self.encode_num)
        encode_key, value_count = np.unique(encode_records, return_counts=True)

        indices = np.where(np.isin(np.arange(self.domain_size), encode_key))[0]
        count[indices] = value_count

        return count

    def calculate_count_matrix_general(self, count):
        shape = []

        for attri in self.attributes_index:
            shape.append(self.domain_size_list[attri])

        return np.copy(count).reshape(tuple(shape))

    def calculate_tuple_key_general(self, unique_value_list):
        self.tuple_key = np.zeros([self.domain_size, self.view_num_attr], dtype=np.uint32)

        if self.view_num_attr != 0:
            for i in range(self.attributes_index.shape[0]):
                categories = unique_value_list[i]
                column_key = np.tile(np.repeat(categories, self.encode_num[i]), self.cum_mul[i])

                self.tuple_key[:, i] = column_key
        else:
            self.tuple_key = np.array([0], dtype=np.uint32)
            self.domain_size = 1

    def project_from_bigger_view_general(self, bigger_view):
        encode_num = np.zeros(self.total_num_attr, dtype=np.uint32)
        encode_num[self.attributes_index] = self.encode_num
        encode_num = encode_num[bigger_view.attributes_index]

        encode_records = np.matmul(bigger_view.tuple_key, encode_num)

        for i in range(self.domain_size):
            key_index = np.where(encode_records == i)[0]
            self.count[i] = np.sum(bigger_view.count[key_index])

    ######################################## functions for consistency #######################
    ############ used in commom view #############
    def initialize_consist_parameters(self, num_target_views):
        self.summations = np.zeros([self.domain_size, num_target_views])
        self.weights = np.zeros(num_target_views)

    def calculate_delta(self):
        target = np.matmul(self.summations, self.weights) / np.sum(self.weights)
        self.delta = - (self.summations - target.reshape(len(target), 1))

    def project_from_bigger_view(self, bigger_view, index):
        encode_num = np.zeros(self.total_num_attr, dtype=np.uint32)
        encode_num[self.attributes_index] = self.encode_num
        encode_num = encode_num[bigger_view.attributes_index]

        encode_records = np.matmul(bigger_view.tuple_key, encode_num)

        self.weights[index] = bigger_view.weight_coeff / np.product(self.domain_size_list[np.setdiff1d(bigger_view.attributes_index, self.attributes_index)])

        for i in range(self.domain_size):
            key_index = np.where(encode_records == i)[0]
            self.summations[i, index] = np.sum(bigger_view.count[key_index])

    ############### used in views to be consisted ###############
    def update_view(self, common_view, index):
        encode_num = np.zeros(self.total_num_attr, dtype=np.uint32)
        encode_num[common_view.attributes_index] = common_view.encode_num
        encode_num = encode_num[self.attributes_index]

        encode_records = np.matmul(self.tuple_key, encode_num)

        for i in range(common_view.domain_size):
            key_index = np.where(encode_records == i)[0]
            self.count[key_index] += common_view.delta[i, index] / len(key_index)

    def non_negativity(self):
        count = np.copy(self.count)
        self.norm_cut(count)
        # self.norm_sub(count)
        self.count = count

    @staticmethod
    def norm_sub(count):
        while (np.fabs(sum(count) - 1) > 1e-6) or (count < 0).any():
            count[count < 0] = 0
            total = sum(count)
            mask = count > 0
            if sum(mask) == 0:
                count[:] = 1.0 / len(count)
                break
            diff = (1 - total) / sum(mask)
            count[mask] += diff
        return count

    @staticmethod
    def norm_cut(count):
        # set all negative value to 0.0
        negative_indices = np.where(count < 0.0)[0]
        negative_total = abs(np.sum(count[negative_indices]))
        count[negative_indices] = 0.0

        # find all positive value
        positive_indices = np.where(count > 0.0)[0]

        if positive_indices.size != 0:
            positive_sort_indices = np.argsort(count[positive_indices])
            sort_cumsum = np.cumsum(count[positive_indices[positive_sort_indices]])

            # set the smallest positive value to 0.0 to preserve the total density
            threshold_indices = np.where(sort_cumsum <= negative_total)[0]

            if threshold_indices.size == 0:
                count[positive_indices[positive_sort_indices[0]]] = sort_cumsum[0] - negative_total
            else:
                count[positive_indices[positive_sort_indices[threshold_indices]]] = 0.0
                next_index = threshold_indices[-1] + 1

                if next_index < positive_sort_indices.size:
                    count[positive_indices[positive_sort_indices[next_index]]] = sort_cumsum[next_index] - negative_total
        else:
            count[:] = 0.0

        return count


if __name__ == "__main__":
    view = View([1, 1, 0, 0], [3, 3, 0, 0])
