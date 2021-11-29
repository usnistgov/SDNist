# DPSyn 

### Overview
This is the original code we submitted for the Sprint 2.
The code can be run if put to the benchmark folder of the [runtime repo](https://github.com/drivendataorg/deid2-runtime/tree/sprint-2).
The competition description is at [drivendata](https://www.drivendata.org/competitions/75/deid2-sprint-2-prescreened/page/285/), 
and the data can be downloaded [here](https://www.drivendata.org/competitions/75/deid2-sprint-2-prescreened/data/).
We will refactor the code for public use and publish the polished version. 

### Description of the code
* ``main.py`` is the entry of our algorithm.

*  ``config/data.yaml`` is the configuration file with public dataset path, target dataset paths 
and binning/grouping attributes strategies.

* ``dataloader/public.csv`` is the public data used in the open/pre-screened arena (IL and OH data).

* ``dataloader/Dataloader.py`` is the dataloader used to load and preprocess both public and private (target) dataset.
It also contains the methods of generating 1-way/2-way marginals.

* ``dataloader/RecordPostprocessor.py`` is for post-processing synthetic dataset to have the same attributes
as input dataset.

* ``method/sample_parallel.py`` is one of the key components in our algorithm.
Details can be found in our pdf document.

* ``method/dpsyn.py`` is another key component in our algorithm. 
It generates synthetic data (for sampling) based on the noisy 1-way or 2-way marginals, 
when we have sufficient privacy budget.

* ``method/sythesizer.py`` is the base class. It contains functions of generating privacy-preserved
marginals.

* ``lib_dysyn/`` contains the classes of enforcing consistency on marginals and synthesize data.

* ``utils/advanced_composition.py`` contains functions to compute noise variance 
given privacy budget, sensitivity and number of queries.
  
* ``proof.pdf`` contains the detailed description of the code and the formal proof.