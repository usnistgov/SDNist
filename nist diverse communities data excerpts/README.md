# The NIST Diverse Community Excerpts

The Diverse Community Excepts data are designed to be a resource to investigate performance of data synthesizers and similar privacy-enhancing technologies when applied to data collected from three communities (Boston area, Dallas-Forth Worth area, and US national) radically different demographics. The data are drawn from real records released in the [American Community Survey](https://www.census.gov/programs-surveys/acs), a product of the US Census Bureau.

## Purpose and design

The Diverse Communities Excerpt Data was developed to address a recurring problem identified in the NIST Differential Privacy Synthetic Data Challenge, NIST Differential Privacy Temporal Map Challenge, and the HLG-MOS Synthetic Data Test Drive. Specifically, if the data are too complex it’s hard to tell for sure what’s going on with it. These data are designed to support deeper and more formal understanding of algorithm behavior on real human data.

The Diverse Community Excerpt Data were designed with input from USCB experts in adaptive sampling design (Consider– [Coffey 2020](https://doi.org/10.1093/jssam/smz026)), and leveraged previous work on geographical differences in CART modeled synthetic data to identify PUMA with challenging distributions (See Appendix B– [Abowd 2021](https://ui.adsabs.harvard.edu/link_gateway/2021arXiv211013239A/arxiv:2110.13239)).

Effectively, we needed a miniature, model-sized version of the problem that we were trying to understand.  Like a ship in a bottle– pieces small enough that they can be assembled by hand, so we can start to see how they fit together.


The requirements we sought to meet included:
- A feature set that is interesting with complexity representative of real communities, yet compact enough to allow for rigorous, penetrating analysis
- Geographic regions that include enough (but not overwhelming amount) individuals and sufficient complexity to investigate relationships between features
- Geographic regions whose typical feature values vary radically to explore performance on diverse data sets.

## Data set description

We are currently offering three geographic regions each contained within its own directory containing the data and a description of each PUMA within data we call postcards.

All of the data have identical schema of 22 features which are provided in a data dictionary with notes below.

### Community descriptions
See the 'postcards' and data dictionaries in each respective directory for more detailed information.
-  `national`: 27254 records drawn from 20 PUMAs from across the United States.
-  `massachusetts`: 7634 records drawn from five PUMAs of communities from the North Shore to the west of the greater Boston, Massachusetts area.
- `texas`:  9276 records drawn from six PUMAs of communities surrounding Dallas-Fort Worth, Texas area.


## Usage guidance:

### Area definitions
Each of the data sets are comprised of data from multiple PUMAs (Public Use Microdata Area). PUMAs are designated by the US Census Bureau and designed to be "non-overlapping, statistical geographic areas that partition each state or equivalent entity into geographic areas containing no fewer than 100,000 people each." [See the Census page for more information](https://www.census.gov/programs-surveys/geography/guidance/geo-areas/pumas.html).

### Data partitions
The data have been broken into three separate data sets, `massachusetts`, `texas` and `national`. Algorithms can be run on each data set separately, or all three together (they use the same schema).  The MA and TX data have been chosen to be more homogenous and regionally focused (north shore Boston and southwest Forth Worth), while the PUMA included in the National data have been chosen to represent an array of complex and diverse communities around the country.
Postcard descriptions: These are included in each data set folder and provide a snapshot introduction to each of the geographies included in the data set. When your algorithm performs well or poorly on a specific PUMA you might find it interesting to check in on the defining characteristics of that PUMA. For instance, the veteran disability variable (DVET) may have a more interesting distribution near military communities. These postcards make a good starting point for learning more about the real communities your algorithms are running on.


### Data dictionary and feature notes
There is a data dictionary in JSON format included with the data.

**Null values:** Different systems encode and handle null values differently; to avoid difficulties with this we have used the literal character 'N' to represent null values throughout this data. For synthesizing numerical features (PINCP, POVIP) you will likely want to convert 'N' to null or a numerical code before processing; be sure to convert it back to 'N' before submitting to the sdnist evaluator.

**Feature notes:**
- Geography Feature: PUMA (see note above)
- Demographic Features: AGEP (age), SEX (sex), HISP (hispanic origin), RAC1P (race)
- Household Features: MSP (marital status), NOC (number of children), NPF (family size), HOUSING_TYPE (single housing unit or group quarters such as dorms, barracks or nursing homes), OWN_RENT (own or rent housing)
- Regional Features: DENSITY (population density of PUMA, useful for distinguishing urban, suburban and rural PUMA)
- Financial Features: PINCP (personal income, including wages and investment), PINCP_DECILE (person’s income discretized as a 10% percentile bin relative to the income distribution in their PUMA) , POVPIP (household income as a percentage of the poverty threshold for that household (dependent on family size and other factors). Households with income more than 5x the property line are given the value 501).
- Industry and Education Features: EDU (highest educational attainment— it’s useful to consider this in combination with AGEP), INDP_CAT (general category of work, for example agriculture or retail), INDP (specific category of work— this is an example of a categorical feature with very many possible values)
- Disability Features: DREM (cognitive difficulty, binary feature), DEYE (vision difficulty, binary feature), DEAR (hearing difficulty, binary feature), DPHY (walking/movement difficulty, binary feature), DVET (disability due to military service— this is a rating value rather than a binary feature).
- Weights: Person’s weight and housing weight can be used to generate a full sample. [to be completed]
- Other notes: INDP_CAT & INDP (INDP_CAT is a partitioning of the codes in INDP), PUMA & DENSITY (DENSITY is the population density of a given PUMA), NPF & NOC (NPF must be greater than NOC), HOUSING_TYPE & OWN_RENT (OWN_RENT is null for group quarters), PINCP & PINCP_DECILE (PINCP_DECILE is a percentile aggregation of PINCP by PUMA) AGE & many features (Children will have null values for many adult features, such as financials, and a maximal possible value for educational attainment dependent on age).

### Suggested feature combinations
**If you want…:**
- A few small binary features, consider using: OWN_RENT, DPHY, DEYE, DEAR, SEX
- A numerical feature, considering using PINCP, POVPIP or AGEP.
- An ordinal feature, consider EDU, PINCP_DECILE, NOC or NPF
- A large cardinality categorical feature, consider using INDP
- A smaller cardinality categorical feature, consider using INDP_CAT, HISP, MSP
- Diverse distributions, look at RAC1P, DVET, SEX, MRST, and RENT_OWN
