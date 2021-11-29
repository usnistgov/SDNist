from setuptools import setup

setup(
    name='sdnist',
    version='0.0.1',
    description='',
    long_description='',
    url='https://github.com/usnistgov/SDNist',
    author='gl',
    author_email='gl@sarus.tech',
    packages=['sdnist'],
    install_requires=["numpy", "pandas", "matplotlib", "pyarrow", "tqdm"],
    classifiers=['Development Status :: 1 - Planning'],
)