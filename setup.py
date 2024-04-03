import json
from setuptools import setup, find_namespace_packages

with open('ignition/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='ignition-framework',
    version=_pkg_info['version'],
    author='IBM',
    description='IBM CP4NA RM driver framework',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IBM/ignition",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ],
    packages=find_namespace_packages(include=['ignition*']),
    include_package_data=True,
    install_requires=[
        'connexion==3.0.5',
        'kafka-python==2.0.2',
        'networkx==2.5.1',
        'frozendict==2.0.2',
        'Jinja2==3.0.1',
        'requests==2.31.0',
        'click==8.0.1',
        'connexion[flask]==3.0.5'
        
    ],
    entry_points='''
        [console_scripts]
        ignition=ignition.cli.entry:init_cli
    '''
)
