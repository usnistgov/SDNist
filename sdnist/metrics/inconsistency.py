from pathlib import Path
import pandas as pd

from sdnist.utils import *

# List of tuples with all the information associated with each inconsistency (abbreviated ic)
# [(category for ic, name for ic, explanation string for ic, features to highlight for ic)]
[GROUP, NAME, DESCRIPTION, FEATURES] = [0, 1, 2, 3]

ic_types = [
    ("a", "child_DVET", "Children (< 15) can't be disabled military veterans",
     ["AGEP", "DVET"]),
    ("a", "child_MSP", "Children (< 15) can't be married",
     ["AGEP", "MSP"]),
    ("a", "child_PINCP", "Children (< 15) don't have personal incomes",
     ["AGEP", "PINCP"]),
    ("a", "child_PINCP_DECILE", "Children (< 15) don't have personal incomes",
     ["AGEP", "PINCP_DECILE"]),
    ("a", "child_INDP", "Children (< 15) don't have work industries",
     ["AGEP", "INDP"]),
    ("a", "child_INDP_CAT", "Children (< 15) don't have work industries",
     ["AGEP", "INDP_CAT"]),
    ("a", "child_phd", "Children (< 15) don't have PhDs",
     ["AGEP", "EDU"]),
    ("a", "adult_child", "Even when the AGEP feature is not explicitly used, "
                         "features which use N to indicate children ( < 15) must agree",
     ["MSP", "PINCP", "PINCP_DECILE"]),
    ("a", "adult_N", "Adults ( > 14) must specify values (other than N) for all adult features",
     ["AGEP", "MSP", "PINCP", "PINCP_DECILE", "EDU", "DPHY", "DREM"]),
    ("a", "toddler_DPHY", "Toddlers (< 5) naturally toddle, it's not a physical disability",
     ["AGEP", "DPHY"]),
    ("a", "toddler_DREM", "Toddlers (< 5) are naturally forgetful, it's not a cognitive disability",
     ["AGEP", "DREM"]),
    ("a", "toddler_diploma", "Toddlers (< 5) don't have high school diplomas",
     ["AGEP", "EDU"]),
    ("a", "infant_EDU", "Infants (< 3) aren't in school",
     ["AGEP", "EDU"]),
    ("w", "wealthy_poor_POVPIP", "Individuals in top 5% income backet (> $300K) aren't in poverty",
     ["PINCP", "POVPIP"]),
    ("w", "wealthy_poor_DECILE",
     "Individuals in top 5% income backet (> $300K) aren't in the lowest income deciles",
     ["PINCP", "PINCP_DECILE"]),
    ("w", "invalid_INDP", "Industry codes must be valid; see data dictionary",
     ["INDP"]),
    ("w", "invalid_INDP_CAT",
     "Industry codes should agree with industry categories; see data dictionary",
     ["INDP", "INDP_CAT"]),
    ("h", "too_many_children",
     "Adults needed: Family size must be at least one greater than number of children",
     ["NOC", "NPF"]),
    ("h", "gq_own_jail",
     "Inmates don't own jails, patients don't own hospitals: Group quarters residents aren't owners",
     ["HOUSING_TYPE", "OWN_RENT"]),
    ("h", "gq_own_dorm",
     "Students don't own dorms, soldiers don't own barracks: Group quarters residents aren't owners",
     ["HOUSING_TYPE", "OWN_RENT"]),
    ("h", "gq_h_family_NPF",
     "Individuals who live in group quarters aren't considered family households",
     ["HOUSING_TYPE", "NPF"]),
    ("h", "gq_h_family_NOC",
     "Individuals who live in group quarters aren't considered family households",
     ["HOUSING_TYPE", "NOC"]),
    ("h", "gq_ro_family_NPF",
     "Individuals who live in group quarters aren't considered family households",
     ["HOUSING_TYPE", "NPF"]),
    ("h", "gq_ro_family_NOC",
     "Individuals who live in group quarters aren't considered family households",
     ["HOUSING_TYPE", "NOC"]),
    ("h", "house_NOC", "Individuals who live in houses must provide number of children",
     ["HOUSING_TYPE", "NOC"]),
    ("h", "house_OWN_RENT", "Individuals who live in houses must specify if they rent or own",
     ["HOUSING_TYPE", "OWN_RENT"]),
]


class Inconsistencies:

    def __init__(self, synthetic_data: pd.DataFrame, out_directory: Path):
        self.s = synthetic_data
        self.out_path = out_directory

        # dict containing headers and paragraphs for each inconsistency group
        # this is used for populating report user interface
        self.report_help = {
            'age': ('Age-Based Inconsistencies',
                    'These inconsistencies deal with the AGE feature; records with '
                    'age-based inconsistencies might have children who are married, '
                    'or infants with high school diplomas'),
            'work': ('Work-Based Inconsistencies',
                     'These inconsistencies deal with the work and finance features; '
                     'records with work-based inconsistencies might have high incomes '
                     'while being in poverty, or have conflicts between their industry '
                     'code and industry category.'),
            'housing': ('Housing-Based Inconsistencies',
                        'These inconsistencies deal with housing and family features; '
                        'records with household-based inconsistencies might have more '
                        'children in the house than the total household size, or be '
                        'residents of group quarters (such as prison inmates) who are '
                        'listed as owning their residences.')
        }

        # dict containing summary of the statistics gathered while computing inconsistencies.
        # this is used for populating report user interface and json report.
        self.stats = {
            'summary': [],
            'age': [],
            'work': [],
            'housing': []
        }

        # json report data
        self.report_data = {k: {'title': v[0], 'description': v[1], 'inconsistencies': []}
                            for k, v in self.report_help.items()}
        self.report_data['summary'] = []

    def compute(self):
        # inconsistency names
        ic_names = [i[NAME] for i in ic_types]
        fl = self.s.columns.tolist()  # features list

        # inconsistency dictionary--stores lists of violators
        # key = ic name, value = list of record ids that violate the ic
        ic_dict = {name: [] for name in ic_names}

        # look through records, register violations for each row
        # i = record id, r = record values
        for i, r in self.s.iterrows():
            # -------------------age related inconsistencies---------------
            if "AGEP" in fl and r["AGEP"] < 15:
                if "DVET" in fl and not (r["DVET"] == 'N'):
                    ic_dict["child_DVET"].append(i)
                if "MSP" in fl and not (r["MSP"] == 'N'):
                    ic_dict["child_MSP"].append(i)
                if "PINCP" in fl and not (r["PINCP"] == 'N'):
                    ic_dict["child_PINCP"].append(i)
                if "PINCP_DECILE" in fl and not (r["PINCP_DECILE"] == 'N'):
                    ic_dict["child_PINCP_DECILE"].append(i)
                if "INDP" in fl and not (r["INDP"] == 'N'):
                    ic_dict["child_INDP"].append(i)
                if "INDP_CAT" in fl and not (r["INDP_CAT"] == 'N'):
                    ic_dict["child_INDP_CAT"].append(i)
                if "EDU" in fl and not (r["EDU"] == 'N') and not (int(r["EDU"]) < 12):
                    ic_dict["child_phd"].append(i)

                if r["AGEP"] < 10:
                    # if "NOC" in fl and not (r["NOC"] == 'N'):
                    #     ic_dict["child_NOC"].append(i)

                    if r["AGEP"] < 5:
                        if "DPHY" in fl and not (r["DPHY"] == 'N'):
                            ic_dict["toddler_DPHY"].append(i)
                        if "DREM" in fl and not (r["DREM"] == 'N'):
                            ic_dict["toddler_DREM"].append(i)
                        if "EDU" in fl and not (r["EDU"] == 'N') and not (int(r["EDU"]) < 5):
                            ic_dict["toddler_diploma"].append(i)

                        if r["AGEP"] < 3:
                            if "EDU" in fl and not (r["EDU"] == 'N'):
                                ic_dict["infant_EDU"].append(i)

            if not ("AGEP" in fl):
                # This forces agreement on MSP, PINCP and PINCP_DECILE if at least 2 exist.
                if ("MSP" in fl and (r["MSP"] == 'N')) and (
                        ("PINCP" in fl and not (r["PINCP"] == 'N')) or (
                        "PINCP_DECILE" in fl and not (r["PINCP_DECILE"] == 'N'))):
                    ic_dict["adult_child"].append(i)
                if ("MSP" in fl and not (r["MSP"] == 'N')) and (
                        ("PINCP" in fl and (r["PINCP"] == 'N')) or (
                        "PINCP_DECILE" in fl and (r["PINCP_DECILE"] == 'N'))):
                    ic_dict["adult_child"].append(i)
                if not ("MSP" in fl) and ("PINCP" in fl) and ("PINCP_DECILE" in fl):
                    if ((r["PINCP"] == 'N') and not (r["PINCP_DECILE"] == 'N')) or (
                            not (r["PINCP"] == 'N') and (r["PINCP_DECILE"] == 'N')):
                        ic_dict["adult_child"].append(i)

            # this catches adults who still have the child 'N' for their features.
            if "AGEP" in fl and r["AGEP"] > 15:
                if ("MSP" in fl and (r["MSP"] == 'N')) or (
                        "PINCP" in fl and (r["PINCP"] == 'N')) or (
                        "PINCP_DECILE" in fl and (r["PINCP_DECILE"] == 'N')) or (
                        "EDU" in fl and (r["EDU"] == 'N')) or (
                        "DPHY" in fl and (r["DPHY"] == 'N')) or (
                        "DREM" in fl and (r["DREM"] == 'N')):
                    ic_dict["adult_N"].append(i)


            # -------------------work and finance related inconsistencies---------------
            # income > 300K
            if "PINCP" in fl and not (r["PINCP"] == 'N') and float(r["PINCP"]) > 3000000:
                if "POVPIP" in fl and not (r["POVPIP"] == "501"):
                    ic_dict["wealthy_poor_POVPIP"].append(i)
                if "PINCP_DECILE" in fl and not (int(r["PINCP_DECILE"]) > 1):
                    ic_dict["wealthy_poor_POVPIP"].append(i)

            # this currently just checks null value agreement,
            # if one is null the other should be too
            if "INDP" in fl and "INDP_CAT" in fl:
                if ((r["INDP"] == "N") and (r["INDP_CAT"] != "N") or (r["INDP"] != "N") and (
                        r["INDP_CAT"] == "N")):
                    ic_dict["invalid_INDP_CAT"].append(i)
                    # TODO: add INDP CAT and INDP code agreement checks

            # -------------------housing and family related inconsistencies---------------
            if ("NOC" in fl) and ("NPF" in fl) and (r["NOC"] != "N") and (r["NPF"] != "N"):
                if not (int(r["NOC"]) < int(r["NPF"])):
                    ic_dict["too_many_children"].append(i)

            # if group quarters (according to HOUSING_TYPE)
            if ("HOUSING_TYPE" in fl) and (r["HOUSING_TYPE"] > 1):
                if "NOC" in fl and not (r["NOC"] == 'N'):
                    ic_dict["gq_h_family_NOC"].append(i)

                if "NPF" in fl and not (r["NPF"] == 'N'):
                    ic_dict["gq_h_family_NPF"].append(i)

                if "OWN_RENT" in fl and (r["OWN_RENT"] == 2):
                    ic_dict["gq_own_jail"].append(i)

                if (r["HOUSING_TYPE"] == 2) and "OWN_RENT" in fl and (r["OWN_RENT"] == 1):
                    ic_dict["gq_own_jail"].append(i)

                if (r["HOUSING_TYPE"] == 3) and "OWN_RENT" in fl and (r["OWN_RENT"] == 1):
                    ic_dict["gq_own_dorm"].append(i)

            # if house (according to HOUSING_TYPE)
            if ("HOUSING_TYPE" in fl) and (int(r["HOUSING_TYPE"]) == 1):
                if "OWN_RENT" in fl and (r["OWN_RENT"] == 0):
                    ic_dict["house_OWN_RENT"].append(i)

                if "NOC" in fl and (r["NOC"] == 'N'):
                    ic_dict["house_NOC"].append(i)

            # if group quarters (according to RENT_OWN)
            if ("RENT_OWN" in fl) and (int(r["RENT_OWN"]) == 0):
                if "NOC" in fl and not (r["NOC"] == 'N'):
                    ic_dict["gq_ro_family_NOC"].append(i)

                if "NPF" in fl and not (r["NPF"] == 'N'):
                    ic_dict["gq_ro_family_NPF"].append(i)

        # ------- Output Statistics ------------------------
        [n, f] = self.s.shape

        # ------- Compute Age-based Inconsistencies------------
        ic_age = dict()
        age_violators = set()  # set of records indexes that have at least one age ic

        age_path = Path(self.out_path, 'age')
        create_path(age_path)
        for i in ic_types:
            if i[GROUP] == 'a':  # cycle through age ic's
                ic_age[i[NAME]] = ic_dict[i[NAME]]
                if len(ic_dict[i[NAME]]) > 0:  # if this ic actually occurred
                    age_violators = age_violators.union(ic_dict[i[NAME]])
                    example_row = self.s.loc[[ic_dict[i[NAME]][0]], :]

                    ic_data = [i[NAME], i[DESCRIPTION], i[FEATURES], f'{len(ic_dict[i[NAME]])} '
                                                                     f'violations', example_row]
                    self.stats['age'].append(
                        ic_data.copy()
                    )
                    row_path = Path(age_path, f'{i[NAME]}_example.csv')
                    example_row.to_csv(row_path)
                    ic_data[4] = row_path
                    self.report_data['age']['inconsistencies'].append(
                        {'inconsistency_name': ic_data[0],
                         'inconsistency_description': ic_data[1],
                         'inconsistency_features': ic_data[2],
                         'inconsistency_violations': int(ic_data[3].split(' ')[0]),
                         'inconsistent_data_indexes': ic_dict[i[NAME]],
                         'inconsistent_record_example': relative_path(row_path, level=3)}
                    )

        # ------- Compute work-based Inconsistencies------------
        ic_work = dict()
        work_violators = set()  # set of records that have at least one work ic

        age_path = Path(self.out_path, 'work')
        create_path(age_path)
        for i in ic_types:
            if i[0] == 'w':
                ic_work[i[NAME]] = ic_dict[i[NAME]]
                if len(ic_dict[i[NAME]]) > 0:
                    work_violators = work_violators.union(ic_dict[i[NAME]])
                    example_row = self.s.loc[[ic_dict[i[NAME]][0]], :]

                    ic_data = [i[NAME], i[DESCRIPTION], i[FEATURES], f'{len(ic_dict[i[NAME]])} '
                                                                     f'violations', example_row]
                    self.stats['work'].append(
                        ic_data.copy()
                    )
                    row_path = Path(age_path, f'{i[NAME]}_example.csv')
                    example_row.to_csv(row_path)
                    ic_data[4] = row_path
                    self.report_data['age']['inconsistencies'].append(
                        {'inconsistency_name': ic_data[0],
                         'inconsistency_description': ic_data[1],
                         'inconsistency_features': ic_data[2],
                         'inconsistency_violations': int(ic_data[3].split(' ')[0]),
                         'inconsistent_data_indexes': ic_dict[i[NAME]],
                         'inconsistent_record_example': relative_path(row_path, level=3)}
                    )

        # ------- Compute housing-based Inconsistencies------------
        ic_house = dict()
        house_violators = set()  # set of records that have at least one house ic

        age_path = Path(self.out_path, 'work')
        create_path(age_path)
        for i in ic_types:
            if i[0] == 'h':
                if len(ic_dict[i[NAME]]) > 0:
                    ic_house[i[NAME]] = ic_dict[i[NAME]]
                    house_violators = house_violators.union(ic_dict[i[NAME]])
                    example_row = self.s.loc[[ic_dict[i[NAME]][0]], :]

                    ic_data = [i[NAME], i[DESCRIPTION], i[FEATURES], f'{len(ic_dict[i[NAME]])} violations',
                               example_row]
                    self.stats['housing'].append(
                        ic_data.copy()
                    )
                    row_path = Path(age_path, f'{i[NAME]}_example.csv')
                    example_row.to_csv(row_path)
                    ic_data[4] = row_path
                    self.report_data['age']['inconsistencies'].append(
                        {'inconsistency_name': ic_data[0],
                         'inconsistency_description': ic_data[1],
                         'inconsistency_features': ic_data[2],
                         'inconsistency_violations': int(ic_data[3].split(' ')[0]),
                         'inconsistent_data_indexes': ic_dict[i[NAME]],
                         'inconsistent_record_example': relative_path(row_path, level=3)}
                    )

        # -------- Compute overall stats---------------------
        # set of records that have at least one ic of any type
        total_violators = age_violators.union(work_violators).union(house_violators)

        overall_stats = [['Age', len(age_violators), round((100 * len(age_violators)) / n, 1)],
                         ['Work', len(work_violators), round((100 * len(work_violators)) / n, 1)],
                         ['Housing', len(house_violators), round((100 * len(house_violators)) / n, 1)]]
        self.stats['summary'] = [{'Inconsistency Group': r[0],
                                  'Number of Records Inconsistent': r[1],
                                  'Percent Records Inconsistent': f'{r[2]}%'}
                                 for r in overall_stats]
        self.report_data['summary'] = [{'Inconsistency Group': r[0],
                                        'Number of Records Inconsistent': r[1],
                                        'Percent Records Inconsistent': r[2]}
                                 for r in overall_stats]

