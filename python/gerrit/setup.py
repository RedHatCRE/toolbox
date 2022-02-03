from setuptools import find_packages
from setuptools import setup

setup(
    name='pygerrit',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'docopt',
        'paramiko',
        'GitPython'
    ]
)
