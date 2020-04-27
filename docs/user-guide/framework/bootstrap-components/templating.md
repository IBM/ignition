# Templating

Templating is a feature offered to drivers to inject property values into infrastructure and lifecycle scripts. For example, the execution of a lifecycle script may vary based on a request property called `fileName`, so uses a variable placeholder:

```
touch {{ fileName }}
```

Rendering the template produces a different result based on the property context used:

Property Context:
```
{
    'fileName': 'my-file.txt'
}
```

Script:
```
touch my-file.txt
```

The [Jinja](https://jinja.palletsprojects.com/en/2.11.x/templates/) library is used to process templates.

Although optional, the Services listed below are enabled by default when using the `ignition.boot.api.build_resource_driver` function.

## Services

The following services are auto-configured when enabled:

| Name                     | Capability         | Required Capabilities             | Bootstrap Enable/Disable flag       | Description                                                                                                                                     |
| ------------------------ | ------------------ | --------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Jinja2TemplatingService | TemplatingCapability | - | bootstrap.templating.service_enabled | Handles rendering templates |
| ResourceTemplateContextService | ResourceTemplateContextCapability | - | bootstrap.templating.resource_context_service_enabled | Builds up a dictionary context to use in templates, based on request inputs. Using this service provides consistent property language for template developers across drivers |

## Usage

Example usage shown for a driver built with Ignition:

```python
class ResourceDriver(Service, ResourceDriverCapability):

    def __init__(self, templating_service, resource_context_service):
        # Jinja2TemplatingService
        self.templating_service = templating_service
        # ResourceTemplateContextService
        self.resource_context_service = resource_context_service

    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location):
        # Build context based on inputs
        context = self.resource_context_service.build(system_properties, properties, deployment_location)
        # Render the template
        with open(driver_files.get_file_path('template.yaml'), 'r') as f:
            rendered_template = self.templating_service.render(f.read(), context)
        # Proceed to use the rendered template
        ...
```