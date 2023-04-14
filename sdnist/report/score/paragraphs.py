k_marg_synopsys_para = "The k-marginal metric checks how far the shape of the deidentified data distribution " \
                       "has shifted away from the target data distribution.  It does this using many 3-dimensional " \
                       "snapshots of the data, averaging the density differences across all snapshots.  It was developed " \
                       "by Sergey Pogodin as an efficient scoring mechanism for the NIST Temporal Data Challenges, and can " \
                       "be applied to measure the distance between any two data distributions.  A score of 0 means two distributions " \
                       "have zero overlap, while a score of 1000 means the two distributions match identically.  More information can be " \
                       "found <a href='https://aaai-ppai22.github.io/files/7.pdf'>here</a>."

sub_sample_para = "Here we provide a sampling error baseline: Taking a random subsample of the data " \
                  "also shifts the distribution by introducing sampling error.  How does the shift from " \
                  "deidentifying data compare to the shift that would occur from subsampling the target data?"

k_marg_all_puma_para = "Different PUMA have different subpopulations and " \
                       "distributions; how much has each PUMA shifted during deidentification?"

univ_dist_para = "Here we provide single feature distribution comparisons ordered to show " \
                 "worst performing features first " \
                 "(based on the L1 norm of density differences). Especially high-count values " \
                 "in the target data are not displayed on the charts but are provided below each distribution figure"

corr_para = "A key goal of deidentified data is to preserve the feature correlations from the target " \
            "data, so that analyses performed on the deidentified data provide meaningful insight about " \
            "the target population.  Which correlations are the deidentified data preserving, and " \
            "which are being altered during deidentification?"


pear_corr_para = "The <a href='https://en.wikipedia.org/wiki/Pearson_correlation_coefficient'>Pearson Correlation</a> " \
                 "difference was a popular utility metric during the <a href='https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/index.html'>" \
                 "HLG-MOS Synthetic Data Test Drive</a>. Note that darker highlighting indicates pairs of features whose " \
                 "correlations were not well preserved by the deidentified data."

kend_corr_para = "This chart shows pairwise correlations using a somewhat different " \
                 "<a href='https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient'>definition of correlation</a>." \
                 " To what extent do the two different correlation metrics agree or disagree with each other about the quality " \
                 "of the deidentified data?"

propensity_para = "Can a decision tree classifier tell the difference between the target data and the deidentified data? " \
                  "If a classifier is trained to distinguish between the two data sets and it performs poorly on the " \
                  "task, then the deidentified data must not be easy to distinguish from the target data. " \
                  "If the green line matches the blue line, then the deidentified data is high quality. " \
                  "Propensity based metrics have been developed by " \
                  "<a href='https://pennstate.pure.elsevier.com/en/publications/general-and-specific-utility-measures-for-synthetic-data'>" \
                  "Joshua Snoke and Gillian Raab</a> and <a href='https://www.researchgate.net/publication/323867757_STatistical_Election_to_Partition_Sequentially_STEPS_and_Its_Application_in_Differentially_Private_Release_and_Analysis_of_Youth_Voter_Registration_Data'>Claire Bowen</a>" \
                  ", all of whom have participated on the NIST Synthetic Data Challenges SME panels."

k_marg_break_para = "In the metrics above we’ve considered all of the data together; " \
                    "however we know that algorithms may behave differently on different " \
                    "subgroups in the population. Below we look in more detail at deidentification " \
                    "performance just in the worst performing PUMA, based on k-marginal score."

worst_k_marg_para = "Which are the worst performing PUMA?"

rec_count_worst_para = "Did the deidentified versions of these PUMA have similar " \
                       "population totals to the target versions? "

univ_dist_worst_para = "Which features are performing the worst in each of these PUMA? "

pear_corr_worst_para = "How are feature correlations performing in each of these PUMA? "

app_match_para = "Deidentified data should reproduce the distribution of the target population " \
                 "using deidentified individuals; this protects the privacy of the real individuals " \
                 "in the target data. Can we be sure that the deidentified data does not include real people? " \
                 "The apparent match metric first considers which deidentified individuals look like they might be " \
                 "real people (they are unique matches on quasi-identifier features) and then considers whether " \
                 "the deidentified records actually represent real individuals. "

quasi_idf_para = "These features are used to determine if a deidentified record looks like it might be a real person in the target data."

rec_matched_para = "Based only on the quasi-identifier features, how much of the target data has " \
                   "apparent unique matches in the deidentified data? and then the " \
                   "percent should be a percent of target data"

percn_matched_para = "Considering the set of apparent matches, to what extent are they real matches? " \
                     "This distribution shows edit similarity between apparently matched pairs on how many of " \
                     "the 22 features does the deidentified record have the same value as the real record. " \
                     "If the distribution is centered near 100% that means these deidentified records largely " \
                     "mimic target records and are potentially leaking information about real individuals. " \
                     "If the distribution is centered below 50% that means the deidentified records are very " \
                     "different from the target records, and the apparent matches are not real matches."

unique_exact_match_para = "This is a count of unique records in the target data that were exactly reproduced " \
                          "in the deidentified data. Because these records were unique outliers in the " \
                          "target data, and they still appear unchanged in the deidentified data, " \
                          "they are potentially vulnerable to reidentification."