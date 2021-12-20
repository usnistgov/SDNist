from setuptools import setup, find_packages

setup(
    name='sdnist',
    version='0.0.1',
    description='',
    long_description='',
    url='https://github.com/usnistgov/SDNist',
    author='gl',
    author_email='gl@sarus.tech',
    packages=find_packages(),
    install_requires=["numpy", "pandas", "matplotlib", "pyarrow", "tqdm", 
        "loguru", "requests", "jinja2"],
    classifiers=['Development Status :: 1 - Planning'],
)