import unittest
from ignition.service.health import HealthCheckerService, HealthReport, TestResult, HealthStatus

class TestHealthReport(unittest.TestCase):

    def test_diagnosis_all_ok(self):
        report = HealthReport([TestResult('A', HealthStatus.OK), TestResult('B', HealthStatus.OK)])
        self.assertEqual(report.diagnosis, HealthStatus.OK)

    def test_diagnosis_with_unhealthy(self):
        report = HealthReport([TestResult('A', HealthStatus.OK), TestResult('B', HealthStatus.UNHEALTHY), TestResult('C', HealthStatus.OK)])
        self.assertEqual(report.diagnosis, HealthStatus.UNHEALTHY)

    def test_diagnosis_is_unhealthy_false_when_all_ok(self):
        report = HealthReport([TestResult('A', HealthStatus.OK), TestResult('B', HealthStatus.OK)])
        self.assertFalse(report.diagnosis_is_unhealthy)

    def test_diagnosis_is_unhealthy_true_when_unhealthy(self):
        report = HealthReport([TestResult('A', HealthStatus.OK), TestResult('B', HealthStatus.UNHEALTHY)])
        self.assertTrue(report.diagnosis_is_unhealthy)

    def test_dict_copy(self):
        report = HealthReport([TestResult('A', HealthStatus.OK), TestResult('B', HealthStatus.UNHEALTHY), TestResult('C', HealthStatus.OK)])
        dict_copy = report.dict_copy()
        self.assertEqual(dict_copy, {
            'vitals': {
                'A': {'status': HealthStatus.OK},
                'B': {'status': HealthStatus.UNHEALTHY},
                'C': {'status': HealthStatus.OK}
            }
        })

class TestHealthCheckerService(unittest.TestCase):

    def test_perform_checkup(self):
        service = HealthCheckerService()
        report = service.perform_checkup()
        self.assertIsInstance(report, HealthReport)
        self.assertEqual(len(report.vitals), 1)
        self.assertEqual(report.vitals[0].name, 'app')
        self.assertEqual(report.vitals[0].status, HealthStatus.OK)
        