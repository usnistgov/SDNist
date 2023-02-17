SDNist v1.4 beta: Deidentified Data Report Tool
====================================

This tool evaluates utility and privacy of a given deidentified dataset and generates a summary quality report with performance of a deide dataset enumerated and illustrated for each utility and privacy metric.

### Project Team  
**Karan Bhagat**, *Knexus Research* - Developer *sdnist.report* package  

**Christine Task**, *Knexus Research* - Project technical lead

**Gary Howarth**, *NIST* - Project PI [gary.howarth@nist.gov](mailto:gary.howarth@nist.gov)

### Reporting Issues:
Help us improve the package and this guide by reporting issues [here](https://github.com/usnistgov/SDNist/issues).

## Setting Up the SDNIST Report Tool
------------------------

### Brief Setup Instructions

SDNist v1.4 requires Python version 3.7 or greater. If you have installed a previous version of the SDNist library, we recommend uninstalling or installing v1.4 in a virtual environment. v1.4 can be installed via [Release 1.4.0b](https://github.com/usnistgov/SDNist/releases/tag/v1.4.1-b.1). The NIST Diverse Community Exceprt data will download on the fly.


### Detailed Setup Instructions

1. The SDNist Report Tool is a part of the sdnist Python library that can be installed on a user’s MAC OS, Windows, or Linux machine.


2. The sdnist library requires Python version 3.7 or greater to be installed on the user's machine. Check whether an installation exists on the machine by executing the following command in your terminal on Mac/Linux or powershell on Windows:
   ```
    c:\\> python -V
   ```
    If Python is already installed, the above command should return the currently installed version. If Python is not found or the version is below 3.7, then you can download Python from the [Python website](https://www.python.org/downloads/).


3.  Create a local directory/folder on the machine to set up the SDNist library. This guide assumes the local directory to be sdnist-project; an example of a complete file path is c:\\sdnist-project:
    ```
    c:\\sdnist-project>     
    ```

4.  Download the sdnist installable wheel (sdnist-1.4.1b-py3-none-any.whl) from the [Github:SDNist beta release](https://github.com/usnistgov/SDNist/releases/download/v1.4.1-b.1/sdnist-1.4.1b1-py3-none-any.whl).


5.  Move the downloaded sdnist-1.4.1b1-py3-none-any.whl file to the sdnist-project directory.


6.  Using the terminal on Mac/Linux or powershell on Windows, navigate to the sdnist-project directory.


7.  In the already-opened terminal or powershell window, execute the following command to create a new Python environment. The sdnist library will be installed in this newly created Python environment:

    ```
    c:\\sdnist-project> python -m venv venv
    ```


8. The new Python environment will be created in the sdnist-project directory, and the files of the environment should be in the venv directory. To check whether a new Python environment was created successfully, use the following command to list all directories in the sdnist-project directory, and make sure the venv directory exists.

    **MAC OS/Linux:**
    ```
    sdnist-project> ls
    ```
    **Windows:**
    ```
    c:\\sdnist-project> dir
    ```

9. Now activate the Python environment and install the sdnist library into it.

    **MAC OS/Linux:**
    ```
    sdnist-project> . venv/bin/activate
    ```
    The python virtual environment should now be activated. You should see environment name (**venv** in this case) appended to the terminal prompt as below:  
    ```
    (venv) sdnist-project>
    ```

    **Windows:**
    ```
    c:\\sdnist-project> . venv/Scripts/activate
    ```
    The python virtual environment should now be activated. You should see environment name (**venv** in this case) appended to the command/powershell prompt as below:  
    ```
    (venv) c:\\sdnist-project>
    ```

    On Windows, a few users may encounter the following error if their machines are new (executing scripts is disabled by default on some Windows machines):
    ```
    C:\\sdnist-project\\venv\\Scripts\\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
    ```
    Run the following command to let Windows execute scripts:
    ```
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
    ```

11. Per step 5 above, the sdnist-1.4.1b1-py3-none-any.whl file should already be present in the sdnist-project directory. Check whether that is true by listing the files in the sdnist-project directory.

  **MAC OS/Linux:**
   ```
   (venv) sdnist-project> ls
   ```
  **Windows:**
   ```
   (venv) c:\\sdnist-project> dir
   ```
   The sdnist-1.4.0b2-py3-none-any.whl file should be in the list printed by the above command; otherwise, follow steps 4 and 5 again to download the .whl file.

12. Install sdnist Python library:
   ```
   (venv) c:\\sdnist-project> pip install sdnist-1.4.1b1-py3-none-any.whl
   ```

13. Installation is successful if executing the following command outputs a help menu for the sdnist.report package:
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report -h
   ```
   Output:
   ```
   usage: __main__.py [-h] [--data-root DATA_ROOT] [--download DOWNLOAD] PATH_DEIDENTIFIED_DATASET TARGET_DATASET_NAME  

   positional arguments:  
   PATH_DEIDENTIFIED_DATASET  
                         Location of deidentified dataset (csv or parquet file)  
   TARGET_DATASET_NAME   Select name of the target dataset that was used to generated given deidentified dataset  

   optional arguments:  
   \-h, \--help            show this help message and exit  
   \--data-root DATA_ROOT                      Path of the directory to be used as the root for the target datasets\--download DOWNLOAD   Download toy datasets if not present locallyChoices for Target Dataset Name::

    (dataname)         (filename)  
    MA                        ma2019

    TX                        tx2019

    NATIONAL                  national2019
   ```

14. These instructions install sdnist into a virtual environment. The virtual environement must be activated (step 9) each time a new terminal window is used with sdnist.




## Generate Data Quality Report
----------------------------

1.  The sdnist.report package requires a path to the deidentified dataset file and the name of the target dataset from which the deidentified dataset file will be created. Following is the command line usage of the sdnist.report package:
      ```
      python -m sdnist.report PATH_DEINDETIFIED_DATASET TARGET_DATSET_NAME
      ```

      The above command is just an example usage signature of the package. Steps 3 through 5 show the actual commands to run the tool, where the parameter PATH_DEIDENTIFIED_DATASET is replaced with the path of the deidentified dataset file on the your machine, and the parameter TARGET_DATASET_NAME is replaced with one of the bundled dataset names (MA, TX, or NATIONAL).

      A deidentified dataset file can be anywhere on your machine. You only need the path of the file to pass it as an argument to the sdnist.report package. For illustration purposes, this guide assumes an example deidentified dataset file named syn_tx.csv is generated from the bundled dataset file named TX that is present in the sdnist-project directory. You can also use the bundled toy deidentified datasets for generating some toy evaluation reports using the sdnist.report package by following steps 5 and 6 in the next section, Setup Data for SDNIST Report Tool.

     The sdnist.report packages come bundled with three target datasets: MA, TX, and NATIONAL. If these datasets are not available locally, the package will download them automatically when you run any one of the commands in steps 3 through 5 for the first time. In case of any trouble while downloading the datasets, please refer to the next section, Setup Data for SDNIST Report Tool.


2.  If you have closed the terminal or the powershell window that was used for the tool setup, open a new one, and after navigating the to sdnist-project directory, run the activate script as explained in step 9 of the Setup SDNIST Report Tool section.


3.  Use the following command to generate a data quality report for the example deidentified dataset (syn_tx.csv) that is generated using the bundled dataset TX:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn_tx.csv TX
      ```
      At the completion of the process initiated by the above command, an .html report will open in the default web browser on your machine. Likewise, .html report files will be available in the reports directory created automatically in the sdnist-project directory.


4.  Use the following command to generate a data quality report for the example deidentified dataset (syn_ma.csv) that is generated using the bundled dataset MA:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn_ma.csv MA
      ```


5.  Use the following command to generate a data quality report for the example deidentified dataset (syn_national.csv) that is generated using the bundled dataset NATIONAL:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn_national.csv NATIONAL
      ```


6.  The following are all the parameters offered by the sdnist.report package:

     - **PATH_DEIDENTIFIED_DATASET **: The absolute or relative path to the deidentified dataset .csv or parquet file. If the provided path is relative, it should be relative to the current working directory. This guide assumes the current working directory is sdnist-project.
     - **TARGET_DATASET_NAME **: This should be the name of one of the datasets bundled with the sdnist.report package. It is the name of the dataset from which the input deidentified dataset is generated, and it can be one of the following:
       - MA
       - TX
       - NATIONAL

     - **--data-root **: The absolute or relative path to the directory containing the bundled dataset, or the directory where the bundled dataset should be downloaded to if it is not available locally. The default directory is set to sdnist_toy_data.


## Setup Data for SDNIST Report Tool
---------------------------------

1.  The sdnist.report package comes with built-in datasets. The package will automatically download the datasets from Github if they are not already available locally on your machine. You should see following message on your terminal or powershell window when the datasets are downloaded by the sdnist.report package:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn_tx.csv TX

      Downloading all SDNist datasets from:  
      https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/SDNist-toy-data-1.4.0-b.1.zip ...  
      ...5%, 47352 KB, 8265 KB/s, 5 seconds elapsed
      ```

      Follow the next subsection, Download Data Manually, if the sdnist.report package is unable to download the datasets.


2. All the datasets required by the sdnist.report package are installed into the sdnist _toy _data directory, which should be now present inside the sdnist-project directory. sdnist _toy _data is also a data root directory. You can use some other directory as a data root by providing the –data-root argument to the sdnist.report package. If you provide a –data-root argument with a path, the sdnist.report package will look for datasets in the data root directory you have specified, and the package will download it if it is not present in the data root.


3. The sdnist.report package also needs a deidentified dataset that it can evaluate against its original counterpart. Since the sdnist.report package comes bundled with the datasets, the deidentified dataset should be generated using the bundled datasets.

   You can download a copy of the datasets from [Github Sdnist Toy Dataset](https://github.com/usnistgov/SDNist/tree/main/nist%20diverse%20communities%20data%20excerpts). This copy is similar to the one bundled with the sdnist.report package, but it contains more documentation and a description of the datasets.


4. You can download the toy deidentified datasets from [Github Sdnist Toy Synthetic Dataset](https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/toy_synthetic_data.zip). Unzip the downloaded file, and move the unzipped toy_synthetic_dataset directory to the sdnist-project directory.


5. Each toy deidentified dataset file is generated using the [Sdnist Toy Dataset](https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/SDNist-toy-data-1.4.0-b.1.zip). The syn_ma.csv, syn_tx.csv, and syn_national.csv deidentified dataset files are created from target datasets MA (ma2019.csv), TX (tx2019.csv), and NATIONAL(national2019.csv), respectively. You can use one of the toy synthetic dataset files for testing whether the sdnist.report package is installed correctly on your system.


6. Use the following commands for generating reports if you are using a toy deidentified dataset file:

   For evaluating the Massachusetts dataset:
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report toy_synthetic_data/syn_ma.csv MA
   ```

   For evaluating the Texas dataset:
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report toy_synthetic_data/syn_tx.csv TX
   ```

   For evaluating the national dataset:
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report toy_synthetic_data/syn_national.csv NATIONAL
   ```

7.  A deidentified dataset can be a .csv or a parquet file, and the path of this file is required
by the sdnist.report package to generate a data quality report.

## Download Data Manually

1.  If the sdnist.report package is not able to download the datasets, you can download them from [Github:SDNist toy data beta release](https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/SDNist-toy-data-1.4.0-b.1.zip).
2.  Move the downloaded SDNist-toy-data-1.4.0-b.1.zip file to the sdnist-project directory.
3.  Unzip the SDNist-toy-data-1.4.0-b.1.zip file and move the data directory inside it to the sdnist-project directory.
4.  Delete the SDNist-toy-data-1.4.0-b.1.zip file once the data directory is successfully moved out of the unzipped directory.
5.  Also delete the now-empty SDNist-toy-data-1.4.0-b.1 directory from where the zip file was extracted.
6.  And finally, to successfully install datasets manually, change the name of the data directory inside the sdnist-project directory to sdnist_toy_data.
