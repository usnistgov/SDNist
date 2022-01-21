import math

import matplotlib.pyplot as plt

import sdnist


def test_score():
    public, schema = sdnist.census()
    assert public.shape[1] == 36

    public = public.sample(n=10000)
    assert sdnist.schema.check_compliance(public, schema)

    synthetic = public.sample(frac=0.1)

    # Directly building score object
    score = sdnist.kmarginal.CensusKMarginalScore(public, synthetic, schema, drop_columns=["HHWT", "DEPARTS", "ARRIVES"])
    score.compute_score()
    for perm in score.columns():
        assert "HHWT" not in perm
        assert "DEPARTS" not in perm
        assert "ARRIVES" not in perm

    assert score.scores is not None
    assert score.score is not None
    assert 0 <= score.score <= 1000

    # Calling from top level 
    score = sdnist.score(public, synthetic, schema, drop_columns=["HHWT", "DEPARTS", "ARRIVES"])
    for perm in score.columns():
        assert "HHWT" not in perm
        assert "DEPARTS" not in perm
        assert "ARRIVES" not in perm

    assert score.scores is not None
    assert score.score is not None
    assert 0 <= score.score <= 1000

    assert isinstance(score.report(), dict)


def _test_score_taxi():
    def compute_df_score(df, frac, benchmark="private"):
        s = []
        for _ in range(4):
            synthetic = df.sample(frac=frac)
            score = sdnist.score(df, synthetic, schema, challenge="taxi", n_permutations=150)
            print(f"{frac*100}%, {benchmark}: {score}")    
            s.append(score.score)

        mean = sum(s) / len(s)
        std = math.sqrt(sum([(x - mean)**2 for x in s]) / len(s))
        print(f"{frac*100}%, {benchmark}: {mean} +/- {std}")

    for frac in (0.01, 0.1, 0.5):
        # 2020
        df, schema = sdnist.taxi(public=False)
        compute_df_score(df, frac, "2020")

        # 2016
        df, schema = sdnist.taxi(public=False, test=True)
        compute_df_score(df, frac, "2016")

def _test_score_census():
    def compute_df_score(df, frac, benchmark="private"):
        s = []
        for _ in range(4):
            synthetic = df.sample(frac=frac)
            score = sdnist.score(df, synthetic, schema, challenge="census", n_permutations=150)
            print(f"{frac*100}%, {benchmark}: {score}")    
            s.append(score.score)

        mean = sum(s) / len(s)
        std = math.sqrt(sum([(x - mean)**2 for x in s]) / len(s))
        print(f"{frac*100}%, {benchmark}: {mean} +/- {std}")


    for frac in (0.01, 0.1, 0.5):
        # 2020
        df, schema = sdnist.census(public=False)
        compute_df_score(df, frac, "public_leaderboard/NY-PA")

        # 2016
        df, schema = sdnist.census(public=False, test=True)
        compute_df_score(df, frac, "private_leaderboard/GA-NC-SC")

def test_flat_score():
    public, schema = sdnist.census()
    public.sort_values("sim_individual_id", inplace=True)
    public = public.iloc[:10000]
    
    public_flat = sdnist.utils.unstack(public)
    assert public_flat.shape[1] == 34 * 7

    synthetic_flat = public_flat.sample(frac=0.1)
    synthetic = sdnist.utils.stack(synthetic_flat)
    assert synthetic.shape[1] == 36

    score = sdnist.kmarginal.CensusLongitudinalKMarginalScore(public, synthetic, schema)
    print(score.compute_score())

    assert score.score is not None
    assert 0 <= score.score <= 1000

def test_flat():
    """ Make sure that stacking/unstacking does not change the dataset. """
    public, schema = sdnist.census()
    public.sort_values("sim_individual_id", inplace=True)
    public = public.iloc[:10000]

    public_flat = sdnist.utils.unstack(public, flat=True)
    assert public_flat.shape[1] == 34 * 7

    stacked = sdnist.utils.stack(public_flat)
    assert stacked.shape == public.shape

    score = sdnist.score(public, stacked, schema, challenge="census")
    assert score.score > 999

def test_report():
    public, schema = sdnist.census(public=True)

    score = sdnist.score(public, public.sample(frac=.1), schema, n_permutations=20)
    score.html(browser=False)

    print(score.column_scores)
    score.html(browser=False, column="DEPARTS")

def test_violin():
    public, schema = sdnist.census(public=True)

    score = sdnist.score(public, public.sample(frac=.1), schema, n_permutations=10)
    score.violin()
   
def test_boxplot():
    public, schema = sdnist.census(public=True)

    score = sdnist.score(public, public.sample(frac=.1), schema, n_permutations=10)
    score.boxplot(idx=0, name="First")
    score.boxplot(idx=1, name="Second")

def test_boxplot_columns():
    public, schema = sdnist.census(public=True)

    score = sdnist.score(public, public.sample(frac=.1), schema, n_permutations=20)
    score.boxplot_columns()
   

if __name__ == "__main__":
    test_score()