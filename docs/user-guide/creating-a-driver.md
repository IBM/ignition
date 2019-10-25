# Creating a Driver

This section will show you how to create your own driver using the Ignition framework to handle the "boilerplate". 

Contents:

- [Create Command](#create-command)
- [The Basics of a Driver](#the-basics-of-a-driver)

# Create Command

Creating a driver with Ignition is simple with the CLI tool provided with the framework. With a few simple inputs you can generate a ready-to-use Python project with solutions for:

- dependency management
- testing, building and releasing
- deployment as a Docker container
- deployment on Kubernetes through Helm

The driver application included in the project is ready to handle infrastructure and/or lifecycle requests with HTTP from Brent and return responses on Kafka - all you need to do is write the code to provide the individual functionality of your driver.

To get started, create a new directory for your project:

```
mkdir my-driver && cd my-driver
```

When creating a driver you must give it a name and specify if it will function as a VIM driver, Lifecycle driver or both. In addition, you may configure any of the following options:

- `--version` - the initial version of the driver (defaults to: 0.0.1)
- `--port` - the default port your driver will run on. This will be configurable at runtime but having a default is recommended for consistency (defaults to a randomly chosen value)
- `--description` - a description of your driver which will be included in metadata for your project
- `--module-name` - the name given to the Python package containing the source code (defaults to a lower case copy of the driver name with spaces, underscores and dashes removed e.g. "My Driver" becomes "mydriver")
- `--docker-name` - the intended name for the docker image of your driver (defaults to a lower case copy of the driver name with spaces replaced for dashes e.g. "My Driver" becomes "my-driver")
- `--helm-name` - the intended name for the helm chart of your driver (defaults to a lower case copy of the driver name with spaces replaced for dashes e.g. "My Driver" becomes "my-driver")
- `--helm-node-port` - the Helm chart includes an option to expose your deployed driver through a NodePort and Ingress. This option allows you to set the default NodePort (defaults to a randomly chosen value)

In the directory for your project, run the create command specifying the name of your driver, type and the value to any options you wish to set:

**Create a VIM Driver:**
```
ignition create "My Driver" -t vim
```

**Create a Lifecycle Driver:**
```
ignition create "My Driver" -t lifecycle
```

**Create a Driver to handle both VIM and Lifecycle:**
```
ignition create "My Driver" -t vim -t lifecycle
```

On completion you should see a directory structure including all of the generated files for your driver.

```
ls
```
Output: 
```
DESCRIPTION.md  devdocs  docker  docs  helm  MANIFEST.in  mydriver  README.md  setup.py  tests
```

The driver is ready to start! The driver has a dependency on Kafka, so you will need a working node/cluster first. Create a new file called `<module_name>_config.yml` e.g. `mydriver_config.yml`, add the following content:

```
messaging:
  connection_address: <insert kafka address>
```

Now run a development version of the driver with `<module_name>-dev` (e.g. mydriver-dev):

```
mydriver-dev
```

If successful you should be able to access your driver at: 

- VIM Driver - `http://localhost:<port>/api/infrastructure/ui`
- Lifecycle Driver - `http://localhost:<port>/api/lifecycle/ui`

# The Basics of a Driver

After running the create command you will have a project which includes the following files and directories:

- DESCRIPTION.md - a markdown file describing the driver, used in the metadata for your Python project (in `setup.py`)
- devdocs - directory containing useful documents for developers of this driver, with example steps to build, test and release the driver
- docker - directory containing the Dockerfile required to build a docker image 
- docs - directory to hold public documentation intended for end-users of your driver
- helm - directory containing the sources for the Helm chart
- MANIFEST.in - file used by `setuptools` (manager of the `setup.py` file) to ensure non-python files are included in the final package of the application
- mydriver (name will be different depending on your `module-name` setting) - a directory representing the Python package for your application. This contains all of the Python source code. 
- README.md - initial readme file useful for describing your project
- setup.py - Python script used by `setuptools` to manage the installation and distribution of the Python application 
- tests - directory to contain unit tests for your driver

The following sections explain the contents of the major directories of the project.

## Setup.py

The `setup.py` is a standard file required to manage the installation and distribution of a Python application with the popular [setuptools](https://pypi.org/project/setuptools/) module.

It is important that you keep this file up-to-date with information about your driver (such as the version number) and maintain the list of dependencies, adding any new packages you need for your implementation.

This allows other developers to install the dependencies required for your project from source with `pip`. It also allows you to produce a distributable version of the package, so it may be installed in a Docker image for a production deployment. 

Give it a try by ensuring you have `setuptools` installed

```
python3 -m pip install --upgrade setuptools
```

Then install the project from source by executing the following in the project's root directory: 

```
python3 -m pip install --editable .
```

This will download all of the dependencies specified in the `install_requires` section of the setup file and install the Python package for your application. The `--editable` option allows you to change the source code of your application on startup without requiring a re-install.

To build a distributable package for your driver, install `wheel`:

```
python3 -m pip install --upgrade wheel
```

Then execute the `setup.py` script with the `bdist_wheel` option:

```
python3 setup.py bdist_wheel
```

## Python Package

The Python package directory (`mydriver` in our example) contains the source code for the driver. Out-of-the-box this directory will include the following files:

- `pkg_info.json` - a file containing the version number of your driver. This is read by `setup.py` and `__init__.py` of your package to the version number is consistent in the distribution of your application and the running application. This is a useful pattern to keep them in-sync.
- `app.py` - contains the code to configure Ignition based application (this is a good file to start reading through to gain an understanding of how your driver works))
- `__main__.py` - contains the entry point used to run the application in development mode
- `__init__.py` - every Python package must have one of these files and they are usually empty. However, the root init file contains the code to return an application to be used in production mode.  This file also includes code to make the version of your driver from `pkg_info.json` available on the Python standard `__version__` variable.
- `config` - directory containing the default properties for the driver
- `bin` - directory containing the scripts used as entry points for the uWSGI production server
- `service` - directory containing the source code for this driver's implementations of the infrastructure and/or lifecycle APIs

You are free to add additional modules to the Python package in order to structure the code in a way that suits your style. 

The number of files can be overwhelming but the important parts to understand at this stage are:

### App.py

This is used to configure the application with Ignition. Let's have a look at the contents of this file:

```
import logging
import ignition.boot.api as ignition
import pathlib
import os
import mydriver.config as driverconfig
from mydriver.service.infrastructure import InfrastructureDriver

default_config_dir_path = str(pathlib.Path(driverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'default_config.yml')

def create_app():
    app_builder = ignition.build_driver('My Driver', vim=True)
    app_builder.include_file_config_properties(default_config_path, required=True)
    app_builder.include_file_config_properties('./mydriver_config.yml', required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/mydriver/mydriver_config.yml', required=False)
    app_builder.include_environment_config_properties('MYDRIVER_CONFIG', required=False)
    app_builder.add_service(InfrastructureDriver)
    return app_builder.configure()


def init_app():
    app = create_app()
    return app.run()
```

The first key component of this file is the `create_app` method, which configures the application. We start by building a Ignition app builder, with the name of our driver and the type. 

```
app_builder = ignition.build_driver('My Driver', vim=True)
```

We then define how our application will be configured, by default we add 4 sources. This may seem excessive but it offers flexbility to configure the application in different ways based on the type of deployment.

The first 3 are all configuration files we expect at a set path:

```
app_builder.include_file_config_properties(default_config_path, required=True)
app_builder.include_file_config_properties('./mydriver_config.yml', required=False)
# custom config file e.g. for K8s populated from Helm chart values
app_builder.include_file_config_properties('/var/mydriver/mydriver_config.yml', required=False)
```

The first line adds the default configuration file included in our application. As this is listed first, it will be set the initial values of our properties. Any values defined in later sources will override them.

The second line signals that the application should look for a file named `mydriver_config.yml` in the same directory it is being started from. As required is false, the application will ignore this source if the file is not found.

The last line adds an additional configuration file, which is auto-created by the Helm chart. This file allows users to configure the application via the Helm chart values. 

We also add an additional source of configuration to the app:

```
app_builder.include_environment_config_properties('MYDRIVER_CONFIG', required=False)
```

This signals that the application should check if a `MYDRIVER_CONFIG` environment variable is set. If it is, then it should point to a configuration file which should be read for property values. 

After configuring the property sources, we configure the custom services to be instantiated on startup:

```
app_builder.add_service(InfrastructureDriver)
```

The Ignition app builder has been auto-configured with several services, based on the type of driver being created (specified on the `build_driver` call), so we only need to add our additional services. In our example, we are adding our implementation of the InfrastructureDriver, which is ultimately called to handle infrastructure requests. You can read more about services and their role in an Ignition based app in the [framework](./framework/index.md) section.

Finally we build the application and return it:

```
return app_builder.configure()
```

The last element of this file is the `init_app` method. This method creates the application and then runs it. You'll see in `__main__.py` and `__init__.py` that in development we want to start the app but in production we only need to create and return it, so it may be managed by a uWSGI container.

### infrastructure.py or lifecycle.py

These files are where you should begin implementing the functionality of your driver. In each file you will see a class which implements either the `InfrastructureCapability` or the `LifecycleCapability`.

To add functionality to your driver, you must implement each method stub included on those classes. 

## Docker 

This directory contains a recommended implementation of a Dockerfile to build an image for your driver. It contains a best practice solution for installing the driver from a pre-built `whl` (see [setup.py](#setup.py)), then running the driver in production mode and exposing the necessary port to allow access to it's APIs.

You are free to adjust this file to produce an image more suited to your deployment patterns. There is no requirement to keep this directory, your Python application is unaffected by it's presence.

## Helm 

This directory contains a recommended implementation of a Helm chart to deploy your the docker image of your driver in a Kubernetes cluster.

The Helm chart will install:

- ConfigMaps to allow configuration properties of the driver to be set 
- a Deployment to run the driver in a docker container. This Deployment is configured to allow logs from your driver to be scrapped into the logging dashboard included in your Stratoss&trade; Lifecycle Manager installation. It also includes best practice solutions to allow the resource limits and affinity rules of the deployment to be configured
- a Service to load balance access to the APIs of your driver. This Service also includes the option to expose the APIs to external clients from the Kuberentes cluster, using NodePorts
- an Ingress rule to expose the APIs to external clients from the Kuberentes using an ingress controller (if your cluster has one installed)

This implementation of a Helm chart should allow you deploy your driver to Kubernetes right away! However, you are free to adjust this directory to produce a chart more suited to your deployment patterns. There is no requirement to keep this directory, your Python application is unaffected by it's presence.
