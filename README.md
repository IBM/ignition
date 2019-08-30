# Ignition

## What is it?

The Resource Manager provided with the Stratoss&trade; Lifecycle Manager, known as Brent, requires VIM drivers to integrate with virtual infrastructure and Lifecycle drivers to complete transitions and operations with different scripting mechanims.

Ignition is a framework which aims to ease the process of building those VIM and Lifecycle driver applications with Python.

# Installing Ignition

Install the latest release from pypi:

```
pip3 install ignition-framework
```

Named release:

```
pip3 install ignition-framework==0.1.0a1
```

## Install from source

Clone the source code and install it from the root directory:

```
pip3 install .
```

# Creating a VIM Driver application

For instructions on how to setup a VIM Driver application using Ignition see [VIM Driver User Guide](docs/userguides/vim_driver.md)

# Creating a Lifecycle Driver application

For instructions on how to setup a Lifecycle Driver application using Ignition see [Lifecycle Driver User Guide](docs/userguides/lifecycle_driver.md)

# Developer Guides

For guides related to development of Ignition, see:

- [Testing](docs/developers/testing.md)
