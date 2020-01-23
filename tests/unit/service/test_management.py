import unittest
from unittest.mock import MagicMock
from ignition.service.management import ManagementApiService, ManagementService
from ignition.service.health import HealthReport, HealthStatus, TestResult

class TestManagementApiService(unittest.TestCase):

    def test_health_response_when_healthy(self):
        mock_mgmt_service = MagicMock()
        report = HealthReport([])
        mock_mgmt_service.check_health.return_value = report
        service = ManagementApiService(mock_mgmt_service)
        response, status = service.health()
        self.assertEqual(response, report.dict_copy())
        self.assertEqual(status, 200)

    def test_health_response_when_unhealthy(self):
        mock_mgmt_service = MagicMock()
        report = HealthReport([TestResult('app', HealthStatus.UNHEALTHY)])
        mock_mgmt_service.check_health.return_value = report
        service = ManagementApiService(mock_mgmt_service)
        response, status = service.health()
        self.assertEqual(response, report.dict_copy())
        self.assertEqual(status, 503)

class TestManagementService(unittest.TestCase):

    def test_check_health(self):
        health_service = MagicMock()
        health_service.perform_checkup.return_value = HealthReport([])
        service = ManagementService(health_service)
        response = service.check_health()
        health_service.perform_checkup.assert_called_once()
        self.assertEqual(response, health_service.perform_checkup.return_value)

