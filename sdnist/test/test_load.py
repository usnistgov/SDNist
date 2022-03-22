import sdnist


def test_load():
    df, schema = sdnist.taxi()
    sdnist.schema.check_compliance(df, schema)

    df, schema = sdnist.census()
    sdnist.schema.check_compliance(df, schema)
    assert len(df.columns) == 36 # 35 + sim_individual_id


def test_expanduser():
    df, schema = sdnist.census(root="~/datasets")


def test_discretize():
    df, schema = sdnist.census(root="~/datasets")
    bins = sdnist.kmarginal.CensusKMarginalScore.BINS
    del df["HHWT"]
    df["this is a test"] = 5

    df_bin = sdnist.utils.discretize(df, schema, bins)


if __name__ == "__main__":
    test_load()
    test_expanduser()
    test_discretize()
