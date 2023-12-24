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
    packages=find_packages(),
    # packages=["sdnist",
    #           "sdnist.challenge",
    #           "sdnist.metrics",
    #           "sdnist.preprocess",
    #           "sdnist.report",
    #           "sdnist.report.score",
    #           "sdnist.report.plots",
    #           "sdnist.report.score.utility",
    #           "sdnist.report.dataset",
    #           "sdnist.gui.elements"
    #           "sdnist.gui.elements.buttons",
    #           "sdnist.gui.elements.dropdowns",
    #           "sdnist.gui.fonts",
    #           "sdnist.gui.groups",
    #           "sdnist.gui.handlers",
    #           "sdnist.gui.pages",
    #           "sdnist.gui.pages.dashboard",
    #           "sdnist.gui.pages.home",
    #           "sdnist.gui.panels",
    #           "sdnist.gui.panels.simple",
    #           "sdnist.gui.panels.dftable",
    #           "sdnist.gui.panels.headers",
    #           "sdnist.gui.res",
    #           "sdnist.gui.windows",
    #           "sdnist.gui.windows.csv",
    #           "sdnist.gui.windows.archive"
    #           "sdnist.gui.windows.directory",
    #           ""]
    # data_files=[('', ['sdnist/report2.jinja2'])],
    install_requires=[
        "jinja2==3.1.2",
        "loguru==0.7.0",
        "matplotlib==3.7.1",
        "numpy==1.24.2",
        "pandas==2.0.0",
        "pyarrow==11.0.0",
        "requests==2.31.0",
        "scikit-learn==1.2.2",
        "scipy==1.10.1",
        "tqdm==4.65.0",
        "colorama==0.4.6",
        "pygame==2.5.0",
        "pygame-gui==0.6.9"
    ],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3.8',
                 'License :: Public Domain',
                 'Intended Audience :: Science/Research'],
    include_package_data=True
)
