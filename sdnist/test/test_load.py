import sdnist


def test_load():
    df, schema = sdnist.taxi()
    sdnist.schema.check_compliance(df, schema)

    df, schema = sdnist.census()
    sdnist.schema.check_compliance(df, schema)
    assert len(df.columns) == 36 # 35 + sim_individual_id

def test_expanduser():
    df, schema = sdnist.census(root="~/datasets")

if __name__ == "__main__":
    test_load()