import json
from os.path import dirname

with open(dirname(__file__) + '/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

__version__ = _pkg_info['version']