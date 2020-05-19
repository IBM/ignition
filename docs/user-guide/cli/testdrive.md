# Test Drive

This command is provided to perform test requests against a driver in development, without requiring a full ALM setup. You can already do this with a Rest client (such as Postman) but this command aims to make this process easier by automating the process of sending an API request to a driver and listening to the response on Kafka.

You will need to build a [Resource State](#resource-state) file to be used on either of the support requests ([execlifecycle](#execlifecycle) and [findreference](#findreference))

# Resource State

A Resource state file outlines the re-usable state of a Resource to be used across simulated requests. This includes:

- Properties (systemProperties included)
- Driver Files 
- Deployment Location
- Associated Topology

Any time you execute a `testdrive` command you will need to reference this file so it's contents may be used on the simulated request.

## Driver Files

Driver files is the `Lifecycle` directory usually included in a Resource package. Add `driverFilesDir` with the full path to this directory:

```
driverFilesDir: MyResourceProject/Lifecycle
```

Later in requests, you will need to specify the `-d` command to tell the command which driver is in use so the correct directory in `driverFilesDir` is included on the request e.g. `ansible` or `openstack`. 

As an example, imagine you have the following:

```
MyResourceProject/
  Lifecycle/
    ansible/
      ...ansible driver files...
    /openstack
      ...openstack driver files...
```

When performing a test request on the Ansible driver you need to use `-d ansible`.

## Properties

You can include Resource properties and System Properties for your Resource. You should include both `value` and `type` for each property (as required by the driver execute lifecycle API):

```
resourceProperties:
  propertyA:
    type: string
    value: PropA
systemProperties:
  resourceId:
    type: string
    value: 3fa7d7c8-54b2-4d7d-8324-7752b64e7296
  resourceName:
    type: string
    value: londona-firewall
```

## Associated Topology

If you wish to simulate a request with a Resource which already has associated topology, you can add valid entries to the file:

```
associatedTopology:
  theName:
    id: theId
    type: theType
```

## Deployment Location

Include the full details of the Deployment Location to be used on the request:

```
deploymentLocation: 
  name: my-kubernetes
  properties:
    driverNamespace: kubedriver
    defaultObjectNamespace: kubedriver
    clientConfig: <snippet removed>
```

## Example Driver Files

```
driverFilesDir: MyResourceProject/Lifecycle
resourceProperties:
  propertyA:
    type: string
    value: PropA
  propertyB:
    type: string
    value: PropB
systemProperties:
  resourceId:
    type: string
    value: 3fa7d7c8-54b2-4d7d-8324-7752b64e7296
  resourceName:
    type: string
    value: londona-firewall
deploymentLocation: 
  name: my-kubernetes
  properties:
    driverNamespace: kubedriver
    defaultObjectNamespace: kubedriver
    clientConfig: <snippet removed>
```

# execlifecycle

Make a lifecycle execution request against a driver (optionally wait for async response).

Check the help section for more details:

```
ignition testdrive execlifecycle --help
```

Examples:

Assuming you have a resource state file created at `my-resource.yaml`) and the driver under test is the Openstack driver with a URL of `http://localhost:8292`

Execute a Create transition, get the sync response:
```
ignition testdrive execlifecycle -l Create -r my-resource.yaml --url http://localhost:8292 -d openstack 
```

Execute a Create transition, get the sync response, then wait for the response on Kafka
```
ignition testdrive execlifecycle -l Create -r my-resource.yaml --url http://localhost:8292 -d openstack --wait
```

Execute a Create transition, get the sync response, then wait for 900 seconds for the response on Kafka (the Kafka cluster in use by the driver is accessible at `kafka:9092` from your machine)
```
ignition testdrive execlifecycle -l Create -r my-resource.yaml --url http://localhost:8292 -d openstack --wait
```

Execute a Create transition, get the sync response, then wait for 900 seconds for the response on Kafka (the Kafka cluster in use by the driver is accessible at `alternative-kafka:9092` from your machine)
```
ignition testdrive execlifecycle -l Create -r my-resource.yaml --url http://localhost:8292 -d openstack --wait -k alternative-kafka:9092
```

Execute a Create transition, get the sync response, then wait just 60 seconds for the response on Kafka (the Kafka cluster in use by the driver is accessible at `kafka:9092` from your machine)
```
ignition testdrive execlifecycle -l Create -r my-resource.yaml --url http://localhost:8292 -d openstack --wait -m 60
```
# findreference

Execute a find reference request against a driver

Check the help section for more details:

```
ignition testdrive findreferences --help
```

Examples:

Assuming you have a resource state file created at `my-resource.yaml`) and the driver under test is the Openstack driver with a URL of `http://localhost:8292`

Find using instanceName=mynetwork
```
ignition testdrive findreference -n mynetwork -r my-resource.yaml --url http://localhost:8292 -d openstack 
```