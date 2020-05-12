import json
from setuptools import setup, find_namespace_packages

with open('tdriver/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='tdriver',
    version=_pkg_info['version'],
    description='unit test driver',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(include=['tdriver*']),
    include_package_data=True,
    install_requires=[
        'ignition-framework==IGNITION_VERSION',
        'uwsgi>=2.0.18,<3.0',
        'gunicorn>=19.9.0,<20.0'
    ],
    entry_points='''
        [console_scripts]
        tdriver-dev=tdriver.__main__:main
    ''',
    scripts=['tdriver/bin/tdriver-uwsgi', 'tdriver/bin/tdriver-gunicorn', 'tdriver/bin/tdriver']
)