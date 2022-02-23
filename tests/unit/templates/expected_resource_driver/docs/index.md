# Test Driver

unit test driver

# Replace Content

Replace the content of this file with a user guide for your application

# Install

Install Test Driver using Helm:

```
helm install --name tdhelm tdhelm-0.5.0.tgz
```

Add configuration through a custom Helm values file:

```
touch custom-values.yaml
```

Add configuration to this file (check [Helm Configuration](#helm-configuration) and [Application Configuration)[#app-configuration] for details of the properties that may be configured):

```
app:
  config:
    override:
      connection_address: foundation-kafka:9092
```

Reference the values file on install to apply configuration:

```
helm install --name tdhelm tdhelm-0.5.0.tgz -f custom_values.yaml-
```

Once the pod for the driver has started you should be able to view the status of the application at: `http://:{(helm.node_port)}/management/health`

## Helm Configuration

The following table lists configurable parameters of the chart:

| Parameter | Description | Default |
| --- | --- | --- |
| docker.image | Name of the image for the driver (may include docker registry information) | tddock |
| docker.version | Image tag to deploy | 0.5.0 |
| docker.imagePullPolicy | Image pull policy | IfNotPresent |
| app.replicas | Number of instances of the driver to deploy | 1 |
| app.config.log.level | Level of log messages output by the driver | INFO |
| app.config.env | Environment variables to be passed to the driver | (See below) |
| app.config.env.LOG_TYPE | Log format (leave as logstash) | logstash |
| app.config.env.NUM_PROCESSES | Number of processes started by the Gunicorn container | 4 |
| app.config.override | Map to set [Application Configuration)[#app-configuration] properties | See connection_address below and [Application Configuration)[#app-configuration] properties |
| app.config.override.message.connection_address | Kafka address. Default set to address of Kafka installed as standard with LM | foundation-kafka:9092 |
| app.affinity | Affinity settings | A pod anti-affinity rule is configured to inform Kubernetes it is preferable to deploy the pods on different Nodes |
| app.tolerations | Tolerations for node taints | [] |
| app.resources | Set requests and limits to CPU and memory resources | {} |
| service.type | Type of Service to be deployed | NodePort |
| service.nodePort | NodePort used to expose the service | 30777 |
| ingress.enabled | Flag to disable/enable creation of an Ingress rule for external access | true |
| ingress.host | Hostname on the Ingress rule | tdhelm.lm |

## Application Configuration

The following table lists configurable parameters of the Application, that may be specified in the `app.config.override` value of the Helm chart:

| Parameter | Description | Default |
| --- | --- | --- |
| application.port | Port the application runs on (internal access only) | 7777 | 
| messaging.connection_address | Kafka address | kafka:9092 |
