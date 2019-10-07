import unittest
from unittest.mock import patch, MagicMock
from ignition.api.exceptions import BadRequest
from ignition.model.infrastructure import InfrastructureTask, CreateInfrastructureResponse, DeleteInfrastructureResponse, FindInfrastructureResponse, FindInfrastructureResult
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR
from ignition.service.infrastructure import InfrastructureService, InfrastructureApiService, InfrastructureTaskMonitoringService, InfrastructureMessagingService
from ignition.service.messaging import Envelope, Message

class TestInfrastructureApiService(unittest.TestCase):

    @patch('ignition.service.infrastructure.logging_context')
    def test_init_without_service_throws_error(self, logging_context):
        with self.assertRaises(ValueError) as context:
            InfrastructureApiService()
        self.assertEqual(str(context.exception), 'No service instance provided')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create(self, logging_context):
        log_context = MagicMock()
        mock_service = MagicMock()
        mock_service.create_infrastructure.return_value = CreateInfrastructureResponse('123', '456')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.create(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'inputs': {'a': 1}, 'deploymentLocation': {'name': 'test'} } })
        mock_service.create_infrastructure.assert_called_once_with('template', 'TOSCA', {'a': 1}, {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456'})
        self.assertEqual(code, 202)

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_template(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'templateType': 'TOSCA', 'inputs': {'a': 1}, 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'template\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_template_type(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'template': 'template', 'inputs': {'a': 1}, 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'templateType\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'inputs': {'a': 1}, 'template': 'template', 'templateType': 'TOSCA' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_inputs_uses_default(self, logging_context):
        mock_service = MagicMock()
        mock_service.create_infrastructure.return_value = CreateInfrastructureResponse('123', '456')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.create(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'deploymentLocation': {'name': 'test'} } })
        mock_service.create_infrastructure.assert_called_once_with('template', 'TOSCA', {}, {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456'})
        self.assertEqual(code, 202)

    @patch('ignition.service.infrastructure.logging_context')
    def test_delete(self, logging_context):
        mock_service = MagicMock()
        mock_service.delete_infrastructure.return_value = DeleteInfrastructureResponse('123', '456')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.delete(**{ 'body': { 'infrastructureId': '123', 'deploymentLocation': {'name': 'test'} } })
        mock_service.delete_infrastructure.assert_called_once_with('123', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456'})
        self.assertEqual(code, 202)

    @patch('ignition.service.infrastructure.logging_context')
    def test_delete_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.delete(**{ 'body': { 'infrastructureId': '123' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_delete_missing_infrastructure_id(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.delete(**{ 'body': { 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'infrastructureId\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_query(self, logging_context):
        mock_service = MagicMock()
        mock_service.get_infrastructure_task.return_value = InfrastructureTask('123', '456', 'IN_PROGRESS')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        mock_service.get_infrastructure_task.assert_called_once_with('123', '456', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456', 'status': 'IN_PROGRESS'})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_with_outputs(self, logging_context):
        mock_service = MagicMock()
        mock_service.get_infrastructure_task.return_value = InfrastructureTask('123', '456', 'COMPLETE', None, {'a': '1'})
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        mock_service.get_infrastructure_task.assert_called_once_with('123', '456', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456', 'status': 'COMPLETE', 'outputs': {'a': '1'}})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_failed_task(self, logging_context):
        mock_service = MagicMock()
        mock_service.get_infrastructure_task.return_value = InfrastructureTask('123', '456', 'FAILED', FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, 'because it was meant to fail'))
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        mock_service.get_infrastructure_task.assert_called_once_with('123', '456', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456', 'status': 'FAILED', 'failureDetails': { 'failureCode': FAILURE_CODE_INFRASTRUCTURE_ERROR, 'description': 'because it was meant to fail'}})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_missing_infrastructure_id(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.query(**{ 'body': { 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'infrastructureId\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_missing_request_id(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.query(**{ 'body': { 'infrastructureId': '123', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'requestId\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find(self, logging_context):
        mock_service = MagicMock()
        mock_service.find_infrastructure.return_value = FindInfrastructureResponse(FindInfrastructureResult('123', {'b': 2}))
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.find(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'instanceName': 'test', 'deploymentLocation': {'name': 'test'} } })
        mock_service.find_infrastructure.assert_called_once_with('template', 'TOSCA', 'test', {'name': 'test'})
        self.assertEqual(response, {'result': {'infrastructureId': '123', 'outputs': {'b': 2} } })
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_not_found(self, logging_context):
        mock_service = MagicMock()
        mock_service.find_infrastructure.return_value = FindInfrastructureResponse(None)
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.find(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'instanceName': 'test', 'deploymentLocation': {'name': 'test'} } })
        mock_service.find_infrastructure.assert_called_once_with('template', 'TOSCA', 'test', {'name': 'test'})
        self.assertEqual(response, {'result': None})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_template(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'templateType': 'TOSCA', 'inputs': {'a': 1}, 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'template\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_template_type(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'template': 'template', 'inputs': {'a': 1}, 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'templateType\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'instanceName': 'test', 'template': 'template', 'templateType': 'TOSCA' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_instance_name(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'deploymentLocation': {'name': 'test' }, 'template': 'template', 'templateType': 'TOSCA' } })
        self.assertEqual(str(context.exception), '\'instanceName\' is a required field but was not found in the request data body')

class TestInfrastructureService(unittest.TestCase):

    def test_init_without_driver_throws_error(self):
        mock_infrastructure_config = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureService(infrastructure_config=mock_infrastructure_config)
        self.assertEqual(str(context.exception), 'driver argument not provided')

    def test_init_without_configuration_throws_error(self):
        mock_service_driver = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureService(driver=mock_service_driver)
        self.assertEqual(str(context.exception), 'infrastructure_config argument not provided')

    def test_init_without_monitor_service_when_async_enabled_throws_error(self):
        mock_service_driver = MagicMock()
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = True
        with self.assertRaises(ValueError) as context:
            InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        self.assertEqual(str(context.exception), 'inf_monitor_service argument not provided (required when async_messaging_enabled is True)')

    def test_create_infrastructure_uses_driver(self):
        mock_service_driver = MagicMock()
        create_response = CreateInfrastructureResponse('test', 'test_req')
        mock_service_driver.create_infrastructure.return_value = create_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        template = 'template'
        template_type = 'TOSCA'
        inputs = {'inputA': 'valueA'}
        deployment_location = {'name': 'TestDl'}
        result = service.create_infrastructure(template, template_type, inputs, deployment_location)
        mock_service_driver.create_infrastructure.assert_called_once_with(template, template_type, inputs, deployment_location)
        self.assertEqual(result, create_response)

    def test_create_infrastructure_uses_monitor_when_async_enabled(self):
        mock_service_driver = MagicMock()
        create_response = CreateInfrastructureResponse('test', 'test_req')
        mock_service_driver.create_infrastructure.return_value = create_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = True
        mock_inf_monitor_service = MagicMock()
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config, inf_monitor_service=mock_inf_monitor_service)
        template = 'template'
        template_type = 'TOSCA'
        inputs = {'inputA': 'valueA'}
        deployment_location = {'name': 'TestDl'}
        result = service.create_infrastructure(template, template_type, inputs, deployment_location)
        mock_inf_monitor_service.monitor_task.assert_called_once_with('test', 'test_req', deployment_location)

    def test_get_infrastructure_task_uses_driver(self):
        mock_service_driver = MagicMock()
        retuned_task = InfrastructureTask('test', 'test_req', 'COMPLETE', None)
        mock_service_driver.get_infrastructure_task.return_value = retuned_task
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        infrastructure_id = 'test'
        request_id = 'test_req'
        deployment_location = {'name': 'TestDl'}
        result = service.get_infrastructure_task(infrastructure_id, request_id, deployment_location)
        mock_service_driver.get_infrastructure_task.assert_called_once_with(infrastructure_id, request_id, deployment_location)
        self.assertEqual(result, retuned_task)

    def test_delete_infrastructure_uses_driver(self):
        mock_service_driver = MagicMock()
        delete_response = DeleteInfrastructureResponse('test', 'test_req')
        mock_service_driver.delete_infrastructure.return_value = delete_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        infrastructure_id = 'test'
        deployment_location = {'name': 'TestDl'}
        result = service.delete_infrastructure(infrastructure_id, deployment_location)
        mock_service_driver.delete_infrastructure.assert_called_once_with(infrastructure_id, deployment_location)
        self.assertEqual(result, delete_response)

    def test_delete_infrastructure_uses_monitor_when_async_enabled(self):
        mock_service_driver = MagicMock()
        delete_response = DeleteInfrastructureResponse('test', 'test_req')
        mock_service_driver.delete_infrastructure.return_value = delete_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = True
        mock_inf_monitor_service = MagicMock()
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config, inf_monitor_service=mock_inf_monitor_service)
        infrastructure_id = 'test'
        deployment_location = {'name': 'TestDl'}
        result = service.delete_infrastructure(infrastructure_id, deployment_location)
        mock_inf_monitor_service.monitor_task.assert_called_once_with('test', 'test_req', deployment_location)

    def test_find_infrastructure_uses_driver(self):
        mock_service_driver = MagicMock()
        find_response = FindInfrastructureResponse(FindInfrastructureResult('123', {'outputA': 1}))
        mock_service_driver.find_infrastructure.return_value = find_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        template = 'template'
        template_type = 'TOSCA'
        instance_name = 'valueA'
        deployment_location = {'name': 'TestDl'}
        result = service.find_infrastructure(template, template_type, instance_name, deployment_location)
        mock_service_driver.find_infrastructure.assert_called_once_with(template, template_type, instance_name, deployment_location)
        self.assertEqual(result, find_response)


class TestInfrastructureTaskMonitoringService(unittest.TestCase):

    def setUp(self):
        self.mock_job_queue = MagicMock()
        self.mock_inf_messaging_service = MagicMock()
        self.mock_driver = MagicMock()
    
    def test_init_without_job_queue_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureTaskMonitoringService(inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        self.assertEqual(str(context.exception), 'job_queue_service argument not provided')

    def test_init_without_inf_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, driver=self.mock_driver)
        self.assertEqual(str(context.exception), 'inf_messaging_service argument not provided')

    def test_init_without_driver_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service)
        self.assertEqual(str(context.exception), 'driver argument not provided')

    def test_init_registers_handler_to_job_queue(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        self.mock_job_queue.register_job_handler.assert_called_once_with('InfrastructureTaskMonitoring', monitoring_service.job_handler)

    def test_monitor_task_schedules_job(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        monitoring_service.monitor_task('inf123', 'req123', {'name': 'TestDl'})
        self.mock_job_queue.queue_job.assert_called_once_with({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })

    def test_monitor_task_throws_error_when_infrastructure_id_is_none(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_task(None, 'req123', {'name': 'TestDl'})
        self.assertEqual(str(context.exception), 'Cannot monitor task when infrastructure_id is not given')
    
    def test_monitor_task_throws_error_when_request_id_is_none(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_task('inf123', None, {'name': 'TestDl'})
        self.assertEqual(str(context.exception), 'Cannot monitor task when request_id is not given')
        
    def test_monitor_task_throws_error_when_deployment_location_is_none(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_task('inf123', 'req123', None)
        self.assertEqual(str(context.exception), 'Cannot monitor task when deployment_location is not given')

    def test_job_handler_does_not_mark_job_as_finished_if_in_progress(self):
        self.mock_driver.get_infrastructure_task.return_value = InfrastructureTask('inf123', 'req123', 'IN_PROGRESS', None)
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})

    def test_job_handler_sends_message_when_task_complete(self):
        self.mock_driver.get_infrastructure_task.return_value = InfrastructureTask('inf123', 'req123', 'COMPLETE', None)
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})
        self.mock_inf_messaging_service.send_infrastructure_task.assert_called_once_with(self.mock_driver.get_infrastructure_task.return_value)
        
    def test_job_handler_sends_message_when_task_failed(self):
        self.mock_driver.get_infrastructure_task.return_value = InfrastructureTask('inf123', 'req123', 'FAILED', None)
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})
        self.mock_inf_messaging_service.send_infrastructure_task.assert_called_once_with(self.mock_driver.get_infrastructure_task.return_value)
         
    def test_job_handler_ignores_job_without_infrastructure_id(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_not_called()
        self.mock_inf_messaging_service.send_infrastructure_task.assert_not_called()

    def test_job_handler_ignores_job_without_request_id(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_not_called()
        self.mock_inf_messaging_service.send_infrastructure_task.assert_not_called()

    def test_job_handler_ignores_job_without_deployment_location_id(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123'
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_not_called()
        self.mock_inf_messaging_service.send_infrastructure_task.assert_not_called()

class TestInfrastructureMessagingService(unittest.TestCase):

    def setUp(self):
        self.mock_postal_service = MagicMock()
        self.mock_topics_configuration = MagicMock(infrastructure_task_events = 'task_events_topic')

    def test_init_without_postal_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(topics_configuration=self.mock_topics_configuration)
        self.assertEqual(str(context.exception), 'postal_service argument not provided')

    def test_init_without_topics_configuration_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(postal_service=self.mock_postal_service)
        self.assertEqual(str(context.exception), 'topics_configuration argument not provided')

    def test_init_without_infrastructure_task_events_topic_throws_error(self):
        mock_topics_configuration = MagicMock(infrastructure_task_events = None)
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=mock_topics_configuration)
        self.assertEqual(str(context.exception), 'infrastructure_task_events topic must be set')

    def test_send_infrastructure_task_sends_message(self):
        messaging_service = InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        messaging_service.send_infrastructure_task(InfrastructureTask('inf123', 'req123', 'FAILED', FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, 'because it was meant to fail')))
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, self.mock_topics_configuration.infrastructure_task_events)
        self.assertIsInstance(envelope_arg.message, Message)
        self.assertEqual(envelope_arg.message.content, b'{"requestId": "req123", "infrastructureId": "inf123", "status": "FAILED", "failureDetails": {"failureCode": "INFRASTRUCTURE_ERROR", "description": "because it was meant to fail"}}')
    
    def test_send_infrastrucutre_task_throws_error_when_task_is_none(self):
        messaging_service = InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        with self.assertRaises(ValueError) as context:
            messaging_service.send_infrastructure_task(None)
        self.assertEqual(str(context.exception), 'infrastructure_task must be set to send an infrastructure task event')

