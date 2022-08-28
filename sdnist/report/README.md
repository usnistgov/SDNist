SDNIST Synthetic Data Quality Report (Beta Release)
====================================

This tool evaluates utility and privacy of a given synthetic dataset and generates a summary quality report with performance of a synthetic dataset enumerated and illustrated for each utility and privacy metric.

Setup SDNIST Report Tool
------------------------

1. Sdnist Report Tool is a part of the sdnist Python library that can be installed on a user’s MAC OS, Windows, or Linux machine.
  

2. The sdnist library requires Python version 3.7 or greater to be installed on the user's machine. Check whether an installation exists on the machine by executing the following command in your terminal on Mac/Linux or powershell on Windows:
   ```
    c:\\> python -v
   ```
    If Python is already installed, the above command should return the currently installed version. If Python is not found or the version is below 3.7, then you can download a higher version of Python from the [Python website](https://www.google.com/url?q=https://www.python.org/downloads/&sa=D&source=editors&ust=1661621593842784&usg=AOvVaw1p2lvwohvSroITRiZ4gnWi).


3.  Create a local directory/folder on the machine to set up the sdnist library. This guide assumes the local directory to be sdnist-project; an example of a complete file path is c:\\sdnist-project:
    ```
    c:\\sdnist-project>     
    ```

4.  Download the sdnist installable wheel (sdnist-1.4.0b1-py3-none-any.whl) from the [Github:SDNist beta release](https://www.google.com/url?q=https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/sdnist-1.4.0b1-py3-none-any.whl&sa=D&source=editors&ust=1661621593844523&usg=AOvVaw1R20BZUyIE3SiXQ3nkoS-Z).


5.  Move the downloaded sdnist-1.4.0b1-py3-none-any.whl file to the sdnist-project directory.


6.  Using the terminal on Mac/Linux or powershell on Windows, navigate to the sdnist-project directory.


7.  In the already-opened terminal or powershell window, execute the following command to create a new Python environment. The sdnist library will be installed in this newly created Python environment:

    ```
    c:\\sdnist-project> python -m venv venv
    ```


8. The new Python environment will be created in the sdnist-project directory, and the files of the environment should be in the venv directory. To check whether a new Python environment was created successfully, use the following command to list all directories in the sdnist-project directory, and make sure the venv directory exists.

    MAC OS/Linux:
    ```
    sdnist-project> ls
    ```
    Windows:
    ```
    c:\\sdnist-project> dir
    ```

9. Now activate the Python environment and install the sdnist library into it.

    MAC OS/Linux:
    ```
    sdnist-project> . venv/bin/activate
    (venv) sdnist-project>
    ```
    Windows:
    ```
    c:\\sdnist-project> . venv/Scripts/activate
    (venv) c:\\sdnist-project>
    ```
    To indicate that a new environment is active, the environment name (venv) is appended to the terminal or powershell prompt upon executing the above command.

    On Windows, a few users may encounter the following error if their machines are new (executing scripts is disabled by default on some Windows machines):
    ```
    C:\\sdnist-project\\venv\\Scripts\\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
    ```
    Run the following command to let Windows execute scripts:
    ```
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
    ```

10. Per step 5 above, the sdnist-1.4.0b1-py3-none-any.whl file should already be present in the sdnist-project directory. Check whether that is true by listing the files in the sdnist-project directory.

   MAC OS/Linux:
   ```
   (venv) sdnist-project> ls
   ```
   Windows:
   ```
   (venv) c:\\sdnist-project> dir
   ```
   The sdnist-1.4.0b1-py3-none-any.whl file should be in the list printed by the above command; otherwise, follow steps 4 and 5 again to download the .whl file.

11.  Install sdnist Python library:
   ```
   (venv) c:\\sdnist-project> pip install sdnist-1.4.0a1-py3-none-any.whl
   ```

12.  Installation is successful if executing the following command outputs a help menu for the sdnist.report package:
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report -h
   ```
   Output:
   ```
   usage: \_\_main\_\_.py \[-h\] \[--data-root DATA\_ROOT\] \[--download DOWNLOAD\] PATH\_SYNTHETIC\_DATASET TARGET\_DATASET\_NAME  
     
   positional arguments:  
   PATH\_SYNTHETIC\_DATASET  
                         Location of synthetic dataset (csv or parquet file)  
   TARGET\_DATASET\_NAME   Select name of the target dataset that was used to generated given synthetic dataset  
     
   optional arguments:  
   \-h, \--help            show this help message and exit  
   \--data-root DATA\_ROOT                      Path of the directory to be used as the root for the target datasets\--download DOWNLOAD   Download toy datasets if not present locallyChoices for Target Dataset Name::
   
    (dataname)         (filename)  
    MA                        ma2019
   
    TX                        tx2019
   
    National                  national2019
   ```


Generate Data Quality Report
----------------------------

1.  The sdnist.report package requires a path to the synthetic dataset file and the name of the target dataset from which the synthetic dataset file will be created. Following is the command line usage of the sdnist.report package:
      ```
      python -m sdnist.report PATH\_SYNTHETIC\_DATASET TARGET\_DATSET\_NAME 
      ```

      The above command is just an example usage signature of the package. Steps 3 to 5 show the actual commands to run the tool, where the parameter PATH\_SYNTHETIC\_DATASET is replaced with the path of the synthetic dataset file on the your machine, and the parameter TARGET\_DATASET\_NAME is replaced with one of the bundled dataset names (MA, TX, o NATIONAL).
      
      A synthetic dataset file can be anywhere on your machine. You only need the path of the file to pass it as an argument to the sdnist.report package. For illustration purposes, this guide assumes an example synthetic dataset file named syn\_tx.csv is generated from the bundled dataset file named TX that is present in the sdnist-project directory. You can also use the bundled toy synthetic datasets for generating some toy evaluation reports using the sdnist.report package by following step 5 and 6 in the next section, Setup Data for SDNIST Report Tool.

      Sdnist.report packages come bundled with three target datasets: MA, TX, and NATIONAL. If these datasets are not available locally, the package will download them automatically when you run any one of the commands in steps 3-5 for the first time. In case of any trouble while downloading the datasets, please refer to the next section, Setup Data for SDNIST Report Tool.


2.  If you have closed the terminal or the powershell window that was used for the tool setup, open a new one , and after navigating the to sdnist-project directory, run the activate script as explained in step 9 of the Setup SDNIST Report Tool section.


3.  Use the following command to generate a data quality report for the example synthetic dataset (syn\_tx.csv) that is generated using the bundled dataset TX:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn\_tx.csv TX
      ```
      At the completion of the process initiated by the above command, an html report will open in the default web browser on your machine. Likewise, .html report files will be available in the reports directory created automatically in the sdnist-project directory.


4.  Use the following command to generate a data quality report for the example synthetic dataset syn\_ma.csv that is generated using the bundled dataset MA:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn\_ma.csv MA
      ```


5.  Use the following command to generate a data quality report for the example synthetic dataset syn\_national.csv that is generated using the bundled dataset NATIONAL:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn\_national.csv NATIONAL
      ```


6.  The following are all the parameters offered by the sdnist.report package:

     * **PATH\_SYNTHETIC\_DATASET**: The absolute or relative path to the synthetic dataset .csv or parquet file. If the provided path is relative, it should be relative to the current working directory.  This guide assumes the current working directory is sdnist-project.
     * **TARGET\_DATASET\_NAME**: This should be the name of one of the datasets bundled with the sdnist.report package. It is the name of the dataset from which the input synthetic dataset is generated, and it can be one of the following:

       * MA
       * TX
       * NATIONAL

     * **--data-root**: The absolute or relative path to the directory containing the bundled dataset, or the directory where the bundled dataset should be downloaded to, if it is not available locally. The default directory is set to sdnist\_toy\_data.

Setup Data for SDNIST Report Tool
---------------------------------

1.  The sdnist.report package comes with built-in datasets. The package will automatically download the datasets from Github if they are not already available locally on your machine. Youshould see following message on your terminal or powershell window when the datasets are downloaded by the sdnist.report package:
      ```
      (venv) c:\\sdnist-project> python -m sdnist.report syn\_tx.csv TX
      
      Downloading all SDNist datasets from:  
      https://github.com/usnistgov/SDNist/releases/download/v1.4.0-a.1/SDNist-data-1.4.0-a.1.zip ...  
      ...5%, 47352 KB, 8265 KB/s, 5 seconds elapsed
      ```

      Follow the next subsection, Download Data Manually, if the sdnist.report package is unable to download the datasets. 


2. All the datasets required by the sdnist.report package are installed into the sdnist\_toy\_data directory, which should be now present inside the sdnist-project directory. sdnist\_toy\_data is also a data root directory. You can use some other directory as a data root by providing the –data-root argument to the sdnist.report package. If you provide a –data-root argument with a path, the sdnist.report package will look for datasets in the data root directory you have specified, and the package will download it if it is not present in the data root.

 
3. The sdnist.report package also needs a synthetic dataset that it can evaluate against its original counterpart. Since the sdnist.report package comes bundled with the datasets, the synthetic dataset should be generated using the bundled datasets.

   You can download a copy of the datasets from [Github Sdnist Toy Dataset](https://www.google.com/url?q=https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/SDNist-toy-data-1.4.0-b.1.zip&sa=D&source=editors&ust=1661621593866597&usg=AOvVaw1ZWEDpiwT2zvPKlum_3Mj2). This copy is similar to the one bundled with the sdnist.report package, but it contains more documentation and a description of the datasets.


4. You can download the toy synthetic datasets from [Github Sdnist Toy Synthetic Dataset](https://www.google.com/url?q=https://github.com/usnistgov/SDNist/releases/download/v1.4.0-b.1/toy_synthetic_data.zip&sa=D&source=editors&ust=1661621593867373&usg=AOvVaw0YMWTOS7MFYnJnoifZ44jL). Unzip the downloaded file, and move the unzipped toy\_synthetic\_dataset directory to the sdnist-project directory.

 
5. Each toy synthetic dataset file is generated using the [Sdnist Toy Dataset](https://www.google.com/url?q=https://github.com/usnistgov/SDNist/tree/main/nist%2520diverse%2520communities%2520data%2520excerpts&sa=D&source=editors&ust=1661621593868256&usg=AOvVaw3ozSD9cSsaIi3D2O4qi8MK). The syn\_ma.csv, syn\_tx.csv and syn\_national.csv synthetic dataset files are created from target datasets MA (ma2019.csv), TX (tx2019.csv) and NATIONAL(national2019.csv), respectively. You can use one of the toy synthetic dataset files for testing whether the sdnist.report package is installed correctly on your system.


6. Use following commands for generating reports if you are using a toy synthetic dataset file:
   
   For evaluating Massachusetts dataset
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report toy\_synthetic\_data/syn\_ma.csv MA
   ```

   For evaluating Texas dataset
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report toy\_synthetic\_data/syn\_tx.csv TX
   ```

   For evaluating National dataset
   ```
   (venv) c:\\sdnist-project> python -m sdnist.report toy\_synthetic\_data/syn\_national.csv NATIONAL
   ```

7.  A synthetic dataset can be a .csv or a parquet file, and the path of this file is required
by the sdnist.report package to generate a data quality report.

### Download Data Manually

1.  If the sdnist.report package is not able to download the datasets, you can download them from [Github:SDNist toy data alpha release](https://www.google.com/url?q=https://github.com/usnistgov/SDNist/tree/main/nist%2520diverse%2520communities%2520data%2520excerpts&sa=D&source=editors&ust=1661621593874153&usg=AOvVaw3u7Mo690-7kbIpVQJuDXa0)
2.  Move the downloaded SDNist-toy-data-1.4.0-b.1.zip file to the sdnist-project directory.
3.  Unzip the SDNist-toy-data-1.4.0-b.1.zip file and move the data directory inside it to the sdnist-project directory.
4.  Delete the SDNist-toy-data-1.4.0-b.1.zip file once the data directory is successfully moved out of the unzipped directory.
5.  Also delete the now-empty SDNist-toy-data-1.4.0-b.1 directory from where the zip file was extracted.
6.  And finally, to successfully install datasets manually, change the name of the data directory inside the sdnist-project directory to sdnist\_toy\_data.