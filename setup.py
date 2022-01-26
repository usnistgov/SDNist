from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='sdnist',
    version='1.2.7',
    description='SDNist: datasets and evaluation tools for data synthesizers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/usnistgov/SDNist',
    author='National Institute of Standards and Technology',
    author_email='gary.howawrth@nist.gov',
    packages=["sdnist", "sdnist.challenge", "sdnist.preprocess"],
    # data_files=[('', ['sdnist/report2.jinja2'])],
    install_requires=["requests>=2", "numpy>=1", "pandas>=1", "matplotlib>=3", "pyarrow>=6", "tqdm>=4",
        "loguru>=0.5", "jinja2>=2"],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3.8',
                 'License :: Other/Proprietary License',
                 'Intended Audience :: Science/Research'],
    include_package_data = True
)
