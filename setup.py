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
              "sdnist.report.score.utility.interfaces",
              "sdnist.report.score.utility.interfaces.kmarginal",
              "sdnist.report.dataset"],
    # data_files=[('', ['sdnist/report2.jinja2'])],
    install_requires=[
        "jinja2==3.1.5",
        "loguru==0.7.3",
        "matplotlib==3.9.4",
        "numpy==1.26.4",
        "pandas==2.2.0",
        "pyarrow==17.0.0",
        "requests==2.32.4",
        "scikit-learn==1.6.1",
        "scipy==1.13.1",
        "tqdm==4.67.1",
        "colorama==0.4.6"
    ],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3.8',
                 'License :: Public Domain',
                 'Intended Audience :: Science/Research'],
    include_package_data=True
)
