from typing import Tuple, Dict
from pathlib import Path
import pandas as pd

from sdnist.metrics.inconsistency import Inconsistencies
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket

from sdnist.utils import *


class InconsistenciesReport:
    def __init__(self, dataset: Dataset, ui_data: ReportUIData, report_data: ReportData):
        self.s = dataset.synthetic_data
        self.r_ui_d = ui_data
        self.rd = report_data
        self.ic = None

        self.attachments = []

        self._create()

    def _create(self):
        o_path = Path(self.r_ui_d.output_directory, 'inconsistencies')
        create_path(o_path)
        self.ic = Inconsistencies(self.s, o_path)
        self.ic.compute()

        # add json report data
        self.rd.add('inconsistencies', self.ic.report_data)
        # add ui report data
        a_sum_h = Attachment(name='Summary',
                             _data=self.ic.stats['summary'])
        self.attachments.append(a_sum_h)
        for k, v in self.ic.report_help.items():
            # attachment header
            ah = Attachment(name=v[0],
                            _data=v[1],
                            _type=AttachmentType.String)
            self.attachments.append(ah)
            for stat in self.ic.stats[k]:
                name = stat[0]
                desc = stat[1]
                features = stat[2]
                s_data = stat[3]
                s_example = stat[4]

                an = Attachment(name=None,
                                _data=f'h4{name}: {desc}',
                                _type=AttachmentType.String)
                # a_desc = Attachment(name=None,
                #                     _data=desc,
                #                     _type=AttachmentType.String)
                a_data = Attachment(name='--no-brake--',
                                    _data=s_data,
                                    _type=AttachmentType.String)
                a_ex_txt = Attachment(name=None,
                                      _data='Example:',
                                      _type=AttachmentType.String)

                # example data
                def build_row_dict(r, add_min=False):
                    res = {'Feature': str(r[0]),
                           'Value': int(r[1]) if str(r[1]).isnumeric() else str(r[1])}
                    if add_min:
                        res['min_idx'] = True
                    return res

                e_d = [build_row_dict(r, True)
                       if r[0] in features else build_row_dict(r)
                       for i, r in s_example.iterrows()]
                a_example = Attachment(name=None,
                                       _data=e_d)
                self.attachments.extend([an, a_data, a_ex_txt, a_example])

    def add_to_ui(self):
        self.r_ui_d.add(UtilityScorePacket('Inconsistencies',
                                           None,
                                           self.attachments))
#from sdnist.report import Dataset
#from sdnist.report.report_data import \
#    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType, \
#    DatasetType, DataDescriptionPacket


# def find_inconsistencies(synthetic_data: pd.DataFrame) -> Dict[any, any]:
#     """
#     Help code:
#         dc = sd.columns.tolist()
#         for i, r in sd.iterrows():
#             if 'HOUSING_TYPE' in dc and 'OWN_RENT' in dc:
#                 ht = r['HOUSING_TYPE']
#                 orent = r['OWN_RENT']
#
#                 if not ((ht in [2, 3] and orent == 0)
#                         or (ht == 1 and orent in [1, 2])):
#                     # update inconsistency count in some dict
#
#             if 'MSP' in dc and 'AGEP' in dc:
#                 msp = r['MSP']
#                 age = r['AGEP']
#
#                 if not ((age < 15 and msp == 'N')
#                         or (age >= 15 and msp != 'N')):
#                     # update inconsistency count in some dict
#
#                     #Dictionary format:  One dictionary, keys are inconsistency types  (NAME, [list of features]), values are lists of record index (i) with that problem
#     """
#     """
#         (non-comprehensive) Basic Consistency Constraint Check:
#             --- Children can't be military veteran, married, income, industry, industry category, can't have their own children (etc). (double check the cut-offs for each in the real data)
#             --- Housing Type and Rent/Own should agree
#             --- Poverty and Income and Income Decile shouldn't be wildly, wildly out of whack with each other (we can check the ground truth data for bounds on the ratios)
#             --- Family size should always be at least one greater than number of own children (double check this is true in the data)
#             ---All numerical features should have max and min values (remember NOC NPF are numerical) and make sure things are in bounds (ideally do this in validation)
#             ---Shouldn't make up new industry codes or PUMA codes that don't exist.  (in fact, might be a bit fun if they make up a PUMA to tell them where their made up PUMA is located, if there's a crosswalk/look up file that's easy for us to use to that purpose)
#             Things we aren't checking
#             --industry category and industry agree
#             --education and age agree
#             --------
#             Report format (group failures into the three categories above: Children, Work and Financials, Housing and Family):
#             P% of records failed This Check:
#             Example inconsistent record (conflict highlighted):
#             P% of records failed This Check
#             Example Inconsistent record (conflict highlighted):
#     """
#     # synethric data
#     sd = synthetic_data
#
#     #list of features that were actually included in this data set
#     features_list = sd.columns.tolist()
#     fl = features_list
#
#
#     #list of tuples with all the information associated with each inconsistency (abbreviated ic)
#     #[(category for ic, name for ic, explanation string for ic, features to highlight for ic)]
#     [GROUP, NAME, DESCRIPTION, FEATURES] = [0, 1, 2, 3]
#     ic_types = [ \
#                 ("a", "child_DVET", "Children (< 15) can't be disabled military veterans", ["AGEP","DVET"]), \
#                 ("a", "child_MSP", "Children (< 15) can't be married", ["AGEP","MSP"]), \
#                 ("a", "child_PINCP", "Children (< 15) don't have personal incomes", ["AGEP","PINCP"]), \
#                 ("a", "child_PINCP_DECILE", "Children (< 15) don't have personal incomes", ["AGEP","PINCP_DECILE"]), \
#                 ("a", "child_INDP", "Children (< 15) don't have work industries", ["AGEP","INDP"]), \
#                 ("a", "child_INDP_CAT", "Children (< 15) don't have work industries", ["AGEP","INDP_CAT"]), \
#                 ("a", "child_phd", "Children (< 15) don't have PhDs", ["AGEP","EDU"]), \
#                 ("a", "child_NOC", "Children (< 10) don't have children", ["AGEP","NOC"]), \
#                 ("a", "toddler_DPHY", "Toddlers (< 5) naturally toddle, it's not a physical disability", ["AGEP","DPHY"]), \
#                 ("a", "toddler_DREM",  "Toddlers (< 5) are naturally forgetful, it's not a cognitive disability", ["AGEP","DREM"]), \
#                 ("a", "toddler_diploma",  "Toddlers (< 5) don't have high school diplomas", ["AGEP","EDU"]), \
#                 ("a", "infant_EDU", "Infants (< 3) aren't in school", ["AGEP","EDU"]), \
#                 ("w", "wealthy_poor_POVPIP", "Individuals in top 5% income backet (> $300K) aren't in poverty", ["PINCP","POVPIP"]), \
#                 ("w", "wealthy_poor_DECILE", "Individuals in top 5% income backet (> $300K) aren't in the lowest income deciles", ["PINCP","PINCP_DECILE"]), \
#                 ("w","invalid_INDP", "Industry codes must be valid; see data dictionary", ["INDP"]), \
#                 ("w","invalid_INDP_CAT", "Industry codes should agree with industry categories; see data dictionary", ["INDP","INDP_CAT"]), \
#                 ("h", "too_many_children", "Adults needed: Family size must be at least one greater than number of children", ["NOC","NPF"]), \
#                 ("h", "gq_own_jail", "Inmates don't own jails, patients don't own hospitals: Group quarters residents aren't owners", ["HOUSING_TYPE","OWN_RENT"]), \
#                 ("h", "gq_own_dorm", "Students don't own dorms, soldiers don't own barracks: Group quarters residents aren't owners", ["HOUSING_TYPE","OWN_RENT"]), \
#                 ("h", "gq_h_family_NPF", "Individuals who live in group quarters aren't considered family households", ["HOUSING_TYPE","NPF"]), \
#                 ("h", "gq_h_family_NOC", "Individuals who live in group quarters aren't considered family households", ["HOUSING_TYPE","NOC"]), \
#                 ("h", "gq_ro_family_NPF", "Individuals who live in group quarters aren't considered family households", ["HOUSING_TYPE","NPF"]), \
#                 ("h", "gq_ro_family_NOC", "Individuals who live in group quarters aren't considered family households", ["HOUSING_TYPE","NOC"]), \
#                 ("h", "house_NOC", "Individuals who live in houses must provide number of children", ["HOUSING_TYPE","NOC"]), \
#                 ("h", "house_OWN_RENT", "Individuals who live in houses must specify if they rent or own", ["HOUSING_TYPE","OWN_RENT"]), \
#                 ]
#
#     #inconsistency names
#     ic_names = [i[NAME] for i in ic_types]
#
#     #incostency dictionary--stores lists of violators
#     ic_dict = dict([ (name, []) for name in ic_names])  # key = ic name, value = list of record ids that violate the ic
#
#
#     #look through records, register violations for each row
#     for i, r in sd.iterrows():   #i = record id, r = record values
#
#
#         #-------------------age related inconsistencies---------------
#         if "AGEP" in fl and r["AGEP"] < 15:
#             if "DVET" in fl and not (r["DVET"] == 'N'):
#                 ic_dict["child_DVET"].append(i)
#             if "MSP" in fl and not (r["MSP"] == 'N'):
#                 ic_dict["child_MSP"].append(i)
#             if "PINCP" in fl and not (r["PINCP"] == 'N'):
#                 ic_dict["child_PINCP"].append(i)
#             if "PINCP_DECILE" in fl and not (r["PINCP_DECILE"] == 'N'):
#                 ic_dict["child_PINCP_DECILE"].append(i)
#             if "INDP" in fl and not (r["INDP"] == 'N'):
#                 ic_dict["child_INDP"].append(i)
#             if "INDP_CAT" in fl and not (r["INDP_CAT"] == 'N'):
#                 ic_dict["child_INDP_CAT"].append(i)
#             if "EDU" in fl and not (r["EDU"] == 'N') and not (int(r["EDU"]) < 12):
#                 ic_dict["child_phd"].append(i)
#
#             if r["AGEP"] < 10:
#                 if "NOC" in fl and not (r["NOC"] == 'N'):
#                     ic_dict["child_NOC"].append(i)
#
#                 if r["AGEP"] < 5:
#                     if "DPHY" in fl and not (r["DPHY"] == 'N'):
#                         ic_dict["toddler_DPHY"].append(i)
#                     if "DREM" in fl and not (r["DREM"] == 'N'):
#                         ic_dict["toddler_DREM"].append(i)
#                     if "EDU" in fl and not (r["EDU"] == 'N') and not (int(r["EDU"]) < 5):
#                         ic_dict["toddler_diploma"].append(i)
#
#                     if r["AGEP"] < 3:
#                         if "EDU" in fl and not (r["EDU"] == 'N'):
#                             ic_dict["infant_EDU"].append(i)
#
#
#         #-------------------work and finance related inconsistencies---------------
#         if "PINCP" in fl and not (r["PINCP"] == 'N') and  float(r["PINCP"]) > 3000000:  #income > 300K
#             if "POVPIP" in fl and not(r["POVPIP"] == "501"):
#                 ic_dict["wealthy_poor_POVPIP"].append(i)
#             if "PINCP_DECILE" in fl and not(int(r["PINCP_DECILE"]) > 1 ):
#                 ic_dict["wealthy_poor_POVPIP"].append(i)
#
#         if "INDP" and "INDP_CAT" in fl: #this currently just checks null value agreemnent, if one is null the other should be too
#             if ((r["INDP"] == "N") and (r["INDP_CAT"] != "N") or (r["INDP"] != "N") and (r["INDP_CAT"] == "N")):
#                 ic_dict["invalid_INDP_CAT"].append(i)
#                  #TODO: add INDP CAT and INDP code agreement checks
#
#
#         #-------------------housing and family related inconsistencies---------------
#
#         if ("NOC" in fl) and ("NPF" in fl) and (r["NOC"] != "N") and (r["NPF"] != "N"):
#             if not (r["NOC"] < r["NPF"]):
#                 ic_dict["too_many_children"].append(i)
#
#
#         if ("HOUSING_TYPE" in fl) and (r["HOUSING_TYPE"] > 1):  #if group quarters (according to HOUSING_TYPE)
#             if "NOC" in fl and not (r["NOC"] == 'N'):
#                 ic_dict["gq_h_family_NOC"].append(i)
#
#             if "NPF" in fl and not (r["NPF"] == 'N'):
#                 ic_dict["gq_h_family_NPF"].append(i)
#
#             if  "OWN_RENT" in fl and (r["OWN_RENT"] == 2):
#                 ic_dict["gq_own_jail"].append(i)
#
#             if (r["HOUSING_TYPE"] == 2) and "OWN_RENT" in fl and (r["OWN_RENT"] == 1):
#                 ic_dict["gq_own_jail"].append(i)
#
#             if (r["HOUSING_TYPE"] == 3) and "OWN_RENT" in fl and (r["OWN_RENT"] == 1):
#                 ic_dict["gq_own_dorm"].append(i)
#
#
#
#         if ("HOUSING_TYPE" in fl) and (int(r["HOUSING_TYPE"]) == 1): #if house (according to HOUSING_TYPE)
#             if  "OWN_RENT" in fl and (r["OWN_RENT"] == 0):
#                 ic_dict["house_RENT_OWN"].append(i)
#
#             if "NOC" in fl and (r["NOC"] == 'N'):
#                 ic_dict["house_NOC"].append(i)
#
#
#
#         if ("RENT_OWN" in fl) and (int(r["RENT_OWN"]) == 0): #if group quarters (according to RENT_OWN)
#             if "NOC" in fl and not (r["NOC"] == 'N'):
#                 ic_dict["gq_ro_family_NOC"].append(i)
#
#             if "NPF" in fl and not (r["NPF"] == 'N'):
#                 ic_dict["gq_ro_family_NPF"].append(i)
#
#
#
#     #------- Output Statistics ------------------------
#
#
#     [n,f] = sd.shape
#
#     #------- Compute Age-based Inconsistencies------------
#     ic_age = dict()
#     age_violators = set()  #set of records indexes that have at least one age ic
#     age_report = "\n\n\n ----------AGE-BASED INCONSISTENCIES---------\n"+\
#     "These inconsistencies deal with the AGE feature; records with age-based inconsistencies might have children who are married, or infants with high school diplomas. \n \n"
#
#     for i in ic_types:
#         if i[GROUP] == 'a':  #cycle through age ic's
#             ic_age[i[NAME]] = ic_dict[i[NAME]]
#             if len(ic_dict[i[NAME]]) > 0: #if this ic actually occurred
#                 age_violators = age_violators.union(ic_dict[i[NAME]])
#                 example = sd.loc[ic_dict[i[NAME]][0],:]  #get an example of this ic
#                 age_report = age_report + i[NAME] + ":\n " + i[DESCRIPTION] + "\n"+ \
#                              "   " + str(len(ic_dict[i[NAME]])) + " violations\n" + \
#                              "   Example: "+ str(example) +" \n\n"  #TODO highlight the i[FEATURES]
#
#     #------- Compute work-based Inconsistencies------------
#     ic_work = dict()
#     work_violators = set()  #set of records that have at least one work ic
#     work_report = "\n\n\n ----------WORK-BASED INCONSISTENCIES---------\n"+\
#         "These inconsistencies deal with the work and finance features; records with work-based inconsistencies might have high incomes while being in poverty, or have conflicts between their industry code and industry category. \n \n"
#
#     for i in ic_types:
#         if i[0] == 'w':
#             ic_work[i[NAME]] = ic_dict[i[NAME]]
#             if len(ic_dict[i[NAME]]) > 0:
#                 work_violators = work_violators.union(ic_dict[i[NAME]])
#                 example = sd.loc[ic_dict[i[NAME]][0],:]
#                 work_report = work_report + i[NAME] + ": \n" + i[DESCRIPTION] + "\n"+ \
#                              "   " + str(len(ic_dict[i[NAME]])) + " violations\n" + \
#                              "   Example: "+ str(example) +"\n\n" #TODO print a record from the dictionary list of indexes, highlight the i[FEATURES]
#
#     #------- Compute housing-based Inconsistencies------------
#     ic_house = dict()
#     house_violators = set()  #set of records that have at least one house ic
#     house_report = "\n\n\n ----------HOUSEHOLD-BASED INCONSISTENCIES---------\n"+\
#     "These inconsistencies deal with housing and family features; records with household-based inconsistencies might have more children in the house than the total household size, or be residents of group quarters (such as prison inmates) who are listed as owning their reidences.  \n \n"
#
#     for i in ic_types:
#         if i[0] == 'h':
#             if len(ic_dict[i[NAME]]) > 0:
#                 ic_house[i[NAME]] = ic_dict[i[NAME]]
#                 house_violators = house_violators.union(ic_dict[i[NAME]])
#                 example = sd.loc[ic_dict[i[NAME]][0],:]
#                 house_report = house_report + i[NAME] + ": \n" + i[DESCRIPTION] + "\n"+ \
#                              "   " + str(len(ic_dict[i[NAME]])) + " violations\n" + \
#                              "   Example: " +str(example) +" \n\n" #TODO print a record from the dictionary list of indexes, highlight the i[FEATURES]
#
#     #-------- Compute overall stats---------------------
#
#     total_violators = age_violators.union(work_violators).union(house_violators)  #set of records that have at least one ic of any type
#
#     Overall_Stats = "Age-based Inconsistencies: " + str(len(age_violators)) + " records, " +  str(round((100*len(age_violators))/n,1)) + "% of data\n" +\
#                     "Work-based Inconsistencies: " + str(len(work_violators)) + " records, " + str(round((100*len(work_violators))/n,1)) + "% of data\n" +\
#                     "Household-based Inconsistencies: " + str(len(house_violators)) + " records, " + str(round((100*len(house_violators))/n,1)) + "% of data\n" +\
#                     "Total Inconsistencies: " + str(len(total_violators)) + " records, " + str(round((100*len(total_violators))/n,1)) + "% of data"
#
#
#     print(Overall_Stats + age_report + work_report + house_report)
#
#
#     #as printlines, go ahead and print a premable that this section is not complete, but should help catch issues. some models
#     #are better about these than others.   They may want to look for more issues themselves.
#
#
#
#
#
#     ### END CODE HERE
#
#     return ic_dict
#
#
#
#
#
#
#
#
# def inconsistencies():
#
#
#     #synthetic_data = pd.read_csv( "/Users/ctask/Desktop/NIST_Code/synthetic_data/SMOTE_oversample_ma.csv")
#     synthetic_data = pd.read_csv( "/Users/ctask/Desktop/NIST_Code/synthetic_data/SMOTE_oversample_na.csv")
#
#     # find inconsistencies in original non-transformed and un-binned synthetic data
#     incons = find_inconsistencies(synthetic_data)
#     print("victory!", synthetic_data.shape)
#
#     # TODO: Add incons to UI
#
# #Run the program:
# inconsistencies()
#
#
#
# # def inconsistencies(dataset: Dataset, ui_data: ReportUIData, report_data: ReportData) \
# #         -> Tuple[ReportUIData, ReportData]:
# #     ds = dataset
# #     r_ui_d = ui_data
# #     rd = report_data
#
# #     # find inconsistencies in original non-transformed and un-binned synthetic data
# #     incons = find_inconsistencies(dataset.synthetic_data)
#
# #     # TODO: Add incons to UI
#
# #     return ui_data, report_data
