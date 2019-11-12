import click
import logging
import os
import ignition.templates.factory as factory

logger = logging.getLogger(__name__)

@click.command(help='Create a new VIM and/or Lifecycle driver')
@click.argument('app_name')
@click.option('--driver-type', '-t', 'driver_types', multiple=True, help='REQUIRED: type of driver to generate. Values must be \'VIM\' or \'Lifecycle\' (case insensitive). You may specify the option twice to support both types')
@click.option('--version', default='0.0.1', help='Initial version of the driver (Defaults to: 0.0.1)')
@click.option('--port', default=None, help='Default port to allow access to the driver at runtime (Defaults to: random value)')
@click.option('--description', default=None, help='A brief description of the driver')
@click.option('--module-name', default=None, help='Name of the python module for the application (Defaults to: lower case copy of the \'app_name\' argument with spaces, underscores and dashes removed)')
@click.option('--docker-name', default=None, help='Intended name of the docker image for the driver (Defaults to: lower case copy of the \'app_name\' argument with spaces replaced for dashes)')
@click.option('--helm-name', default=None, help='Intended name of the helm chart for the driver (Defaults to: lower case copy of the \'app_name\' argument with spaces and replaced for dashes)')
@click.option('--helm-node-port', default=None, help='Default node port to specify in the helm chart, in order to allow NodePort access in Kubernetes (Defaults to: random value)')
def create(app_name, driver_types, version, port, description, module_name, docker_name, helm_name, helm_node_port):
    parsed_driver_types = []
    if len(driver_types) == 0:
        click.echo('ERROR: must specify at least one --driver-type (-t)')
        exit(1)
    for driver_type in driver_types:
        target_driver_type = driver_type.upper()
        if target_driver_type != factory.DRIVER_TYPE_VIM and target_driver_type != factory.DRIVER_TYPE_LIFECYCLE:
            click.echo('ERROR: invalid driver-type value supplied: {0}'.format(target_driver_type))
            exit(1)
        else:
            parsed_driver_types.append(target_driver_type)
    try:
        request = factory.DriverGenRequest(parsed_driver_types, app_name, version, port=port, module_name=module_name, description=description, docker_name=docker_name, \
            helm_name=helm_name, helm_node_port=helm_node_port)
    except ValueError as e:
        logger.exception(str(e))
        click.echo('ERROR: {0}'.format(str(e)))
        exit(1)
    location = os.getcwd()
    producer = factory.DriverProducer(request, location)
    try:
        click.echo('Creating driver named {0} at {1}'.format(app_name, location))
        producer.produce()
        click.echo('Complete!')
    except factory.ProducerError as e:
        logger.exception(str(e))
        click.echo('ERROR: {0}'.format(str(e)))
        exit(1)