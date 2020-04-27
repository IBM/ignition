import unittest
from unittest.mock import patch, MagicMock, ANY
from ignition.api.exceptions import BadRequest
from ignition.service.resourcedriver import (ResourceDriverApiService, ResourceDriverService, LifecycleExecutionMonitoringService, LifecycleMessagingService, 
                        DriverFilesManagerService, TemporaryResourceDriverError, RequestNotFoundError)
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution
from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.model.internal_resources import InternalResources
from ignition.service.messaging import Envelope, Message, TopicConfigProperties
import zipfile
import os
import tempfile
import shutil
import base64
from ignition.utils.propvaluemap import PropValueMap

class TestResourceDriverApiService(unittest.TestCase):
    
    def __props_with_types(self, orig_props):
        props = {}
        for k, v in orig_props.items():
            props[k] = {'type': 'string', 'value': v}
        return props

    def __propvaluemap(self, orig_props):
        props = {}
        for k, v in orig_props.items():
            props[k] = {'type': 'string', 'value': v}
        return PropValueMap(props)

    @patch('ignition.service.resourcedriver.logging_context')
    def test_init_without_service_throws_error(self, logging_context):
        with self.assertRaises(ValueError) as context:
            ResourceDriverApiService()
        self.assertEqual(str(context.exception), 'No service instance provided')

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute(self, logging_context):
        mock_service = MagicMock()
        mock_service.execute_lifecycle.return_value = LifecycleExecuteResponse('123')
        controller = ResourceDriverApiService(service=mock_service)
        response, code = controller.execute_lifecycle(**{ 
            'body': { 
                'lifecycleName': 'Start', 
                'systemProperties': self.__props_with_types({'resourceId': '1'}),
                'resourceProperties': self.__props_with_types({'a': '2'}),
                'requestProperties': self.__props_with_types({'reqA': '3'}),
                'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                'driverFiles': b'123', 
                'deploymentLocation': {'name': 'test'} 
            } 
        })
        mock_service.execute_lifecycle.assert_called_once_with('Start', b'123', {'resourceId': { 'type': 'string', 'value': '1'}}, {'a': { 'type': 'string', 'value': '2'}}, {'reqA': {'type': 'string', 'value': '3'}}, [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}], {'name': 'test'})
        self.assertEqual(response, {'requestId': '123', 'internalResources': []})
        self.assertEqual(code, 202)
        logging_context.set_from_headers.assert_called_once()

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_lifecycle_name(self, logging_context):
        mock_service = MagicMock()
        controller = ResourceDriverApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute_lifecycle(**{ 
                'body': { 
                    'systemProperties': self.__props_with_types({'resourceId': '1'}),
                    'resourceProperties': self.__props_with_types({'a': '2'}),
                    'requestProperties': self.__props_with_types({'reqA': '3'}),
                    'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                    'driverFiles': b'123', 
                    'deploymentLocation': {'name': 'test'} 
                } 
            })
        self.assertEqual(str(context.exception), '\'lifecycleName\' is a required field but was not found in the request data body')

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_driver_files(self, logging_context):
        mock_service = MagicMock()
        controller = ResourceDriverApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute_lifecycle(**{ 
                'body': { 
                    'lifecycleName': 'Start',
                    'systemProperties': self.__props_with_types({'resourceId': '1'}),
                    'resourceProperties': self.__props_with_types({'a': '2'}),
                    'requestProperties': self.__props_with_types({'reqA': '3'}),
                    'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                    'deploymentLocation': {'name': 'test'} 
                } 
            })
        self.assertEqual(str(context.exception), '\'driverFiles\' is a required field but was not found in the request data body')

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = ResourceDriverApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute_lifecycle(**{ 
                'body': { 
                    'lifecycleName': 'Start', 
                    'systemProperties': self.__props_with_types({'resourceId': '1'}),
                    'resourceProperties': self.__props_with_types({'a': '2'}),
                    'requestProperties': self.__props_with_types({'reqA': '3'}),
                    'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                    'driverFiles': b'123'
                } 
            })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_system_properties(self, logging_context):
        mock_service = MagicMock()
        controller = ResourceDriverApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute_lifecycle(**{ 
                'body': { 
                    'lifecycleName': 'Start', 
                    'resourceProperties': self.__props_with_types({'a': '2'}),
                    'requestProperties': self.__props_with_types({'reqA': '3'}),
                    'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                    'driverFiles': b'123', 
                    'deploymentLocation': {'name': 'test'} 
                } 
            })
        self.assertEqual(str(context.exception), '\'systemProperties\' is a required field but was not found in the request data body')

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_resource_properties(self, logging_context):
        mock_service = MagicMock()
        mock_service.execute_lifecycle.return_value = LifecycleExecuteResponse('123')
        controller = ResourceDriverApiService(service=mock_service)
        response, code = controller.execute_lifecycle(**{ 
            'body': { 
                'lifecycleName': 'Start', 
                'systemProperties': self.__props_with_types({'resourceId': '1'}),
                'requestProperties': self.__props_with_types({'reqA': '3'}),
                'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                'driverFiles': b'123', 
                'deploymentLocation': {'name': 'test'} 
            } 
        })
        mock_service.execute_lifecycle.assert_called_once_with('Start', b'123', {'resourceId': { 'type': 'string', 'value': '1'}}, {}, {'reqA': {'type': 'string', 'value': '3'}}, [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}], {'name': 'test'})
        self.assertEqual(response, {'requestId': '123', 'internalResources': []})
        self.assertEqual(code, 202)
    
    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_request_properties(self, logging_context):
        mock_service = MagicMock()
        mock_service.execute_lifecycle.return_value = LifecycleExecuteResponse('123')
        controller = ResourceDriverApiService(service=mock_service)
        response, code = controller.execute_lifecycle(**{ 
            'body': { 
                'lifecycleName': 'Start', 
                'systemProperties': self.__props_with_types({'resourceId': '1'}),
                'resourceProperties': self.__props_with_types({'a': '2'}),
                'internalResources': [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}],
                'driverFiles': b'123', 
                'deploymentLocation': {'name': 'test'} 
            } 
        })
        mock_service.execute_lifecycle.assert_called_once_with('Start', b'123', {'resourceId': { 'type': 'string', 'value': '1'}}, {'a': { 'type': 'string', 'value': '2'}}, {}, [{'id': 'abc', 'name': 'Test', 'type': 'Testing'}], {'name': 'test'})
        self.assertEqual(response, {'requestId': '123', 'internalResources': []})
        self.assertEqual(code, 202)

    @patch('ignition.service.resourcedriver.logging_context')
    def test_execute_missing_internal_resources(self, logging_context):
        mock_service = MagicMock()
        mock_service.execute_lifecycle.return_value = LifecycleExecuteResponse('123')
        controller = ResourceDriverApiService(service=mock_service)
        response, code = controller.execute_lifecycle(**{ 
            'body': { 
                'lifecycleName': 'Start', 
                'systemProperties': self.__props_with_types({'resourceId': '1'}),
                'resourceProperties': self.__props_with_types({'a': '2'}),
                'requestProperties': self.__props_with_types({'reqA': '3'}),
                'driverFiles': b'123', 
                'deploymentLocation': {'name': 'test'} 
            } 
        })
        mock_service.execute_lifecycle.assert_called_once_with('Start', b'123', {'resourceId': { 'type': 'string', 'value': '1'}}, {'a': { 'type': 'string', 'value': '2'}}, {'reqA': {'type': 'string', 'value': '3'}}, [], {'name': 'test'})
        self.assertEqual(response, {'requestId': '123', 'internalResources': []})
        self.assertEqual(code, 202)

class TestResourceDriverService(unittest.TestCase):

    def __propvaluemap(self, orig_props):
        props = {}
        for k, v in orig_props.items():
            props[k] = {'type': 'string', 'value': v}
        return PropValueMap(props)

    def assert_requests_equal(self, actual_request, expected_request):
        expected_request_id = expected_request.get('request_id', None)
        expected_lifecycle_name = expected_request.get('lifecycle_name', None)
        expected_driver_files = expected_request.get('driver_files', None)
        expected_properties = expected_request.get('properties', None)
        expected_system_properties = expected_request.get('system_properties', None)
        expected_deployment_location = expected_request.get('deployment_location', None)
        if expected_request_id is not None:
            actual_request_id = actual_request.get('request_id', None)
            self.assertIsNotNone(actual_request_id)
            self.assertEqual(expected_request_id, actual_request_id)

        if expected_lifecycle_name is not None:
            actual_lifecycle_name = actual_request.get('lifecycle_name', None)
            self.assertIsNotNone(actual_lifecycle_name)
            self.assertEqual(expected_lifecycle_name, actual_lifecycle_name)

        if expected_driver_files is not None:
            actual_driver_files = actual_request.get('driver_files', None)
            self.assertIsNotNone(actual_driver_files)
            self.assertEqual(expected_driver_files, actual_driver_files)

        if expected_deployment_location is not None:
            actual_deployment_location = actual_request.get('deployment_location', None)
            self.assertIsNotNone(actual_deployment_location)
            self.assertDictEqual(expected_deployment_location, actual_deployment_location)

        if expected_properties is not None:
            actual_properties = actual_request.get('properties', None)
            self.assertIsNotNone(actual_properties)
            self.assertDictEqual(expected_properties, actual_properties)

        if expected_system_properties is not None:
            actual_system_properties = actual_request.get('system_properties', None)
            self.assertIsNotNone(actual_system_properties)
            self.assertDictEqual(expected_system_properties, actual_system_properties)

    def test_init_without_driver_throws_error(self):
        mock_resource_driver_config = MagicMock()
        mock_driver_files_manager = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverService(resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager)
        self.assertEqual(str(context.exception), 'handler argument not provided')

    def test_init_without_configuration_throws_error(self):
        mock_driver = MagicMock()
        mock_driver_files_manager = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverService(handler=mock_driver, driver_files_manager=mock_driver_files_manager)
        self.assertEqual(str(context.exception), 'resource_driver_config argument not provided')

    def test_init_without_driver_files_manager_throws_error(self):
        mock_driver = MagicMock()
        mock_resource_driver_config = MagicMock()
        with self.assertRaises(ValueError) as context:
            ResourceDriverService(handler=mock_driver, resource_driver_config=mock_resource_driver_config)
        self.assertEqual(str(context.exception), 'driver_files_manager argument not provided')

    def test_init_without_monitor_service_when_async_enabled_throws_error(self):
        mock_service_driver = MagicMock()
        mock_driver_files_manager = MagicMock()
        mock_resource_driver_config = MagicMock()
        mock_resource_driver_config.async_messaging_enabled = True
        with self.assertRaises(ValueError) as context:
            ResourceDriverService(handler=mock_service_driver, resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager)
        self.assertEqual(str(context.exception), 'lifecycle_monitor_service argument not provided (required when async_messaging_enabled is True)')

    def test_init_without_request_queue_service_when_async_requests_enabled_throws_error(self):
        mock_service_driver = MagicMock()
        mock_driver_files_manager = MagicMock()
        mock_resource_driver_config = MagicMock()
        mock_resource_driver_config.async_messaging_enabled = False
        mock_resource_driver_config.lifecycle_request_queue.enabled = True
        with self.assertRaises(ValueError) as context:
            ResourceDriverService(handler=mock_service_driver, resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager)
        self.assertEqual(str(context.exception), 'lifecycle_request_queue argument not provided (required when lifecycle_request_queue.enabled is True)')

    def test_execute_with_request_queue(self):
        mock_service_driver = MagicMock()
        mock_request_queue = MagicMock()
        mock_driver_files_manager = MagicMock()
        mock_resource_driver_config = MagicMock()
        mock_resource_driver_config.async_messaging_enabled = False
        mock_resource_driver_config.lifecycle_request_queue.enabled = True
        service = ResourceDriverService(handler=mock_service_driver, resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager, lifecycle_request_queue=mock_request_queue)
        lifecycle_name = 'Install'
        driver_files = '123'
        system_properties = {'resourceId': '1'}
        resource_properties = {'propA': 'valueA'}
        request_properties = {'reqPropA': 'reqValueA'}
        internal_resources = [{'id': '123', 'name': 'Test', 'type': 'TestType'}]
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location)
        self.assertIsNotNone(result.request_id)
        mock_service_driver.execute_lifecycle.assert_not_called()
        mock_request_queue.queue_lifecycle_request.assert_called_once()
        name, args, kwargs = mock_request_queue.queue_lifecycle_request.mock_calls[0]
        request = args[0]
        self.assert_requests_equal(request, {
            'request_id': result.request_id,
            'lifecycle_name': 'Install',
            'driver_files': '123',
            'resource_properties': resource_properties,
            'system_properties': system_properties,
            'request_properties': request_properties,
            'internal_resources': internal_resources,
            'deployment_location': deployment_location
        })

    def test_execute_uses_driver_handler(self):
        mock_service_driver = MagicMock()
        execute_response = LifecycleExecuteResponse('123')
        mock_service_driver.execute_lifecycle.return_value = execute_response
        mock_driver_files_manager = MagicMock()
        mock_script_tree = MagicMock()
        mock_driver_files_manager.build_tree.return_value = mock_script_tree
        mock_resource_driver_config = MagicMock()
        mock_resource_driver_config.lifecycle_request_queue.enabled = False
        service = ResourceDriverService(handler=mock_service_driver, resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager)
        lifecycle_name = 'start'
        driver_files = b'123'
        system_properties = self.__propvaluemap({'resourceId': '999'})
        resource_properties = self.__propvaluemap({'a': 1})
        request_properties = self.__propvaluemap({'reqPropA': 'reqValueA'})
        internal_resources = [{'id': '123', 'name': 'Test', 'type': 'TestType'}]
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location)
        mock_service_driver.execute_lifecycle.assert_called_once_with(lifecycle_name, mock_script_tree, self.__propvaluemap(system_properties), self.__propvaluemap(resource_properties), self.__propvaluemap(request_properties), InternalResources.from_list(internal_resources), deployment_location)
        self.assertEqual(result, execute_response)

    def test_execute_uses_file_manager(self):
        mock_service_driver = MagicMock()
        execute_response = LifecycleExecuteResponse('123')
        mock_service_driver.execute_lifecycle.return_value = execute_response
        mock_driver_files_manager = MagicMock()
        mock_script_tree = MagicMock()
        mock_driver_files_manager.build_tree.return_value = mock_script_tree
        mock_resource_driver_config = MagicMock()
        mock_resource_driver_config.lifecycle_request_queue.enabled = False
        service = ResourceDriverService(handler=mock_service_driver, resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager)
        lifecycle_name = 'start'
        driver_files = b'123'
        system_properties = {'resourceId': '999'}
        resource_properties = {'a': 1}
        request_properties = {'reqPropA': 'reqValueA'}
        internal_resources = [{'id': '123', 'name': 'Test', 'type': 'TestType'}]
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location)
        mock_driver_files_manager.build_tree.assert_called_once_with(ANY, driver_files)
        mock_service_driver.execute_lifecycle.assert_called_once_with(lifecycle_name, mock_script_tree, self.__propvaluemap(system_properties), self.__propvaluemap(resource_properties), self.__propvaluemap(request_properties), InternalResources.from_list(internal_resources), deployment_location)
        self.assertEqual(result, execute_response)

    def test_execute_uses_monitor_when_async_enabled(self):
        mock_service_driver = MagicMock()
        execute_response = LifecycleExecuteResponse('123')
        mock_service_driver.execute_lifecycle.return_value = execute_response
        mock_driver_files_manager = MagicMock()
        mock_pointer = MagicMock()
        mock_driver_files_manager.build_pointer.return_value = mock_pointer
        mock_resource_driver_config = MagicMock()
        mock_resource_driver_config.async_messaging_enabled = True
        mock_resource_driver_config.lifecycle_request_queue.enabled = False
        mock_lifecycle_monitor_service = MagicMock()
        service = ResourceDriverService(handler=mock_service_driver, resource_driver_config=mock_resource_driver_config, driver_files_manager=mock_driver_files_manager, lifecycle_monitor_service=mock_lifecycle_monitor_service)
        lifecycle_name = 'start'
        driver_files = b'123'
        system_properties = {'resourceId': '999'}
        resource_properties = {'a': 1}
        request_properties = {'reqPropA': 'reqValueA'}
        internal_resources = [{'id': '123', 'name': 'Test', 'type': 'TestType'}]
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location)
        mock_lifecycle_monitor_service.monitor_execution.assert_called_once_with('123', deployment_location)

class TestLifecycleExecutionMonitoringService(unittest.TestCase):

    def setUp(self):
        self.mock_job_queue = MagicMock()
        self.mock_lifecycle_messaging_service = MagicMock()
        self.mock_driver = MagicMock()
    
    def test_init_without_job_queue_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleExecutionMonitoringService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        self.assertEqual(str(context.exception), 'job_queue_service argument not provided')

    def test_init_without_lifecycle_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, handler=self.mock_driver)
        self.assertEqual(str(context.exception), 'lifecycle_messaging_service argument not provided')

    def test_init_without_driver_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service)
        self.assertEqual(str(context.exception), 'handler argument not provided')

    def test_init_registers_handler_to_job_queue(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        self.mock_job_queue.register_job_handler.assert_called_once_with('LifecycleExecutionMonitoring', monitoring_service.job_handler)

    def test_monitor_execution_schedules_job(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        monitoring_service.monitor_execution('req123', {'name': 'TestDl'})
        self.mock_job_queue.queue_job.assert_called_once_with({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })

    def test_monitor_execution_throws_error_when_request_id_is_none(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_execution(None, {'name': 'TestDl'})
        self.assertEqual(str(context.exception), 'Cannot monitor task when request_id is not given')
        
    def test_monitor_execution_throws_error_when_deployment_location_is_none(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_execution('req123', None)
        self.assertEqual(str(context.exception), 'Cannot monitor task when deployment_location is not given')

    def test_job_handler_does_not_mark_job_as_finished_if_in_progress(self):
        self.mock_driver.get_lifecycle_execution.return_value = LifecycleExecution('req123', 'IN_PROGRESS', None)
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})

    def test_job_handler_does_not_mark_job_as_finished_if_temporary_error_thrown(self):
        self.mock_driver.get_lifecycle_execution.side_effect = TemporaryResourceDriverError('Retry it')
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})

    def test_job_handler_marks_job_as_finished_if_request_not_found_error_thrown(self):
        self.mock_driver.get_lifecycle_execution.side_effect = RequestNotFoundError('Not found')
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})


    def test_job_handler_sends_message_when_task_complete(self):
        self.mock_driver.get_lifecycle_execution.return_value = LifecycleExecution('req123', 'COMPLETE', None)
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_called_once_with(self.mock_driver.get_lifecycle_execution.return_value)
        
    def test_job_handler_sends_message_when_task_failed(self):
        self.mock_driver.get_lifecycle_execution.return_value = LifecycleExecution('req123', 'FAILED', None)
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_called_once_with(self.mock_driver.get_lifecycle_execution.return_value)
        
    def test_job_handler_ignores_job_without_request_id(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_not_called()
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_not_called()

    def test_job_handler_ignores_job_without_deployment_location_id(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, handler=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123'
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_not_called()
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_not_called()

class TestLifecycleMessagingService(unittest.TestCase):

    def setUp(self):
        self.mock_postal_service = MagicMock()
        self.mock_topics_configuration = MagicMock(lifecycle_execution_events = TopicConfigProperties(name='lifecycle_execution_events_topic'))

    def test_init_without_postal_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleMessagingService(topics_configuration=self.mock_topics_configuration)
        self.assertEqual(str(context.exception), 'postal_service argument not provided')

    def test_init_without_topics_configuration_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleMessagingService(postal_service=self.mock_postal_service)
        self.assertEqual(str(context.exception), 'topics_configuration argument not provided')

    def test_init_without_lifecycle_execution_events_topic_throws_error(self):
        mock_topics_configuration = MagicMock(lifecycle_execution_events = None)
        with self.assertRaises(ValueError) as context:
            LifecycleMessagingService(postal_service=self.mock_postal_service, topics_configuration=mock_topics_configuration)
        self.assertEqual(str(context.exception), 'lifecycle_execution_events topic must be set')

    def test_init_without_lifecycle_execution_events_topic_name_throws_error(self):
        mock_topics_configuration = MagicMock(lifecycle_execution_events = TopicConfigProperties())
        with self.assertRaises(ValueError) as context:
            LifecycleMessagingService(postal_service=self.mock_postal_service, topics_configuration=mock_topics_configuration)
        self.assertEqual(str(context.exception), 'lifecycle_execution_events topic name must be set')

    def test_send_lifecycle_execution_sends_message(self):
        messaging_service = LifecycleMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        messaging_service.send_lifecycle_execution(LifecycleExecution('req123', 'FAILED', FailureDetails(FAILURE_CODE_INTERNAL_ERROR, 'because it was meant to fail')))
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, self.mock_topics_configuration.lifecycle_execution_events.name)
        self.assertIsInstance(envelope_arg.message, Message)
        self.assertEqual(envelope_arg.message.content, b'{"requestId": "req123", "status": "FAILED", "failureDetails": {"failureCode": "INTERNAL_ERROR", "description": "because it was meant to fail"}, "outputs": {}, "internalResources": []}')
    
    def test_send_lifecycle_execution_throws_error_when_task_is_none(self):
        messaging_service = LifecycleMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        with self.assertRaises(ValueError) as context:
            messaging_service.send_lifecycle_execution(None)
        self.assertEqual(str(context.exception), 'lifecycle_execution must be set to send an lifecycle execution event')

test_valid_scripts_zip_file = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'resources', 'scripts_packages', 'test_valid.zip')

class TestDriverFilesManagerService(unittest.TestCase):

    def setUp(self):
        self.tmp_workspace = tempfile.mkdtemp()
        self.mock_resource_driver_config = MagicMock(scripts_workspace=self.tmp_workspace)

    def tearDown(self):
        shutil.rmtree(self.tmp_workspace)

    def test_auto_creates_workspace(self):
        workspace = os.path.join(self.tmp_workspace, 'my_workspace')
        self.assertFalse(os.path.exists(workspace))
        mock_resource_driver_config = MagicMock(scripts_workspace=workspace)
        service = DriverFilesManagerService(resource_driver_config=mock_resource_driver_config)
        self.assertTrue(os.path.exists(workspace))

    def test_build_tree(self):
        service = DriverFilesManagerService(resource_driver_config=self.mock_resource_driver_config)
        with open(test_valid_scripts_zip_file, 'rb') as file:
            file_content = base64.b64encode(file.read())
        service.build_tree('test', file_content)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'start.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'lib')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'lib', 'lib1.sh')))

    def test_build_tree_replaces_existing(self):
        os.mkdir(os.path.join(self.tmp_workspace, 'test'))
        os.mkdir(os.path.join(self.tmp_workspace, 'test', 'oldlib'))
        with open(os.path.join(self.tmp_workspace, 'test', 'start.sh'), 'w') as file:
            pass
        with open(os.path.join(self.tmp_workspace, 'test', 'oldlib', 'stop.sh'), 'w') as file:
            pass
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'start.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'oldlib', 'stop.sh')))
        service = DriverFilesManagerService(resource_driver_config=self.mock_resource_driver_config)
        with open(test_valid_scripts_zip_file, 'rb') as file:
            file_content = base64.b64encode(file.read())
        service.build_tree('test', file_content)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'start.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'lib')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'lib', 'lib1.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'oldlib', 'stop.sh')))
        