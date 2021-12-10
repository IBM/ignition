import json
from setuptools import setup, find_namespace_packages

with open('{(app.module_name)}/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='{(app.module_name)}',
    version=_pkg_info['version'],
    description='{(app.description)}',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(include=['{(app.module_name)}*']),
    include_package_data=True,
    install_requires=[
        'ignition-framework=={(ignition.version)}',
        'gunicorn>=19.9.0,<20.0'
    ],
    entry_points='''
        [console_scripts]
        {(app.module_name)}-dev={(app.module_name)}.__main__:main
    '''
)
