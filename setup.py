from setuptools import setup

setup(
    name='sdnist',
    version='0.1.1',
    description='SDNist datasets and evaluation tools for data synthesizers',
    long_description='',
    url='https://github.com/usnistgov/SDNist',
    author='gl',
    author_email='gl@sarus.tech',
    packages=['sdnist'],
    install_requires=["numpy", "pandas", "matplotlib", "pyarrow", "tqdm", "loggeru"],
    classifiers=['Development Status :: 4 - Beta testing'],
)
