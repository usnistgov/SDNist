from setuptools import setup, find_packages

setup(
    name='sdnist',
    version='0.1.1',
    description='SDNist datasets and evaluation tools for data synthesizers',
    long_description='',
    url='https://github.com/usnistgov/SDNist',
    author='gl',
    author_email='gl@sarus.tech',
    packages=["sdnist", "sdnist.challenge", "sdnist.preprocess"],
    install_requires=["numpy", "pandas", "matplotlib", "pyarrow", "tqdm", 
        "loguru", "requests", "jinja2"],
    classifiers=['Development Status :: 4 - Beta testing'],
)
