import os
import yaml
import logging
import json
import time
import uuid
import threading
from threading import Lock
from datetime import datetime
from kafka import KafkaConsumer
from .driver_client import DriverClient, DriverClientError

logger = logging.getLogger(__name__)
logging.getLogger('kafka').setLevel(logging.WARNING)

class ExecLifecycleRequest:

    def __init__(self, 
                    resource_state, 
                    lifecycle_name, 
                    driver_type, 
                    driver_endpoint,
                    wait_async, 
                    request_properties=None, 
                    kafka_endpoint=None, 
                    topic='lm_vnfc_lifecycle_execution_events', 
                    async_timeout=900, 
                    quiet=False,
                    tx_id=None, 
                    process_id=None, 
                    task_id=None):
        if resource_state is None:
            raise ValueError('resource_state must be provided')
        self.resource_state = resource_state
        if lifecycle_name is None:
            raise ValueError('lifecycle_name must be provided')
        self.lifecycle_name = lifecycle_name
        if driver_type is None:
            raise ValueError('driver_type must be provided')
        self.driver_type = driver_type
        if driver_endpoint is None:
            raise ValueError('driver_endpoint must be provided')
        self.driver_endpoint = driver_endpoint
        self.wait_async = wait_async
        if self.wait_async and kafka_endpoint is None:
            raise ValueError('kafka_endpoint must be provided when wait_async is True')
        self.kafka_endpoint = kafka_endpoint
        if self.wait_async and topic is None:
            raise ValueError('topic must be provided when wait_async is True')
        self.topic = topic
        if self.wait_async and async_timeout is None:
            raise ValueError('async_timeout must be provided when wait_async is True')
        self.async_timeout = async_timeout
        self.request_properties = request_properties if request_properties is not None else {}
        self.quiet = quiet
        self.tx_id = tx_id or 'testdrive-tx-{0}'.format(str(uuid.uuid4()))
        self.process_id = process_id or 'testdrive-process-{0}'.format(str(uuid.uuid4()))
        self.task_id = task_id or 'testdrive-task-{0}'.format(str(uuid.uuid4()))

    def run(self):
        if self.wait_async is True:
            consumer_thread = self._start_consumer_thread()
        accept_response = self._make_request()
        if self.wait_async is True:
            self._wait_for_async_response(accept_response, consumer_thread)

    def _make_request(self):
        client = DriverClient(self.driver_endpoint)
        args = self._get_request_args()
        self._log_request(args)
        try:
            response = client.execute_lifecycle(**args)
        except DriverClientError as e:
            self._log_failed_request(e)
            raise
        self._log_sync_response(response)
        return response

    def _get_request_args(self):
        headers = {
            'x-tracectx-TransactionId': self.tx_id,
            'x-tracectx-ProcessId': self.process_id,
            'x-tracectx-TaskId': self.task_id,
        }
        return {
            'lifecycle_name': self.lifecycle_name,
            'driver_files': self.resource_state.base64_driver_files(self.driver_type),
            'system_properties': self.resource_state.system_properties,
            'resource_properties': self.resource_state.resource_properties,
            'request_properties': self.request_properties,
            'associated_topology': self.resource_state.associated_topology,
            'deployment_location': self.resource_state.deployment_location,
            'headers': headers
        }

    def _start_consumer_thread(self):
        thread = KafkaPollThread(self.kafka_endpoint, self.topic)
        thread.setDaemon(True)
        thread.start()
        return thread

    def _wait_for_async_response(self, accept_response, consumer_thread):
        request_id = accept_response.get('requestId')
        logger.info(f'Waiting {self.async_timeout} second(s) for async response to request {request_id}')
        try:
            async_response, wait_duration = self._wait_for_response_on_kafka(request_id, consumer_thread)  
        except Exception as e:
            self._log_wait_async_failure(e)
            raise
        self._log_async_response(async_response, wait_duration)
        if async_response.get('status') == 'FAILED':
            raise RequestFailedError('Request failed: ' + str(async_response))

    def _wait_for_response_on_kafka(self, request_id, consumer_thread):
        async_response = None
        wait_duration = None
        timed_out = False
        start_time = datetime.now()
        while async_response is None and timed_out is False:
            async_response = consumer_thread.get_response(request_id)
            if async_response is None:
                now = datetime.now()
                wait_duration = (now - start_time).total_seconds()
                if wait_duration > self.async_timeout:
                    timed_out = True
                else:
                    time.sleep(0.5)
        if timed_out:
            raise AsyncTimeoutError(f'Did not see a response for request {request_id} after waiting {wait_duration} second(s)')
        consumer_thread.stop = True
        return async_response, wait_duration

    def _log_request(self, args):
        if not self.quiet:
            msg = '--- Request: execute_lifecycle ---'
            msg += '\n'
            msg += yaml.safe_dump(args)
            logger.info(msg)

    def _log_failed_request(self, error):
        if not self.quiet:
            msg = '--- Response: execute_lifecycle ---'
            msg += '\n'
            msg += f'Request failed: {str(error)}'
            logger.info(msg)

    def _log_sync_response(self, response):
        if not self.quiet:
            msg = '--- Response: execute_lifecycle ---'
            msg += '\n'
            msg += yaml.safe_dump(response)
            logger.info(msg)
        
    def _log_wait_async_failure(self, error):
        if not self.quiet:
            msg = '--- Async Response: execute_lifecycle ---'
            msg += '\n'
            msg += f'Failure waiting for async response: {str(error)}'
            logger.info(msg)

    def _log_async_response(self, response, wait_duration):
        if not self.quiet:
            msg = f'--- Async Response: execute_lifecycle (after {wait_duration} seconds) ---'
            msg += '\n'
            msg += yaml.safe_dump(response)
            logger.info(msg)

class AsyncTimeoutError(Exception):
    pass

class RequestFailedError(Exception):
    pass

lock = Lock()

class KafkaPollThread(threading.Thread):

    def __init__(self, bootstrap_servers, topic):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.stop = False
        self._responses = {}
        super().__init__()

    def _add_response(self, response):
        with lock:
            request_id = response.get('requestId')
            self._responses[request_id] = response

    def get_response(self, request_id):
        with lock:
            return self._responses.get(request_id)

    def run(self):
        logger.info(f'Starting watch on topic: {self.topic}')
        consumer = KafkaConsumer(self.topic, bootstrap_servers=self.bootstrap_servers, group_id=None)
        try:
            while self.stop is False:
                msg_pack = consumer.poll(timeout_ms=500)
                for tp, messages in msg_pack.items():
                    for message in messages:
                        response = json.loads(message.value.decode('utf-8'))
                        self._add_response(response)     
        except Exception as e:
            logger.exception(f'Watch thread for topic {self.topic} is closing due to error (see below):')
        finally:
            consumer.close()
