k_marg_synopsys_para = (
    "The k-marginal metric checks how far the shape of the deidentified data distribution "
    "has shifted away from the target data distribution.  It does this using many 3-dimensional "
    "snapshots of the data, averaging the density differences across all snapshots.  It was developed "
    "by Sergey Pogodin as an efficient scoring mechanism for the NIST Temporal Data Challenges, and can "
    "be applied to measure the distance between any two data distributions.  A score of 0 means two distributions "
    "have zero overlap, while a score of 1000 means the two distributions match identically.  More information can be "
    "found <a href='https://aaai-ppai22.github.io/files/7.pdf'>here</a>."
)

sub_sample_para = (
    "Here we provide a sampling error baseline: Taking a random subsample of the data "
    "also shifts the distribution by introducing sampling error.  How does the shift from "
    "deidentifying data compare to the shift that would occur from subsampling the target data?"
)

k_marg_all_puma_para = (
    "Different geographical regions have different data distributions.  How much has each been altered by deidentification?"
)

univ_dist_para = (
    "Here we provide single feature distribution comparisons ordered to show "
    "worst performing features first "
    "(based on the L1 norm of density differences). Especially high-count values "
    "in the target data are not displayed on the charts but are provided below each distribution figure"
)

corr_para = (
    "<p>A key goal of deidentified data is to preserve the feature correlations from the target data, "
    "so that analyses performed on the deidentified data provide meaningful insight about the target "
    "population.Which correlations are the deidentified data preserving, and which are being altered during deidentification?</p>"
    "<p>The charts below show absolute difference of pairwise feature correlations. Darker highlighting "
    "indicates pairs of features whose correlations were not well preserved in the deidentified data.</p>"
)


pear_corr_para = (
    "The Pearson Correlation difference was a popular utility metric during the HLG-MOS Synthetic Data Test Drive"
)

kend_corr_para = (
    "This chart shows pairwise correlations using a somewhat different definition of correlation. "
    "To what extent do the two different correlation metrics agree or disagree with each other about the quality of the deidentified data?"
)

propensity_para = (

    "<p>Can a decision tree classifier tell the difference between the target data and the deidentified data? If a classifier is trained to distinguish between the two data sets, but it performs very poorly on the task when tested, then the deidentified data must look very similar to the target data. Propensity based metrics have been developed by Joshua Snoke and Gillian Raab and Claire Bowen, all of whom have participated on the NIST Synthetic Data Challenges SME panels.</p>"
    "<p>We test the classifier by giving it an unlabeled mix of original target records and deidentified records; it has to guess which is which. If the classifier is 100% confident that a given record was deidentified (not in the original target data), then it predicts '100'. If it's perfectly confident it's a target record, it predicts '0'. </p>"
    "<p>In the graph below we show the separated results-- the blue line shows the distribution of predictions the classifier gave for records that were really in the target data.  The green line shows the predictions for records from the deidentified data.  If the classifier could easily distinguish the two data sets, it will predict 100 for all deid records and 0 for all target records, and you'll see a sharp green spike on the right side of the chart and a sharp blue spike on the left side of the graph. </p>"
    "<p>If the classifier was completely confused (the two data sets had extremely similar distributions), you'll see the blue and green lines combine in a single spike at 50. </p>"
    "<p>But data is complicated, and often you'll see a variety of smaller spikes spread across the chart, as the deidentified data does a good job of capturing some parts of the target data's distribution and a poor job on other parts. </p>"
)

k_marg_break_para = (
    "In the metrics above we've considered all of the data together; "
    "however we know that algorithms may behave differently on different "
    "subgroups in the population. Below we look in more detail at deidentification "
    "performance just in the worst performing PUMA, based on k-marginal score."
)

worst_k_marg_para = "Which are the worst performing PUMA?"

rec_count_worst_para = (
    "Did the deidentified versions of these PUMA have similar "
    "population totals to the target versions? "
)

univ_dist_worst_para = "Which features are performing the worst in each of these PUMA? "

pear_corr_worst_para = "How are feature correlations performing in each of these PUMA? "

app_match_para = (
    "Deidentified data should reproduce the distribution of the target population "
    "using deidentified individuals; this protects the privacy of the real individuals "
    "in the target data. Can we be sure that the deidentified data does not include real people? "
    "The apparent match metric first considers which deidentified individuals look like they might be "
    "real people (they are unique matches on quasi-identifier features) and then considers whether "
    "the deidentified records actually represent real individuals. "
)

quasi_idf_para = "These features are used to determine if a deidentified record looks like it might be a real person in the target data."

rec_matched_para = (
    "Based only on the quasi-identifier features, how much of the target data has "
    "apparent unique matches in the deidentified data? and then the "
    "percent should be a percent of target data"
)

percn_matched_para = (
    "Considering the set of apparent matches, to what extent are they real matches? "
    "This distribution shows edit similarity between apparently matched pairs on how many of "
    "the 22 features does the deidentified record have the same value as the real record. "
    "If the distribution is centered near 100% that means these deidentified records largely "
    "mimic target records and are potentially leaking information about real individuals. "
    "If the distribution is centered below 50% that means the deidentified records are very "
    "different from the target records, and the apparent matches are not real matches."
)

unique_exact_match_para_1 = (
    "Unique Exact Match (UEM) is a simple privacy metric that counts the percentage of singleton records in the target data that are also present in the deidentified data; these uniquely identifiable individuals leaked through the deidentification process."
)

unique_exact_match_para_2 = (
    ""
)

unique_exact_match_para_3 = (
    ""
)

unique_exact_match_para_4 = (
    ""
)

# Explainer paragraphs for DiSCO Metric
disco_explainer_a = (
    "The <a href='https://arxiv.org/abs/2406.16826'>Disclosive in Synthetic Correct Original"
    " (DiSCO)</a> metric is a privacy metric developed "
    " by Gillian Raab, Beata Nowok and Chris Dibben that"
    " measures attribute disclosure risk in a synthetic dataset. It aims to quantify the proportion"
    " of records in the target dataset that have sensitive features which can be correctly inferred "
    " from certain identifying features present in the synthetic dataset."
)

disco_explainer_b = (
    "To calculate DiSCO, we first identify a set of variables that, when combined, can be used to"
    " identify attributes (Target Features) of records in the target dataset. Then,we check to see"
    " if there are any deidentified records that have one unique target value for a given set of"
    " quasi-identifier values. Finally, we check to see if records in the target dataset that match "
    " our potentially-disclosive quasi-identifiers also match on the corresponding target value."
)

disco_explainer_c = (
    "We expand upon this metric for the entire dataset by taking each set of k quasi-identifiers and calculating "
    "DiSCO for each target feature in the dataset. We can then average across the DiSCO scores we’ve calculated to "
    "produce an overall k-DiSCO score for a dataset. We can average each DiSCO score for a particular target feature "
    "to find how vulnerable this feature is to an attribute inference attack, or, average across all DiSCO scores "
    "where a specific quasi-identifier feature is present to calculate how disclosive a particular feature is."
)
