# Install Ignition

The main intention of the Ignition framework is for it to be used as dependency installed as part of your Python application. 

However, we recommend installing Ignition to your machine so you may use the CLI tool as it makes creating new drivers much simpler. 

## Pre-requisites

### Python 3

Before you begin you will need to install:

- <a href="https://www.python.org" target="_blank">Python3 (v3.5+)</a>
- <a href="https://pip.pypa.io/en/stable/installing/" target="_blank">Pip3</a> (already installed with many Python installations)

As it's possible to have both Python2 and Python3 installed on one machine, this guide will make use of `python3` and `pip3` commands instead of `python` and `pip`. If you only have Python3, then you may use the latter instead. Verify which command works for you by running both:

```
python --version

python3 --version
```

Use the version which responds with a `3.x` number.


### Python Virtual Environment

It is highly recommended that you install and make use of a virtual environment when installing Ignition. This will keep Ignition and it's dependencies isolated from other Python applications on your machine. 

We recommend installing <a href="https://virtualenv.pypa.io/en/latest/" target="_blank">Virtualenv</a>:

```
python3 -m pip install virtualenv
```

Create a new virtual environment with `virtualenv`, specifying a suitable name for it:

```
python3 -m virtualenv env
```

This will create an environment in a directory named `env` (or any name you decide). Once created, the virtual environment can be activated anytime with:

```
source env/bin/activate
```

On Windows, try:

```
env\Scripts\activate.bat
```

Ensure the environment is active anytime you install or use LMCTL to maintain isolation from your global Python environment.

To deactivate the virtual environment at anytime just execute:

```
deactivate
```

## Install

Activate any virtual environment (if you plan to use one) and install Ignition with pip:

```
python3 -m pip install ignition-framework
```

To install a specific version (<a href="https://pypi.org/project/ignition-framework/" target="_blank">see available versions</a>) add the number to the end of the command with `==`:

```
python3 -m pip install ignition-framework==0.4.0
```

Verify the installation has worked by executing:

```
ignition --version
```

Access the `help` section of LMCTL with:

```
ignition --help
```