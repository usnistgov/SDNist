from sdnist.kmarginal import KMarginalScore


class TaxiGraphEdgeMapScore(KMarginalScore):
    COLUMNS = [
        "pickup_community_area",
        "dropoff_community_area"
    ]
    BINS = {}
    ALWAYS_GROUPBY = []
    N_PERMUTATIONS = 1
