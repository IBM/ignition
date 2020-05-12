import click
import logging
import os
import ignition.templates.factory as factory
from ignition.testdrive.exec_lifecycle import ExecLifecycleRequest
from ignition.testdrive.find_reference import FindReferenceRequest
from ignition.testdrive.resource_state import ResourceState

logger = logging.getLogger(__name__)

@click.group(name='testdrive', help='Commands for executing test requests against a driver')
def testdrive():
    pass

@testdrive.command(help='Make a lifecycle execution request against a driver (optionally wait for async response)')
@click.option('--lifecycle', '-l', required=True, type=str, help='Name of lifecycle transition/operation to execute')
@click.option('--resource', '-r', required=True, type=click.Path(exists=True), help='Path to a file describing the resource artifacts')
@click.option('--url', '-u', required=True, type=str, help='Endpoint of the driver e.g. http://host:port (do not add any API paths)')
@click.option('--driver-type', '-d', required=True, type=str, help='Type of driver, used to determine the directory of driver_files to use when using driver_files_dir in your resource artifacts e.g. openstack, ansible.')
@click.option('--wait', '-w',  is_flag=True, default=False, help='Wait for the async response of the request to appear on Kafka [Default: False]')
@click.option('--max-wait', '-m', type=int, default=900, help='Time, in seconds, to wait for an async response (required if --wait-async/-w is enabled) [Default: 900]')
@click.option('--kafka', '-k', type=str, default='kafka:9092', help='Endpoint for connection to Kafka broker (required if --wait-async/-w is enabled) [Default: kafka:9092]')
@click.option('--topic', '-t', type=str, default='lm_vnfc_lifecycle_execution_events', help='Kafka topic to consume async responses (required if --wait-async/-w is enabled) [Default: lm_vnfc_lifecycle_execution_events]')
@click.option('--set', 'set_request_properties', nargs=2, type=click.Tuple([str,str]), multiple=True, help='Request properties passed to the driver')
def execlifecycle(lifecycle, resource, url, driver_type, wait, max_wait, kafka, topic, set_request_properties):
    try:
        request_properties = {}
        if set_request_properties is not None:
            for tpl in set_request_properties:
                request_properties[tpl[0]] = {'type': 'string', 'value': tpl[1]}
        resource_state = ResourceState.from_file(resource)
        exec_request = ExecLifecycleRequest(resource_state, lifecycle, driver_type, url, wait, kafka_endpoint=kafka, topic=topic, async_timeout=max_wait, request_properties=request_properties)
        exec_request.run()
    except Exception as e:
        logger.exception(str(e))
        click.echo('ERROR: {0}'.format(str(e)))
        exit(1)

@testdrive.command(help='Make a find reference request against a driver')
@click.option('--name', '-n', required=True, type=str, help='instanceName to filter on')
@click.option('--resource', '-r', required=True, type=click.Path(exists=True), help='Path to a file describing the resource artifacts')
@click.option('--url', '-u', required=True, type=str, help='Endpoint of the driver e.g. http://host:port (do not add any API paths)')
@click.option('--driver-type', '-d', required=True, type=str, help='Type of driver, used to determine the directory of driver_files to use when using driver_files_dir in your resource artifacts e.g. openstack, ansible.')
def findreference(name, resource, url, driver_type):
    try:
        resource_state = ResourceState.from_file(resource)
        request = FindReferenceRequest(resource_state, name, driver_type, url)
        request.run()
    except Exception as e:
        logger.exception(str(e))
        click.echo('ERROR: {0}'.format(str(e)))
        exit(1)