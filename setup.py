from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='sdnist',
    version='1.4.1',
    description='SDNist: datasets and evaluation tools for data synthesizers',
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
              "sdnist.report.plots"],
    # data_files=[('', ['sdnist/report2.jinja2'])],
    install_requires=[
        "jinja2>=3",
        "loguru>=0.6",
        "matplotlib>=3",
        "numpy>=1",
        "pandas>=1",
        "pyarrow>=7",
        "requests>=2",
        "scikit-learn>=1",
        "scipy>=1",
        "tqdm>=4"
    ],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3.8',
                 'License :: Other/Proprietary License',
                 'Intended Audience :: Science/Research'],
    include_package_data=True
)
