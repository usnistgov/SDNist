from sdnist.metrics.kmarginal import KMarginalScore


class TaxiGraphEdgeMapScore(KMarginalScore):
    NAME = 'Graph Edge Map'
    COLUMNS = [
        "pickup_community_area",
        "dropoff_community_area"
    ]
    BINS = {}
    ALWAYS_GROUPBY = []
    N_PERMUTATIONS = 1
