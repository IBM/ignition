import click
import ignition.cli.cmd_create as cmd_create
import logging.config
import os
import yaml
from pkg_resources import resource_string

@click.group()
@click.version_option()
def cli():
    """Ignition tools"""

def init_cli():
    setup_logging()
    cli.add_command(cmd_create.create)
    cli()

def setup_logging(default_level=logging.INFO):
  logging_config = os.path.join(os.getcwd(), 'ignition-logging.yaml')
  if os.path.exists(logging_config):
    with open(logging_config, 'r') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
  else:
    logging.basicConfig(level=default_level)	