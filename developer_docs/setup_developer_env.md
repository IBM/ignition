# Setup Developer Environment

To develop Ignition you need Python v3.6.9+ (install using instructions suitable for your operating system).

## Pip/Setup

Once installed, make sure you have the latest `pip`, `setuptools` and `wheel`:

```
python3 -m pip install -U pip setuptools wheel
```

It's also recommended that you create a [virtualenv](https://virtualenv.pypa.io/en/latest/) to manage an isolated Python env for this project:

Install virtualenv:

```
python3 -m pip install virtualenv
```

## Virtualenv

Create a virtualenv (do this from the root of your Ignition clone):

```
python3 -m virtualenv env
```

The virtualenv should be activated in your terminal when working on Ignition:

(Unix/Mac)
```
source env/bin/activate
```

(Windows Powershell)
```
Scripts\activate.ps1
```

(Windows Other)
```
Scripts\activate
```

## Install Ignition

You may now install Ignition into your environment:

```
python3 -m pip install --editable .
```

Use the `--editable` flag to avoid re-installing on every change you make. 

## Build Ignition

To build Ignition (to distribute/use in a driver project), you need to build a whl:

```
python3 setup.py bdist_wheel
```

The `.whl` file will be created in the `dist` directory at the root of the project. This `.whl` file can be transferred and used to install this version of Ignition with pip elsewhere.

```
cp dist/ignition_framework-2.0.4.dev0-py3-none-any.whl another-location/
python3 -m pip install another-location/ignition_framework-2.0.4.dev0-py3-none-any.whl
```

For example, you may wish to build an [Ansible Lifecycle Driver](https://github.com/IBM/ansible-lifecycle-driver) docker image with a custom Ignition version, so can copy the whl to the `docker/whls` directory:

```
cp dist/ignition_framework-2.0.4.dev0-py3-none-any.whl ~/my-git-repos/ansible-lifecycle-driver/docker/whls/
```

