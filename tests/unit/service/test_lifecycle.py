import unittest
from unittest.mock import patch, MagicMock, ANY
from ignition.api.exceptions import BadRequest
from ignition.service.lifecycle import LifecycleApiService, LifecycleService, LifecycleExecutionMonitoringService, LifecycleMessagingService, LifecycleScriptFileManagerService
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution
from ignition.model.failure import FailureDetails, FAILURE_CODE_INTERNAL_ERROR
from ignition.service.messaging import Envelope, Message
import zipfile
import os
import tempfile
import shutil
import base64

class TestLifecycleApiService(unittest.TestCase):

    @patch('ignition.service.lifecycle.logging_context')
    def test_init_without_service_throws_error(self, logging_context):
        with self.assertRaises(ValueError) as context:
            LifecycleApiService()
        self.assertEqual(str(context.exception), 'No service instance provided')

    @patch('ignition.service.lifecycle.logging_context')
    def test_execute(self, logging_context):
        mock_service = MagicMock()
        mock_service.execute_lifecycle.return_value = LifecycleExecuteResponse('123')
        controller = LifecycleApiService(service=mock_service)
        response, code = controller.execute(**{ 'body': { 'lifecycleName': 'start', 'systemProperties': {'resourceId': 1}, 'properties': {'a': 2}, 'lifecycleScripts': b'123', 'deploymentLocation': {'name': 'test'} } })
        mock_service.execute_lifecycle.assert_called_once_with('start', b'123', {'resourceId': 1}, {'a': 2}, {'name': 'test'})
        self.assertEqual(response, {'requestId': '123'})
        self.assertEqual(code, 202)
        logging_context.set_from_headers.assert_called_once()

    @patch('ignition.service.lifecycle.logging_context')
    def test_execute_missing_lifecycle_name(self, logging_context):
        mock_service = MagicMock()
        controller = LifecycleApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute(**{ 'body': { 'systemProperties': {'resourceId': 1}, 'properties': {'a': 2}, 'lifecycleScripts': b'123', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'lifecycleName\' is a required field but was not found in the request data body')

    @patch('ignition.service.lifecycle.logging_context')
    def test_execute_missing_lifecycle_scripts(self, logging_context):
        mock_service = MagicMock()
        controller = LifecycleApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute(**{ 'body': { 'lifecycleName': 'start', 'systemProperties': {'resourceId': 1}, 'properties': {'a': 2}, 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'lifecycleScripts\' is a required field but was not found in the request data body')

    @patch('ignition.service.lifecycle.logging_context')
    def test_execute_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = LifecycleApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute(**{ 'body': { 'lifecycleName': 'start', 'systemProperties': {'resourceId': 1}, 'properties': {'a': 2}, 'lifecycleScripts': b'123' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.lifecycle.logging_context')
    def test_execute_missing_system_properties(self, logging_context):
        mock_service = MagicMock()
        controller = LifecycleApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.execute(**{ 'body': { 'lifecycleName': 'start', 'properties': {'a': 2}, 'lifecycleScripts': b'123', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'systemProperties\' is a required field but was not found in the request data body')

    @patch('ignition.service.lifecycle.logging_context')
    def test_execute_missing_properties(self, logging_context):
        mock_service = MagicMock()
        mock_service.execute_lifecycle.return_value = LifecycleExecuteResponse('123')
        controller = LifecycleApiService(service=mock_service)
        response, code = controller.execute(**{ 'body': { 'lifecycleName': 'start', 'systemProperties': {'resourceId': 1}, 'lifecycleScripts': b'123', 'deploymentLocation': {'name': 'test'} } })
        mock_service.execute_lifecycle.assert_called_once_with('start', b'123', {'resourceId': 1}, {}, {'name': 'test'})
        self.assertEqual(response, {'requestId': '123'})
        self.assertEqual(code, 202)

class TestLifecycleService(unittest.TestCase):

    def test_init_without_driver_throws_error(self):
        mock_lifecycle_config = MagicMock()
        mock_script_file_manager = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleService(lifecycle_config=mock_lifecycle_config, script_file_manager=mock_script_file_manager)
        self.assertEqual(str(context.exception), 'driver argument not provided')

    def test_init_without_configuration_throws_error(self):
        mock_driver = MagicMock()
        mock_script_file_manager = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleService(driver=mock_driver, script_file_manager=mock_script_file_manager)
        self.assertEqual(str(context.exception), 'lifecycle_config argument not provided')

    def test_init_without_script_file_manager_throws_error(self):
        mock_driver = MagicMock()
        mock_lifecycle_config = MagicMock()
        with self.assertRaises(ValueError) as context:
            LifecycleService(driver=mock_driver, lifecycle_config=mock_lifecycle_config)
        self.assertEqual(str(context.exception), 'script_file_manager argument not provided')

    def test_init_without_monitor_service_when_async_enabled_throws_error(self):
        mock_service_driver = MagicMock()
        mock_script_file_manager = MagicMock()
        mock_lifecycle_config = MagicMock()
        mock_lifecycle_config.async_messaging_enabled = True
        with self.assertRaises(ValueError) as context:
            LifecycleService(driver=mock_service_driver, lifecycle_config=mock_lifecycle_config, script_file_manager=mock_script_file_manager)
        self.assertEqual(str(context.exception), 'lifecycle_monitor_service argument not provided (required when async_messaging_enabled is True)')

    def test_execute_uses_driver(self):
        mock_service_driver = MagicMock()
        execute_response = LifecycleExecuteResponse('123')
        mock_service_driver.execute_lifecycle.return_value = execute_response
        mock_script_file_manager = MagicMock()
        mock_script_tree = MagicMock()
        mock_script_file_manager.build_tree.return_value = mock_script_tree
        mock_lifecycle_config = MagicMock()
        service = LifecycleService(driver=mock_service_driver, lifecycle_config=mock_lifecycle_config, script_file_manager=mock_script_file_manager)
        lifecycle_name = 'start'
        lifecycle_scripts = b'123'
        system_properties = {'resourceId': '999'}
        properties = {'a': 1}
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, lifecycle_scripts, system_properties, properties, deployment_location)
        mock_service_driver.execute_lifecycle.assert_called_once_with(lifecycle_name, mock_script_tree, system_properties, properties, deployment_location)
        self.assertEqual(result, execute_response)

    def test_execute_uses_file_manager(self):
        mock_service_driver = MagicMock()
        execute_response = LifecycleExecuteResponse('123')
        mock_service_driver.execute_lifecycle.return_value = execute_response
        mock_script_file_manager = MagicMock()
        mock_script_tree = MagicMock()
        mock_script_file_manager.build_tree.return_value = mock_script_tree
        mock_lifecycle_config = MagicMock()
        service = LifecycleService(driver=mock_service_driver, lifecycle_config=mock_lifecycle_config, script_file_manager=mock_script_file_manager)
        lifecycle_name = 'start'
        lifecycle_scripts = b'123'
        system_properties = {'resourceId': '999'}
        properties = {'a': 1}
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, lifecycle_scripts, system_properties, properties, deployment_location)
        mock_script_file_manager.build_tree.assert_called_once_with(ANY, lifecycle_scripts)
        mock_service_driver.execute_lifecycle.assert_called_once_with(lifecycle_name, mock_script_tree, system_properties, properties, deployment_location)
        self.assertEqual(result, execute_response)

    def test_execute_uses_monitor_when_async_enabled(self):
        mock_service_driver = MagicMock()
        execute_response = LifecycleExecuteResponse('123')
        mock_service_driver.execute_lifecycle.return_value = execute_response
        mock_script_file_manager = MagicMock()
        mock_pointer = MagicMock()
        mock_script_file_manager.build_pointer.return_value = mock_pointer
        mock_lifecycle_config = MagicMock()
        mock_lifecycle_config.async_messaging_enabled = True
        mock_lifecycle_monitor_service = MagicMock()
        service = LifecycleService(driver=mock_service_driver, lifecycle_config=mock_lifecycle_config, script_file_manager=mock_script_file_manager, lifecycle_monitor_service=mock_lifecycle_monitor_service)
        lifecycle_name = 'start'
        lifecycle_scripts = b'123'
        system_properties = {'resourceId': '999'}
        properties = {'a': 1}
        deployment_location = {'name': 'TestDl'}
        result = service.execute_lifecycle(lifecycle_name, lifecycle_scripts, system_properties, properties, deployment_location)
        mock_lifecycle_monitor_service.monitor_execution.assert_called_once_with('123', deployment_location)

class TestLifecycleExecutionMonitoringService(unittest.TestCase):

    def setUp(self):
        self.mock_job_queue = MagicMock()
        self.mock_lifecycle_messaging_service = MagicMock()
        self.mock_driver = MagicMock()
    
    def test_init_without_job_queue_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleExecutionMonitoringService(lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        self.assertEqual(str(context.exception), 'job_queue_service argument not provided')

    def test_init_without_lifecycle_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, driver=self.mock_driver)
        self.assertEqual(str(context.exception), 'lifecycle_messaging_service argument not provided')

    def test_init_without_driver_throws_error(self):
        with self.assertRaises(ValueError) as context:
            LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service)
        self.assertEqual(str(context.exception), 'driver argument not provided')

    def test_init_registers_handler_to_job_queue(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        self.mock_job_queue.register_job_handler.assert_called_once_with('LifecycleExecutionMonitoring', monitoring_service.job_handler)

    def test_monitor_execution_schedules_job(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        monitoring_service.monitor_execution('req123', {'name': 'TestDl'})
        self.mock_job_queue.queue_job.assert_called_once_with({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })

    def test_monitor_execution_throws_error_when_request_id_is_none(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_execution(None, {'name': 'TestDl'})
        self.assertEqual(str(context.exception), 'Cannot monitor task when request_id is not given')
        
    def test_monitor_execution_throws_error_when_deployment_location_is_none(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_execution('req123', None)
        self.assertEqual(str(context.exception), 'Cannot monitor task when deployment_location is not given')

    def test_job_handler_does_not_mark_job_as_finished_if_in_progress(self):
        self.mock_driver.get_lifecycle_execution.return_value = LifecycleExecution('req123', 'IN_PROGRESS', None)
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})

    def test_job_handler_sends_message_when_task_complete(self):
        self.mock_driver.get_lifecycle_execution.return_value = LifecycleExecution('req123', 'COMPLETE', None)
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
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
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_called_once_with('req123', {'name': 'TestDl'})
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_called_once_with(self.mock_driver.get_lifecycle_execution.return_value)
        
    def test_job_handler_ignores_job_without_request_id(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'LifecycleExecutionMonitoring',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_lifecycle_execution.assert_not_called()
        self.mock_lifecycle_messaging_service.send_lifecycle_execution.assert_not_called()

    def test_job_handler_ignores_job_without_deployment_location_id(self):
        monitoring_service = LifecycleExecutionMonitoringService(job_queue_service=self.mock_job_queue, lifecycle_messaging_service=self.mock_lifecycle_messaging_service, driver=self.mock_driver)
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
        self.mock_topics_configuration = MagicMock(lifecycle_execution_events = 'lifecycle_execution_events_topic')

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

    def test_send_lifecycle_execution_sends_message(self):
        messaging_service = LifecycleMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        messaging_service.send_lifecycle_execution(LifecycleExecution('req123', 'FAILED', FailureDetails(FAILURE_CODE_INTERNAL_ERROR, 'because it was meant to fail')))
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, self.mock_topics_configuration.lifecycle_execution_events)
        self.assertIsInstance(envelope_arg.message, Message)
        self.assertEqual(envelope_arg.message.content, b'{"requestId": "req123", "status": "FAILED", "failureDetails": {"failureCode": "INTERNAL_ERROR", "description": "because it was meant to fail"}}')
    
    def test_send_lifecycle_execution_throws_error_when_task_is_none(self):
        messaging_service = LifecycleMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        with self.assertRaises(ValueError) as context:
            messaging_service.send_lifecycle_execution(None)
        self.assertEqual(str(context.exception), 'lifecycle_execution must be set to send an lifecycle execution event')

test_valid_scripts_zip_file = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'resources', 'scripts_packages', 'test_valid.zip')

class TestLifecycleScriptFileManagerService(unittest.TestCase):

    def setUp(self):
        self.tmp_workspace = tempfile.mkdtemp()
        self.mock_lifecycle_config = MagicMock(scripts_workspace=self.tmp_workspace)

    def tearDown(self):
        shutil.rmtree(self.tmp_workspace)

    def test_build_tree(self):
        service = LifecycleScriptFileManagerService(lifecycle_config=self.mock_lifecycle_config)
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
        service = LifecycleScriptFileManagerService(lifecycle_config=self.mock_lifecycle_config)
        with open(test_valid_scripts_zip_file, 'rb') as file:
            file_content = base64.b64encode(file.read())
        service.build_tree('test', file_content)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'start.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'lib')))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'lib', 'lib1.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.tmp_workspace, 'test', 'oldlib', 'stop.sh')))
        