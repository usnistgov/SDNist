from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='sdnist',
    version='1.2.0',
    description='SDNist: datasets and evaluation tools for data synthesizers',
    long_description='',
    url='https://github.com/usnistgov/SDNist',
    DOI='10.18434/mds2-2515',
    author='National Institute of Standards and Technology',
    author_email='gary.howawrth@nist.gov',
    packages=["sdnist", "sdnist.challenge", "sdnist.preprocess"],
    # data_files=[('', ['sdnist/report2.jinja2'])],
    install_requires=["numpy", "pandas", "matplotlib", "pyarrow", "tqdm",
        "loguru", "requests", "jinja2"],
    classifiers=['Development Status :: 5 - Stable Release',
                 'Programming Language :: Python :: 3.8',
                 'Topic :: Synthetic Data :: Evaluation',],
    include_package_data = True
)
