import math

import numpy as np
from scipy.optimize import fsolve


def lap_comp(epsilon, delta, sensitivity, k):
    return epsilon * 1.0 / k / sensitivity


def lap_adv_comp(epsilon, delta, sensitivity, k):
    def func(x_0):
        eps_0 = x_0[0]
        return math.sqrt(2 * k * math.log(1 / delta)) * eps_0 + k * (math.exp(eps_0) - 1) * eps_0 - epsilon

    result = fsolve(func, np.array([0.0]))

    return result[0] / sensitivity


def gauss_adv_comp(epsilon, delta, sensitivity, k):
    def gauss(delta_0):
        dlt = delta - delta_0 * k

        def eps_func(x_0):
            eps_0 = x_0[0]
            return math.sqrt(2 * k * math.log(1 / dlt)) * eps_0 + k * (math.exp(eps_0) - 1) * eps_0 - epsilon

        epsilon_0 = fsolve(eps_func, np.array([0.0]))[0]
        sigma = sensitivity * np.sqrt(2 * math.log(1.25 / delta_0)) / epsilon_0
        return sigma

    l, h = 1e-30, delta * 1.0 / k / 1.1
    min_delta_0 = my_minimize(gauss, l, h)
    return gauss(min_delta_0)


def my_minimize(func, l, h):
    vfunc = np.vectorize(func)
    cur_l, cur_h = l, h
    n = 20000
    for i in range(10):
        xs = np.linspace(cur_l, cur_h, n)
        vs = vfunc(xs)
        vs_index = np.argsort(vs)
        cur_l_index, cur_h_index = vs_index[0], vs_index[1]
        cur_l, cur_h = xs[cur_l_index], xs[cur_h_index]

    return (cur_l + cur_h) / 2


def gauss_renyi(epsilon, delta, sensitivity, k):
    def renyi(low):
        epsilon0 = max(1e-20, epsilon - np.log(1.0 / delta) * 1.0 / (low - 1))
        sigma = np.sqrt(k * low * sensitivity ** 2 * 1.0 / 2 / epsilon0)
        return sigma

    l, h = 1.00001, 100000
    min_low = my_minimize(renyi, l, h)
    min_sigma = renyi(min_low)

    return min_sigma


def gauss_zcdp(epsilon, delta, sensitivity, k):
    tmp_var = 2 * k * sensitivity ** 2 * math.log(1 / delta)

    sigma = (math.sqrt(tmp_var) + math.sqrt(tmp_var + 2 * k * sensitivity ** 2 * epsilon)) / (2 * epsilon)

    return sigma


# zcdp and zcdp2 and rdp perform the same
def gauss_zcdp2(epsilon, delta, sensitivity, k):
    my_log = math.log(1 / delta)

    sigma = sensitivity * math.sqrt(k / 2) / (math.sqrt(epsilon + my_log) - math.sqrt(my_log))

    return sigma


def lap_zcdp_comp(epsilon, delta, sensitivity, k):
    return math.sqrt(2.0 * (math.sqrt(k) * sensitivity / epsilon) ** 2)


def get_noise(eps, delta, sensitivity, num_composition):
    lap_param = lap_comp(eps, delta, sensitivity, num_composition)
    lap_naive_var = 2 * (1.0 / lap_param ** 2)

    gauss_param = gauss_zcdp(eps, delta, sensitivity, num_composition)
    gauss_var_zcdp = gauss_param ** 2
    if lap_naive_var < gauss_var_zcdp:
        return 'lap', 1 / lap_param
    else:
        return 'gauss', gauss_param


# print(gauss_zcdp(0.88, 3e-11, 7, 22) ** 2)
# print(2 * (1.0 / lap_comp(0.88, 3e-11, 7, 22) ** 2))
#
# print(gauss_zcdp(10, 3e-11, 7, 233) ** 1)
# print(2 * (1.0 / lap_comp(10, 3e-11, 7, 233) ** 2))

'''
# when 2 * k ** 0.5 > (math.log(1/delta) + epsilon) ** 0.5 + (math.log(1/delta)) ** 0.5, zcdp gives better accuracy

total_epss = [0.001, 0.002]
total_epss = [0.3, 1, 8]
total_epss = [0.252, 0.87, 7.28]
total_epss = [0.01]
sensitivitys = [1]
n = 30000
# total_delta = 1.0 / n ** 2
total_delta = 1e-15
ks = [1, 5, 10, 15, 20, 30, 50, 100]

alpha = 0.05
domain_size = 100

for total_eps in total_epss:
    for sensitivity in sensitivitys:
        print(total_eps)
        for k in ks:
            lap_param = lap_comp(total_eps, total_delta, sensitivity, k)
            lap_naive_var = 2 * (1.0 / lap_param ** 2)
            print('& $%.1E$' % lap_naive_var, end='\t')

        print('\\\\')
        for k in ks:
            lap_param = lap_adv_comp(total_eps, total_delta, sensitivity, k)
            lap_var = 2 * (1.0 / lap_param ** 2)
            print('& $%.1E$' % lap_var, end='\t')

        print('\\\\')
        for k in ks:
            gauss_param = gauss_adv_comp(total_eps, total_delta, sensitivity, k)
            gauss_var_adv = gauss_param ** 2
            print('& $%.1E$' % gauss_var_adv, end='\t')

            # gauss_param = gauss_renyi(total_eps, total_delta, sensitivity, k)
            # gauss_var = gauss_param ** 2

        print('\\\\')
        for k in ks:
            gauss_param = gauss_zcdp(total_eps, total_delta, sensitivity, k)
            gauss_var_zcdp = gauss_param ** 2
            print('& $%.1E$' % gauss_var_zcdp, end='\t')

            # gauss_param3 = gauss_zcdp2(total_eps, total_delta, sensitivity, k)
            # gauss_var_zcdp3 = gauss_param3 ** 2

            # print(
            #     f'${total_eps}, ${sensitivity}$, ${math.sqrt(lap_naive_var)}$, ${math.sqrt(lap_var)}$, ${math.sqrt(gauss_var_adv)}$, ${math.sqrt(gauss_var_zcdp)}$')

            norm_scale = gauss_param
            lap_scale = 1.0 / lap_param
            norm_mean = 0
            laplace_mean = 0

            # norm_threshold = 4.0 * norm.ppf(1 - alpha / domain_size, norm_mean, norm_scale)
            # lap_threshold = 4.0 * laplace.ppf(1 - alpha / domain_size, laplace_mean, lap_scale)
            # print(norm_threshold, lap_threshold)
        print('\\\\')
'''