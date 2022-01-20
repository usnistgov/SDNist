
import pandas as pd


def cellchange(df1, df2, quasi, exclude_cols):
    uniques1 = df1.drop_duplicates(subset=quasi, keep=False)
    uniques2 = df2.drop_duplicates(subset=quasi, keep=False)
    matcheduniq = uniques1.merge(uniques2, how='inner', on = quasi)
    allcols = set(df1.columns).intersection(set(df2.columns))
    cols = allcols - set(quasi) - set(exclude_cols)
    return match(matcheduniq, cols), uniques1, uniques2, matcheduniq

def match(df, cols):
    S = pd.Series(data=0, index=df.index)
    for c in cols:
        c_x = c + "_x"
        c_y = c + "_y"
        S = S + (df[c_x] == df[c_y]).astype(int)
    S = (S/len(cols))*100
    return S