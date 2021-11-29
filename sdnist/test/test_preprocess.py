import numpy as np
import pandas as pd

import sdnist


def test_user_id():
    public, schema = sdnist.census(public=True)
    public.sort_values(["sim_individual_id", "YEAR"], inplace=True)

    sizes = public.groupby("sim_individual_id").size() 
    assert (sizes >= 4).all()
    assert (sizes <= 7).all()

    sizes = public.groupby(["YEAR", "sim_individual_id"]).size()
    assert (sizes == 1).all()
