k_marg_synopsys_para = "The k-marginal metric checks how far the shape of " \
                       "the synthetic data distribution has shifted away from " \
                       "the target data distribution.  It does this using many " \
                       "3-dimensional snapshots of the data, averaging the " \
                       "density differences across all snapshots.  It was developed " \
                       "by Sergey Pogodin as an efficient scoring mechanism for the NIST " \
                       "Temporal Data Challenges, and can be applied to measure the " \
                       "distance between any two data distributions.  " \
                       "A score of 0 means two distributions have zero overlap, " \
                       "while a score of 1000 means the two distributions match identically.  " \
                       "More information can be found here: <a href='https://www.google.com/'>[PPAI paper]</a>."

sub_sample_para = "Here we provide a sampling error baseline: " \
                  "Taking a random subsample of the data also shifts " \
                  "the distribution by introducing sampling error.  " \
                  "How does the shift from synthesizing data compare to " \
                  "the shift that would occur from subsampling the target data? "

k_marg_all_puma_para = "Different PUMA have different subpopulations and distributions; " \
                       "how much has each PUMA shifted during synthesis? "

univ_dist_para = "Here we provide single feature distribution comparisons for the worst performing " \
                 "features (based on the L1 norm of density differences)."

corr_para = "A key goal of synthetic data is to preserve the feature " \
            "correlations from the target data, so that analyses performed " \
            "on the synthetic data provide meaningful insight about the target " \
            "population.  Which correlations are the synthetic data preserving, " \
            "and which are being altered during synthesis?"

pear_corr_para = "lorum lorum lorum, I’m skeptical of using this correlation approach but " \
                 "that’s all the more reason to include it and draw attention to it. " \
                 "Note that darker highlighting indicates pairs of features whose correlations " \
                 "were not well preserved by the synthetic data. Note that it was popular during " \
                 "the HLG-MOS Synthetic Data Test Drive. "

kend_corr_para = "lorum, lorum, lorum.   Compare this to the PCC above. "

propensity_para = "Can a decision tree classifier tell the difference between the target data " \
                  "and the synthetic data?   If a classifier is trained to distinguish between " \
                  "the two data sets and it performs poorly on the task, then the synthetic " \
                  "data must not be easy to distinguish from the target data.  If the green " \
                  "line matches the blue line, and if the propensity score is close to 0.5 " \
                  "[check with gillian], then the synthetic data is high quality.  Propensity " \
                  "based metrics have been developed by [Gillian & Josh] and [Claire Bowen], " \
                  "all members of the NIST Synthetic Data Challenges SME panels."

pca_para = "This is another approach for visualizing where the distribution of " \
           "the synthetic data has shifted away from the target data.  In this approach, " \
           "we begin by using PCA to find a way of representing the target data in a " \
           "lower dimensional space (in 5 dimensions rather than the full 22 dimensions of " \
           "the original feature space).   Descriptions of the new five dimensions " \
           "(components) are given in the components table; these will change depending " \
           "on which target data set you’re using.   Five is better than 22, but we want " \
           "to get down to two dimensions so we can plot the data on simple (x,y) axes– " \
           "the plots below show the data across each possible pair combination of " \
           "our five components.  You can compare how the shapes change between the " \
           "target data and the synthetic data, and consider what that might mean in " \
           "light of the component definitions.  This is a relatively new metric designed " \
           "by [Part of the IPUMS International Submission for the HLG-MOS Test Drive]"

k_marg_break_para = "In the metrics above we’ve considered all of the data together; " \
                    "however we know that algorithms may behave differently on different " \
                    "subgroups in the population.   Below we look in more detail at synthesis " \
                    "performance just in the worst performing PUMA, based on k-marginal score."

worst_k_marg_para = "Which are the worst performing PUMA?"

rec_count_worst_para = "Did the synthetic versions of these PUMA have similar " \
                       "population totals to the target versions? "

univ_dist_worst_para = "Which features are performing the worst in each of these PUMA? "

pear_corr_worst_para = "How are feature correlations performing in each of these PUMA? "

app_match_para = "Synthetic data should reproduce the distribution of the target " \
                 "population using synthetic individuals; this protects the privacy " \
                 "of the real individuals in the target data." \
                 "Can we be sure that the synthetic data does not include real people?   " \
                 "The apparent match metric first considers which synthetic individuals look " \
                 "like they might be real people (they are unique matches on quasi-identifier " \
                 "features) and then considers whether the synthetic records actually represent " \
                 "real individuals. "

quasi_idf_para = "These features are used to determine if a synthetic record looks " \
                 "like it might be a real person in the target data."

rec_matched_para = "Based only on the quasi-identifier features, how many synthetic records " \
                   "uniquely match an individual in the target data? " \
                   "What percentage of the synthetic data has apparent real matches?"

percn_matched_para = "Considering the set of apparent matches, to what extent are they real " \
                     "matches?  This distribution shows edit similarity between apparently " \
                     "matched pairs– on how many of the 22 features does the synthetic record " \
                     "have the same value as the real record.  If the distribution is centered " \
                     "near 100% that means these synthetic records largely mimic target records " \
                     "and are potentially leaking information about real individuals. " \
                     "If the distribution is centered below 50% that means the synthetic " \
                     "records are very different from the target records, and the apparent " \
                     "matches aren’t real matches."