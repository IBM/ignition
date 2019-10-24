import click
import ignition.cli.cmd_create as cmd_create

@click.group()
@click.version_option()
def cli():
    """Ignition tools"""

def init_cli():
    cli.add_command(cmd_create.create)
    cli()
