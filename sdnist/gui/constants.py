from pathlib import Path
# Target Data Root
cwd = Path(__file__).parent.parent.parent

DATA_ROOT_PATH = Path(cwd, 'diverse_communities_data_excerpts')

# SDNIST Data Evaluation Report
DER_FULL = 'Data Evaluation Report'
REPORT_DIR_PREFIX = 'SDNIST_DER'
ARCHIVE_DIR_PREFIX = 'SDNIST_ARCHIVE'
METAREPORT_DIR_PREFIX = 'SDNIST_METAREPORT'

MA2019 = 'ma2019'
TX2019 = 'tx2019'
NATIONAL2019 = 'national2019'

# Target datasets
target_datasets = [MA2019, TX2019, NATIONAL2019]

# Feature Sets
all_features = ["PUMA", "AGEP", "SEX", "MSP", "HISP",
                "RAC1P", "NOC", "NPF", "HOUSING_TYPE",
                "OWN_RENT", "DENSITY", "INDP", "INDP_CAT",
                "EDU", "PINCP", "PINCP_DECILE", "POVPIP",
                "DVET", "DREM", "DPHY", "DEYE", "DEAR",
                "WGTP", "PWGTP"]
simple_features = ["PUMA", "AGEP", "SEX", "MSP", "HISP",
                "RAC1P", "NOC", "NPF", "HOUSING_TYPE",
                "OWN_RENT", "DENSITY", "INDP_CAT",
                "EDU", "PINCP", "PINCP_DECILE", "POVPIP",
                "DVET", "DREM", "DPHY", "DEYE", "DEAR"]
demographic_focused = ["AGEP", "SEX", "MSP", "RAC1P", "HOUSING_TYPE",
                        "OWN_RENT", "EDU", "PINCP_DECILE",
                        "DVET", "DEYE"]
family_focused = ["PUMA", "AGEP", "SEX", "MSP", "HISP", "RAC1P",
                  "NOC", "NPF", "OWN_RENT", "PINCP_DECILE", "POVPIP"]
industry_focused = ["PUMA", "SEX", "MSP", "HISP", "RAC1P",
                    "OWN_RENT", "INDP_CAT", "EDU", "PINCP_DECILE"]
detailed_industry_focused = ["PUMA", "SEX", "MSP", "HISP", "RAC1P",
                             "OWN_RENT", "INDP", "EDU",
                             "PINCP_DECILE"]
small_categorical = ["SEX", "RAC1P", "OWN_RENT",
                     "PINCP_DECILE", "PUMA"]
tiny_categorical = ["RAC1P", 'PUMA']
