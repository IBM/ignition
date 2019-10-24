import json
from setuptools import setup, find_namespace_packages

with open('ignition/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='ignition-framework',
    version=_pkg_info['version'],
    author='Accanto Systems',
    description='Stratoss Lifecycle Manager RM driver framework',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/accanto-systems/ignition",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ],
    packages=find_namespace_packages(include=['ignition*']),
    include_package_data=True,
    install_requires=[
        'connexion[swagger-ui]>=2.2.0,<3.0',
        'kafka-python>=1.4.6',
        'networkx>=2.3',
        'frozendict>=1.2',
        'Jinja2>=2.7',
        'click>=7.0'
    ],
    entry_points='''
        [console_scripts]
        ignition=ignition.cli.entry:init_cli
    '''
)
