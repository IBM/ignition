from ignition.service.framework import Capability, Service, interface
from ignition.templating import JinjaTemplate, ResourceContextBuilder

class TemplatingCapability(Capability):
    """
    Interface for a Templating service capable of rendering templates
    """

    @interface
    def render(self, content, context):
        """
        Render the given content based on the given context

        Args:
            content (str): string contents of the template to be rendered
            context (dict): context properties that may be referenced in the template

        Returns:
            string contents of the rendering result
        """
        pass

class Jinja2TemplatingService(Service, TemplatingCapability):
    """
    Implementation of the TemplatingCapability based on Jinja2
    """

    def render(self, content, context):
        return JinjaTemplate(content).render(context)

class ResourceTemplateContextCapability(Capability):
    """
    Interface for building Template render context based on common inputs to infrastructure and lifecycle requests
    """

    @interface
    def build(self, system_properties, properties, request_properties, deployment_location):
        """
        Builds a dictionary context, suitable for rendering templates, based on the properties of a request.
        The structure of the context depends on the chosen implementation

        Args:
            system_properties (dict or PropValueMap): dictionary of system_properties to include
            properties (dict or PropValueMap): dictionary of properties to include
            request_properties (dict or PropValueMap): dictionary of request properties to include
            deployment_location (dict): dictionary representing the deployment location details

        Returns:
            the context (dict)
        """
        pass

class ResourceTemplateContextService(Service, ResourceTemplateContextCapability):
    """
    Implementation of the ResourceTemplateContextCapability which uses the ignition.templating.ResourceContextBuilder class 
    """

    def build(self, system_properties, properties, request_properties, deployment_location):
        """
        Builds a dictionary context, suitable for rendering templates, based on the properties of a request.
        Uses the ignition.templating.ResourceContextBuilder class, so consult it's documentation for details on the structure of the result.

        This class can be extended to add additional properties to the context. Do this by overriding the `_configure_additional_props` method
        which provides the current builder and the original args

        Example:

        class MyExtendedResourceTemplateContextService(ResourceTemplateContextService):
            def _configure_additional_props(self, builder, system_properties, properties, deployment_location):
                builder.add_system_property('my-extra-property', 'someValue')

        Args:
            system_properties (dict or PropValueMap): dictionary of system_properties to include
            properties (dict or PropValueMap): dictionary of properties to include
            request_properties (dict or PropValueMap): dictionary of request properties to include
            deployment_location (dict): dictionary representing the deployment location details

        Returns:
            the context (dict)
        """
        builder = self._initiate_builder(system_properties, properties, request_properties, deployment_location)
        self._configure_additional_props(builder, system_properties, properties, request_properties, deployment_location)
        return builder.result

    def _initiate_builder(self, system_properties, properties, request_properties, deployment_location):
        return ResourceContextBuilder(system_properties, properties, request_properties, deployment_location)
    
    def _configure_additional_props(self, builder, system_properties, properties, request_properties, deployment_location):
        #Room for extensions
        pass