from setuptools import find_packages, setup

setup(
    name='pygerrit',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'paramiko',
        'GitPython'
    ]
)
