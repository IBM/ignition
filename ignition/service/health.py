from ignition.service.framework import Service, Capability, interface

class HealthChecker(Capability):

    @interface
    def perform_checkup(self):
        pass

class HealthStatus:
    OK = "OK"
    UNHEALTHY = "UNHEALTHY"

class TestResult:
    """
    An entry in the Health report, describing the health of a single component in the application
    """
    def __init__(self, name, status):
        self.name = name
        self.status = status

class HealthReport:
    """
    Report for the Health of the application
    """
    def __init__(self, vitals):
        self.vitals = vitals

    @property
    def diagnosis(self):
        """Check if a key vital is unhealthy"""
        for vital in self.vitals:
            if vital.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        return HealthStatus.OK

    @property
    def diagnosis_is_unhealthy(self):
        return self.diagnosis == HealthStatus.UNHEALTHY

    def dict_copy(self):
        report = {'vitals': {}}
        for vital in self.vitals:
            report['vitals'][vital.name] = {'status': vital.status}
        return report

class HealthCheckerService(Service, HealthChecker):

    def perform_checkup(self):
        app_vital = TestResult('app', HealthStatus.OK)
        return HealthReport([app_vital])
