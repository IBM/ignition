from ignition.service.framework import Capability, Service, interface
from ignition.templating import JinjaTemplate, ResourceContextBuilder, Syntax

class TemplatingCapability(Capability):
    """
    Interface for a Templating service capable of rendering templates
    """

    @interface
    def syntax(self):
        """
        Describe the syntax to be used in Templates

        Returns:
            string describing the syntax to be used in Templates
        """
        pass

    @interface
    def build_settings(self):
        """
        Initiate a settings object suitable for use with this templating service

        Returns:
            a settings object. The chosen return type depends on the templating service implementation
        """
        pass

    @interface
    def render(self, content, context, settings=None):
        """
        Render the given content based on the given context

        Args:
            content (str): string contents of the template to be rendered
            context (dict): context properties that may be referenced in the template
            settings (object): settings object used to control the templating behaviour (usually initialised from build_settings) 

        Returns:
            string contents of the rendering result
        """
        pass

class Jinja2TemplatingService(Service, TemplatingCapability):
    """
    Implementation of the TemplatingCapability based on Jinja2
    """

    def syntax(self):
        return Syntax.JINJA2

    def build_settings(self):
        return JinjaTemplate.build_settings()

    def render(self, content, context, settings=None):
        return JinjaTemplate(content).render(context, settings=settings)

class ResourceTemplateContextCapability(Capability):
    """
    Interface for building Template render context based on common inputs to driver requests
    """

    @interface
    def build(self, system_properties, resource_properties, request_properties, deployment_location, associated_topology = None):
        """
        Builds a dictionary context, suitable for rendering templates, based on the properties of a request.
        The structure of the context depends on the chosen implementation

        Args:
            system_properties (dict or PropValueMap): dictionary of system_properties to include
            resource_properties (dict or PropValueMap): dictionary of properties to include
            request_properties (dict or PropValueMap): dictionary of request properties to include
            deployment_location (dict): dictionary representing the deployment location details
            associated_topology (dict or AssociatedTopology): dictionary representing the associated topology details

        Returns:
            the context (dict)
        """
        pass

class ResourceTemplateContextService(Service, ResourceTemplateContextCapability):
    """
    Implementation of the ResourceTemplateContextCapability which uses the ignition.templating.ResourceContextBuilder class 
    """

    def build(self, system_properties, resource_properties, request_properties, deployment_location, associated_topology = None):
        """
        Builds a dictionary context, suitable for rendering templates, based on the properties of a request.
        Uses the ignition.templating.ResourceContextBuilder class, so consult it's documentation for details on the structure of the result.

        This class can be extended to add additional properties to the context. Do this by overriding the `_configure_additional_props` method
        which provides the current builder and the original args

        Example:

        class MyExtendedResourceTemplateContextService(ResourceTemplateContextService):
            def _configure_additional_props(self, builder, system_properties, resource_properties, deployment_location):
                builder.add_system_property('my-extra-property', 'someValue')

        Args:
            system_properties (dict or PropValueMap): dictionary of system_properties to include
            resource_properties (dict or PropValueMap): dictionary of properties to include
            request_properties (dict or PropValueMap): dictionary of request properties to include
            deployment_location (dict): dictionary representing the deployment location details
            associated_topology (dict or AssociatedTopology): dictionary representing the associated topology details

        Returns:
            the context (dict)
        """
        builder = self._initiate_builder(system_properties, resource_properties, request_properties, deployment_location, associated_topology)
        self._configure_additional_props(builder, system_properties, resource_properties, request_properties, deployment_location)
        return builder.result

    def _initiate_builder(self, system_properties, resource_properties, request_properties, deployment_location, associated_topology = None):
        return ResourceContextBuilder(system_properties, resource_properties, request_properties, deployment_location, associated_topology)
    
    def _configure_additional_props(self, builder, system_properties, resource_properties, request_properties, deployment_location):
        #Room for extensions
        pass
