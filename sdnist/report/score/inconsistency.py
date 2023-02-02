from typing import Tuple, Dict

import pandas as pd

from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket


def find_inconsistencies(synthetic_data: pd.DataFrame) -> Dict[any, any]:
    """
    Help code:
        dc = sd.columns.tolist()
        for i, r in sd.iterrows():
            if 'HOUSING_TYPE' in dc and 'OWN_RENT' in dc:
                ht = r['HOUSING_TYPE']
                orent = r['OWN_RENT']

                if not ((ht in [2, 3] and orent == 0)
                        or (ht == 1 and orent in [1, 2])):
                    # update inconsistency count in some dict

            if 'MSP' in dc and 'AGEP' in dc:
                msp = r['MSP']
                age = r['AGEP']

                if not ((age < 15 and msp == 'N')
                        or (age >= 15 and msp != 'N')):
                    # update inconsistency count in some dict
                    
                    #Dictionary format:  One dictionary, keys are inconsistency types  (NAME, [list of features]), values are lists of record index (i) with that problem  
    """
    """
        (non-comprehensive) Basic Consistency Constraint Check:
            --- Children can't be military veteran, married, income, industry, industry category, can't have their own children (etc). (double check the cut-offs for each in the real data)
            --- Housing Type and Rent/Own should agree
            --- Poverty and Income and Income Decile shouldn't be wildly, wildly out of whack with each other (we can check the ground truth data for bounds on the ratios)
            --- Family size should always be at least one greater than number of own children (double check this is true in the data)
            ---All numerical features should have max and min values (remember NOC NPF are numerical) and make sure things are in bounds (ideally do this in validation)
            ---Shouldn't make up new industry codes or PUMA codes that don't exist.  (in fact, might be a bit fun if they make up a PUMA to tell them where their made up PUMA is located, if there's a crosswalk/look up file that's easy for us to use to that purpose)
            Things we aren't checking
            --industry category and industry agree
            --education and age agree
            --------
            Report format (group failures into the four categories above: Children, Housing Type, Financials, Family size):
            P% of records failed This Check:
            Example inconsistent record (conflict highlighted):
            P% of records failed This Check
            Example Inconsistent record (conflict highlighted):
    """
    # dictionary for storing inconsistency counts
    ic = dict()
    sd = synthetic_data

    ### START CODE HERE

    ### END CODE HERE

    return ic


def inconsistencies(dataset: Dataset, ui_data: ReportUIData, report_data: ReportData) \
        -> Tuple[ReportUIData, ReportData]:
    ds = dataset
    r_ui_d = ui_data
    rd = report_data

    # find inconsistencies in original non-transformed and un-binned synthetic data
    incons = find_inconsistencies(dataset.synthetic_data)

    # TODO: Add incons to UI

    return ui_data, report_data
