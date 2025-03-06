from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
version = open("sdnist/version.py").readlines()[-1].split()[-1].strip("\"'")

setup(
    name='sdnist',
    version=version,
    description='SDNist: Deidentified Data Report Generator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/usnistgov/SDNist',
    author='National Institute of Standards and Technology',
    author_email='gary.howarth@nist.gov',
    packages=["sdnist",
              "sdnist.challenge",
              "sdnist.metrics",
              "sdnist.preprocess",
              "sdnist.report",
              "sdnist.report.score",
              "sdnist.report.plots",
              "sdnist.report.score.utility",
              "sdnist.report.dataset"],
    # data_files=[('', ['sdnist/report2.jinja2'])],
    install_requires=[
        "jinja2==3.1.6",
        "loguru==0.7.0",
        "matplotlib==3.7.1",
        "numpy==1.24.2",
        "pandas==2.0.0",
        "pyarrow==14.0.1",
        "requests==2.32.0",
        "scikit-learn==1.2.2",
        "scipy==1.10.1",
        "tqdm==4.66.3",
        "colorama==0.4.6"
    ],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3.8',
                 'License :: Public Domain',
                 'Intended Audience :: Science/Research'],
    include_package_data=True
)
