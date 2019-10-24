import logging
import ignition.boot.api as ignition
import pathlib
import os
import {( app.module_name )}.config as driverconfig
{%- if app.is_vim == true %}
from {( app.module_name )}.service.infrastructure import InfrastructureDriver
{%- endif %}
{%- if app.is_lifecycle == true %}
from {( app.module_name )}.service.lifecycle import LifecycleDriver
{%- endif %}


default_config_dir_path = str(pathlib.Path(driverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'default_config.yml')


def create_app():
    app_builder = ignition.build_driver('{( app.name )}'{% if app.is_vim == true %}, vim=True{% endif %}{% if app.is_lifecycle == true %}, lifecycle=True{% endif %})
    app_builder.include_file_config_properties(default_config_path, required=True)
    app_builder.include_file_config_properties('./{( app.module_name )}_config.yml', required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/{( app.module_name )}/{( app.module_name )}_config.yml', required=False)
    app_builder.include_environment_config_properties('{( app.module_name|upper )}_CONFIG', required=False)
    {%- if app.is_vim == true %}
    app_builder.add_service(InfrastructureDriver)
    {%- endif %}
    {%- if app.is_lifecycle == true %}
    app_builder.add_service(LifecycleDriver)
    {%- endif %}
    return app_builder.configure()


def init_app():
    app = create_app()
    return app.run()
