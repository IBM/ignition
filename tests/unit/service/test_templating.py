import unittest
from ignition.service.templating import Jinja2TemplatingService, ResourceTemplateContextService
from ignition.templating import JinjaTemplate, ResourceContextBuilder

class TestJinja2TemplatingService(unittest.TestCase):

    def test_render(self):
        service = Jinja2TemplatingService()
        result = service.render('my {{ variable }} content', {'variable': 'dynamic'})
        self.assertEqual(result, 'my dynamic content')

class ExtendedResourceTemplateContextService(ResourceTemplateContextService):

    def _configure_additional_props(self, builder, system_properties, properties, deployment_location):
        sysA_value = system_properties.get('sysA')
        builder.add_system_property('extSysA', sysA_value)
        propA_value = properties.get('propA')
        builder.add_property('extPropA', propA_value)
        dlPropA_value = deployment_location.get('properties').get('dlPropA')
        builder.add_deployment_location_property('ExtDlPropA', dlPropA_value)

class TestResourceTemplateContextService(unittest.TestCase):

    def test_build(self):
        service = ResourceTemplateContextService()
        system_properties = {
            'sysA': 'A',
            'sysB': 'B'
        }
        properties = {
            'propA': 'A Prop'
        }
        deployment_location = {
            'name': 'Test',
            'type': 'Kubernetes',
            'properties': {
                'dlPropA': 'A DL Prop'
            }
        }
        result = service.build(system_properties, properties, deployment_location)
        self.assertEqual(result, {
            'propA': 'A Prop',
            'systemProperties': {
                'sysA': 'A',
                'sysB': 'B'
            }, 
            'deploymentLocationInst': {
                'name': 'Test',
                'type': 'Kubernetes',
                'properties': {
                    'dlPropA': 'A DL Prop'
                }
            }
        })

    def test_extension(self):
        service = ExtendedResourceTemplateContextService()
        system_properties = {
            'sysA': 'A',
            'sysB': 'B'
        }
        properties = {
            'propA': 'A Prop'
        }
        deployment_location = {
            'name': 'Test',
            'type': 'Kubernetes',
            'properties': {
                'dlPropA': 'A DL Prop'
            }
        }
        result = service.build(system_properties, properties, deployment_location)
        self.assertEqual(result, {
            'propA': 'A Prop',
            'extPropA': 'A Prop',
            'systemProperties': {
                'sysA': 'A',
                'sysB': 'B',
                'extSysA': 'A'
            }, 
            'deploymentLocationInst': {
                'name': 'Test',
                'type': 'Kubernetes',
                'properties': {
                    'dlPropA': 'A DL Prop',
                    'ExtDlPropA': 'A DL Prop'
                }
            }
        })