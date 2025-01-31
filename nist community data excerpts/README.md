# The NIST Data Excerpt Benchmarks 

The NIST Data Excerpts are curated subsets of publicly released tabular data sets, drawn from real households and businesses in the U.S. The Excerpts serve as benchmark data for the [SDNist v2: Deidentified Data Report Tool](https://github.com/usnistgov/SDNist/) and are the taget data for the [2025 NIST Collaborative Researtch Cycle](https://pages.nist.gov/privacy_collaborative_research_cycle/).

The Excerpts are designed to be a resource to investigate performance of data synthesizers and similar privacy-enhancing technologies.  There are two sets of benchmark data, the ACS Data Excerpts & the SBO Data Excerpts. We provide a brief overview of each below: 


## ACS Data Excerpts

The ACS Data Excerpts are the recommended staring point for identifying and diagnosing problems in data deidentification algorithms.  They focus on a small set of challenging survey features and geographical regions (Public Use Micodata Areas). The data are drawn from real records released in the 2019 [American Community Survey](https://www.census.gov/programs-surveys/acs), a product of the US Census Bureau. 

The ACS Data Excerpts were developed to address a recurring problem identified in the NIST Differential Privacy Synthetic Data Challenge, NIST Differential Privacy Temporal Map Challenge, and the HLG-MOS Synthetic Data Test Drive. Specifically, if the data are too complex, it’s hard to tell for sure what’s going on with it. These data are designed to support a deeper and more formal understanding of algorithm behavior on real human data.

The benchmark data were designed with input from US Census Bureau experts in adaptive sampling design (consider [Coffey 2020](https://doi.org/10.1093/jssam/smz026)) and leveraged previous work on geographical differences in CART-modeled synthetic data to identify Public Use Microdata Areas (PUMAs) with challenging distributions (see Appendix B, [Abowd 2021](https://ui.adsabs.harvard.edu/link_gateway/2021arXiv211013239A/arxiv:2110.13239)).

Effectively, we attempt to provide a model-sized version of the problem that we were trying to understand. Like a ship in a bottle: pieces small enough that they can be assembled by hand, so that we can start to see how they fit together.

### Data Partitions and Area definitions
We are currently offering three geographic regions, each contained within its own directory, containing the data and a description of each PUMA within data we call "postcards". All of the data have identical schema of 24 features that are provided in a data dictionary with accompanying notes.

- `national`: 27254 records drawn from 20 PUMAs from across the United States
- `massachusetts`: 7634 records drawn from five PUMAs of communities from the North Shore to the west of the greater Boston, Massachusetts area.
- `texas`:  9276 records drawn from six PUMAs of communities surrounding Dallas-Fort Worth, Texas area

Each of the data sets comprise data from multiple PUMAs. PUMAs are designated by the US Census Bureau and designed to be "non-overlapping, statistical geographic areas that partition each state or equivalent entity into geographic areas containing no fewer than 100,000 people each." 

For each regional data set, in addition to the 2019 target data, we also include 2018 sample as a control or baseline set.  This is useful in the development of privacy leak metrics (which must be able to infer individual attributes better on the deidentified target data than on the control to be considered successful attacks).  Currently, the sdnist evaluator is only configured to run against 2019 files. Any analysis of 2018 data is entirely up to the user.

### Feature Notes
There is a data dictionary in JSON format included with the data. An overview of the features available in the ACS Excerpts is given below: 

- Geography Feature: PUMA (see note above)
- Regional Features: DENSITY (population density of PUMA, useful for distinguishing urban, suburban, and rural PUMAs)
- Industry and Education Features: EDU (highest educational attainment; it’s useful to consider this in combination with AGEP), INDP_CAT (general category of work, for example, agriculture or retail), INDP (specific category of work&mdash;this is an example of a categorical feature with very many possible values)
- Demographic Features: AGEP (age), SEX (sex), HISP (hispanic origin), RAC1P (race)
- Household Features: MSP (marital status), NOC (number of children), NPF (family size), HOUSING_TYPE (single housing unit or group quarters such as dorms, barracks, or nursing homes), OWN_RENT (own or rent housing)
- Disability Features: DREM (cognitive difficulty, binary feature), DEYE (vision difficulty, binary feature), DEAR (hearing difficulty, binary feature), DPHY (walking/movement difficulty, binary feature), DVET (disability due to military service;this is a rating value rather than a binary feature)
- Financial Features: PINCP (personal income, including wages and investment), PINCP_DECILE (person’s income discretized as a 10% percentile bin relative to the income distribution in their PUMA), POVPIP (household income as a percentage of the poverty threshold for that household (dependent on family size and other factors&mdash;households with income more than 5x the property line are given the value 501)
- Weights: Person’s weight and housing weight can be used to generate a full sample. To make a full population persons data estimate, duplicate each record the number of times indicates by its PWGHT feature.
- There exist some deterministic relationships between features (consistency constraints):
   * NPF & NOC (NPF must be greater than NOC). 
   * HOUSING_TYPE & OWN_RENT (OWN_RENT is null for group quarters).
   * AGEP dependence on many features: children (~ AGEP < 18) will have null values for many adult features, such as financials, and a maximal possible value for educational attainment dependent on age)
- Other Notes: INDP_CAT & INDP (INDP_CAT is a partitioning of the codes in INDP), PUMA & DENSITY (DENSITY is the population density of a given PUMA),  PINCP & PINCP_DECILE (PINCP_DECILE is a percentile aggregation of PINCP by PUMA)

Note: For studying tabular/histogram methods you will likely want to bin AGE into a set of ranges: [0-10], [11-20], etc.  

**Null values:** 
Different systems encode and handle null (empty) values differently; we use the literal character 'N' to represent null values throughout these data. Null values appear in columns representing categorical and numerical data. For synthesizing numerical features (PINCP, POVIP), you will likely want to convert 'N' to null or a numerical code before processing. The presence of a string in a column may cause a programing environment to interpret all values of said column as strings. To avoid this in the Pandas package of Python, for example, specify 'N' as the null value during CSV import: `df = pandas.read_csv('./national2019.csv', na_values='N')`. **Be sure to convert null values back to 'N' before submitting to the sdnist evaluator.** Again in Pandas, `df.to_csv('./synthetic_national2019.csv', na_rep='N')`.



#SBO Data Excerpts 
The original NIST ACS Data Excerpts released in 2023 has only 24 features and 40K records, and is designed to support the fine grained analysis of the behavior of data deidentification algorithms.  In 2025 we have added a new data set, the NIST SBO Data Excerpts, to provide a platform for stress-testing successful methods on much larger schema (130 features) features and data sets (161K records).  This data is drawn from the US Census Survey of Business Owners and includes a mix of demographic, temporal and financial features.  

In particular, the NIST SBO Excerpts will support stress-testing of privacy metrics developed during the second phase of the CRC Red-teaming project. Privacy metrics that require record similarity metrics and provide easily interpretable results on small schema, often don't scale well to significantly larger schema. 

## Data partitions and Area Definitions 
We provide two data sets of similar size, a target data and a withheld data.  Deidentified data samples from the target data will be provided for the red team participants, with the withheld data acting as an external baseline.  A broad range of geographies is represented in the excerpts:  

Target Dataset States and Row Counts:
- TX	54318
- IL	45195
- MA	27468
- AL	15306
- OK	10804
- AK, WY	7988

Withheld Dataset States and Row Counts:
- OH	34580
- CO	24778
- AZ	22042
- IN	16590
- CT	14389
- MS	10628
- RI, VT	8702
- NM	8658
- NH	6715

## Feature Notes: 
The Excerpts contains 130 features.  Note that many of these features have only 3 possible values ('Yes','No', and "Missing"); this prevents the data space from being infeasibly large.  These features include the following: 

- FIPST - State/Territory
- SECTOR - Business Sector
- N07_EMPLOYER (Employer status)
- TABWGT - Tabulation Weight
- Measures of Size (noise-infused for disclosure avoidance)
	- EMPLOYMENT_NOISY (Establishment employment)
	- PAYROLL_NOISY (Establishment payroll)
	- RECEIPTS_NOISY (Establishment Receipts)
- Individual Owner Information (for the primary owner):
	- PCT1 (Percentage Ownership)
- Characteristics of business owners (for the first owner):
	- ACQYR1 (When the owner acquired the business)
	- AGE1 (Owner age)
	- EDUC1 (Owner educational background)
	- 15 Additional Features listed in included data dictionary 
- Characteristics of businesses
	- Conducted transactions in language features (Example: JAPANESE)
	- Source of Startup Capital features (Example: SCSAVINGS)
	- Source of Expansion Capital features (Example: ECASSETS)
	- 101 Features in this category listed in the included data dictionary  
	
**Null values:** Null values in the SBO data csv files appear as adjacent commas for example, the third value here is null: "0,1,,1".
	
	
## Credits 

- [Christine Task](mailto:christine.task@knexusresearch.com) - Project technical lead - christine.task@knexusresearch.com
- [Karan Bhagat](https://github.com/kbtriangulum) - Contributor
- [Aniruddha Sen](https://www.linkedin.com/in/senaniruddha/) - Contributor
- [Damon Streat](https://www.linkedin.com/in/damon-streat-244106190) - Contributor
- [Ashley Simpson](https://www.linkedin.com/in/ashleysimpson33) - Contributor
- [Gary Howarth](https://www.nist.gov/people/gary-howarth) - Project PI - gary.howarth@nist.gov



