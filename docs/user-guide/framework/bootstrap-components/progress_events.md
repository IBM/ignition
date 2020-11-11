# Resource Transition Progress Events

The Progress Event Log is a feature offered to drivers to submit events during the execution of a Resource lifecycle transition or operation, to provide live progress. 

Although optional, the Services listed below are enabled by default when using the `ignition.boot.api.build_resource_driver` function.

## Services

The following services are auto-configured when enabled:

| Name                     | Capability         | Required Capabilities             | Bootstrap Enable/Disable flag       | Description                                                                                                                                     |
| ------------------------ | ------------------ | --------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| ProgressEventLogWriterService | ProgressEventLogWriterCapability | - | bootstrap.progress_event_log.service_enabled | Handles submitting events |

## Events

The intended schema for Resource transition progress events is as follows:

```
eventType:
  type: string
  description: To remain consistent with other TNCO events, this event type field indicates the payload is for a Resource Transition Progress event
  fixedValue: ResourceTransitionProgressEvent
progressEventType:
  type: string
  description: Considered a "sub event type". Describes the type of event taking place within the context of the driver implementation
details:
  type: object
  description: Details of the event, deliberately schema-less so the driver implementation can add any relevant information
```

In addition, there is an expected naming convention for values of progressEventType to:

- prevent collision between the names of events from 2 different drivers; but
- allow drivers to use consistent names for common events

progressEventType values to use the following format:

```
<group>/<name>

group - the driver name/type or any other valid name for a logical grouping of events
name - the associated name of the event in the group
```

For example, the Ansible driver could produce events such as:

- `ansible/PlaybookStart`
- `ansible/TaskStart`

Whilst the Kubernetes driver could produce:

- `kubernetes/ObjectCreated`

But both drivers could produce:

- `common/SomeCommonEvent`

## Usage

To use the event log you should create your own Resource transition progress events by subclassing `ResourceTransitionProgressEvent` from `ignition.model.progress_events`. Override the `_details` function in order to provide extra context to the event.

Example usage shown for a driver built with Ignition:

```python
from ignition.model.progress_events import ResourceTransitionProgressEvent

class ScriptStartedEvent(ResourceTransitionProgressEvent):
    progress_event_type = 'mydriver/ScriptStarted

    def __init__(self, script_name):
        # Must call super
        super().__init__()
        self.script_name = script_name

    # Override _details with additional information to include on event
    def _details(self):
        return {
            'scriptName': self.script_name
        }

class ScriptFinishedEvent(ResourceTransitionProgressEvent):
    progress_event_type = 'mydriver/ScriptFinished

    def __init__(self, script_name, result):
        super().__init__()
        self.script_name = script_name
        self.result = result

    def _details(self):
        return {
            'scriptName': self.script_name,
            'result': self.result
        }

class ResourceDriverHandler(Service, ResourceDriverHandlerCapability):

    def __init__(self, event_log_service):
        # ProgressEventLogWriterService
        self.event_log_service = event_log_service

    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, associated_topology, deployment_location):
        script_name = lifecycle_name + '.script'
        script = driver_files.get_file_path(lifecycle_name + '.script')
        
        # Send event
        self.event_log_service.add(ScriptStartedEvent(script_name))

        # Do some work
        result = execute_script(script)

        # Send another event
        self.event_log_service.add(ScriptFinishedEvent(script_name))
        ...
```